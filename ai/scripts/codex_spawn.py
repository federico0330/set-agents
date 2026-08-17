#!/usr/bin/env python3
"""Codex-lane CLI subprocess spawn primitive (ADR-0032, closes ADR-0030's gap).

Why this exists: the Codex-hosted orchestrator delegates via codex's own agents feature,
where the child's model/effort come from the installed `~/.codex/agents/<role>.toml` —
STATIC curated values (`generate.py` emits `model = ...` / `model_reasoning_effort =
...` per role). Codex has zero `@tier` variants, so before this module NO codex-lane
spawn could apply a `--route-decide` model at spawn time and every routed role degraded
to `MODEL_STATIC_FALLBACK`. Here the decision is materialized for ANY roster role as a
subprocess: `codex exec --ephemeral --sandbox <mode> --color never -m <model>
[-c model_reasoning_effort=<effort>] -c developer_instructions=<role-prompt>
-o <last-message-file> -`, task delivered via stdin.

Evidence (live-verified against the installed codex-cli 0.146.0, this feature's own
evidence session): `codex exec --help` documents `-m/--model` and `-c key=value`
("Override a configuration value that would otherwise be loaded from
~/.codex/config.toml … If it fails to parse as TOML, the raw string is used as a
literal"); a real run with `-m gpt-5.4-mini -c model_reasoning_effort=low
-c developer_instructions="…codeword…"` echoed the header `reasoning effort: low` and
returned the developer-instruction codeword — all three knobs honored per invocation.
`codex exec --agent` does NOT exist (live-verified: "unexpected argument '--agent'"),
which is why the role prompt travels as `developer_instructions` (the same field the
installed agent TOMLs use), read from the canonical `Global/_canonical/agents/<role>.md`
— the ADR-0007 pi-lane pattern (`--append-system-prompt <role.md>`), adapted.

Model mapping: `openai-codex` catalog models pass VERBATIM (`-m gpt-5.6-sol` — the same
bare ids `models.toml`'s `codex` column already uses). Any other provider fails closed
(`PROVIDER_UNSUPPORTED`): anthropic decisions are served by the claude-code redirect.

Effort: `-c model_reasoning_effort=<e>` for the closed routing universe
{low, medium, high, xhigh} only (matching `models.toml`'s own `codex_effort` catalog);
absent/unknown omits the override and the child runs at config default — advisory,
never fatal (ADR-0030 effort-extension discipline).

Sandbox ceiling — CLI-level, decided per role capability, never caller-chosen:
`code-rw`/`docs-rw`/`memory-rw`/`factory-rw` -> `workspace-write` (the role's actual
job); every other capability -> `read-only`. `--dangerously-bypass-approvals-and-sandbox`
and `--dangerously-bypass-hook-trust` are NEVER composed (checked fail-closed, not
merely documented). cwd is ALWAYS inside the repository root (write-containment
boundary, `claude_code_spawn` precedent). `--ephemeral` keeps every child sessionless
(the pi lane's `--no-session` equivalent).

Role classes and lifecycle: identical three-mode shape to `opencode_spawn.py` —
`--dispatch-writer` (consumes an existing run_id, drives dispatched->spawn->terminal),
`--dispatch-review` (no bookkeeping, nonce-fenced supplementary), `--dispatch-simulate`
(role_class `other` only; refuses writer/review — a simulate decision authorizes
nothing durable, ADR-0030 "Never fabricate enforcement"). Structural precedent is
`ai/scripts/claude_code_spawn.py`; never a call into it.

Model verification: `codex exec` prints a `model: <id>` header line on stdout — when
present and different from the requested model this classifies as `model_mismatch`
(R2-08 discipline); when absent, `detail["model_verified"]` is False and the run is
otherwise classified on exit code + last-message presence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config  # noqa: E402
from spawn_task_fence import compose_task_payload  # noqa: E402
from routing_core.store import RoutingStore  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
APP_CLI = ROOT / "ai/scripts/set_agents_app.py"
CANON_AGENTS = ROOT / "Global/_canonical/agents"

CODEX_BIN = "codex"
CODEX_TIMEOUT_SECONDS = 300.0
AUDIT_LOG_FILENAME = "codex_spawn_audit.jsonl"

_CODEX_EFFORT_LEVELS = frozenset({"low", "medium", "high", "xhigh"})
_WRITE_CAPABILITIES = {"code-rw", "docs-rw", "memory-rw", "factory-rw"}
# Never composed, under any parameter, on any argv this module builds.
_FORBIDDEN_FLAGS = ("--dangerously-bypass-approvals-and-sandbox", "--dangerously-bypass-hook-trust")

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+"),
)


def _redact(text: str) -> str:
    if not text:
        return ""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class SpawnError(Exception):
    """A stable, non-secret reason string; never a bare traceback."""


# ADR-0056 (amends ADR-0012, AC-12, 025/D5): see `claude_code_spawn._fetch_vault_block`'s
# own docstring for the full rationale (sanctioned `--context --json` channel, why an
# in-process re-implementation would be a circular import, "obligatorio" != "falla
# cerrado", per-process cache). Duplicated here rather than imported: this module is,
# by this feature's own deliberate architecture (module docstring above, "never a call
# into" `claude_code_spawn`), a SEPARATE lane module.
_VAULT_FETCH_TIMEOUT_SECONDS = 10.0
_VAULT_NONE_LINKED_NOTE = "[vault: none linked for this project; spawn proceeds without it]"
_VAULT_DEGRADED_NOTE = "[vault: lookup failed; spawn proceeds without it]"
VAULT_DEGRADATION_LOG_FILENAME = "vault_degradation.jsonl"
# Cache only settled outcomes. Transient failures must be retried by the next spawn.
_vault_block_cache: dict[str, str] = {}


def _persist_vault_degradation(reason: str, *, routing_test_root=None) -> None:
    try:
        root = RoutingStore(root=Path(routing_test_root) if routing_test_root else None).ensure_cache_root()
        path = root / VAULT_DEGRADATION_LOG_FILENAME
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"ts": time.time(), "reason": reason}, sort_keys=True) + "\n")
        os.chmod(path, 0o600)
    except Exception:  # noqa: BLE001 - observational only
        pass


def _fetch_vault_block(cwd, *, timeout: float = _VAULT_FETCH_TIMEOUT_SECONDS, routing_test_root=None) -> str:
    key = str(Path(cwd).resolve()) if cwd is not None else str(ROOT)
    if key in _vault_block_cache:
        return _vault_block_cache[key]
    try:
        proc = subprocess.run(
            [sys.executable, str(APP_CLI), "--context", "--json", "--project", key],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _persist_vault_degradation(f"VAULT_FETCH_EXCEPTION:{type(exc).__name__}", routing_test_root=routing_test_root)
        return _VAULT_DEGRADED_NOTE
    if proc.returncode != 0:
        _persist_vault_degradation(f"VAULT_FETCH_NONZERO_EXIT:{proc.returncode}", routing_test_root=routing_test_root)
        return _VAULT_DEGRADED_NOTE
    try:
        doc = json.loads(proc.stdout.strip()) if proc.stdout.strip() else {}
    except ValueError:
        _persist_vault_degradation("VAULT_FETCH_UNPARSEABLE_OUTPUT", routing_test_root=routing_test_root)
        return _VAULT_DEGRADED_NOTE
    sections = [doc.get(name) for name in ("hub", "company", "project", "pending")] if isinstance(doc, dict) else []
    present = [section for section in sections if isinstance(section, str) and section]
    block = "\n\n".join(present) if present else _VAULT_NONE_LINKED_NOTE
    _vault_block_cache[key] = block
    return block


_MODEL_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def codex_model_id(provider: str, model: str) -> str:
    """openai-codex catalog models pass verbatim; everything else fails closed."""
    if provider != "openai-codex":
        raise SpawnError("PROVIDER_UNSUPPORTED")
    if not _MODEL_TOKEN_RE.fullmatch(model or ""):
        raise SpawnError("MODEL_TOKEN_INVALID")
    return model


def _roster_item(role: str, roster):
    if isinstance(roster, dict):
        return roster.get(role)
    return next((row for row in roster if row.get("role") == role), None)


def _role_class(role: str, roster) -> str:
    item = _roster_item(role, roster)
    if item is None:
        raise SpawnError("ROLE_UNKNOWN")
    if item.get("capability") == "code-rw":
        return "writer"
    if item.get("capability") == "review-ro" and item.get("duty") in {"audit", "judge"}:
        return "review"
    return "other"


def _sandbox_mode(role: str, roster) -> str:
    item = _roster_item(role, roster)
    if item is None:
        raise SpawnError("ROLE_UNKNOWN")
    return "workspace-write" if item.get("capability") in _WRITE_CAPABILITIES else "read-only"


def compose_task(task: str, supplementary: str | None = None, vault_block: str | None = None) -> str:
    """SEC-004 precedent: nonce-fenced untrusted supplementary content. ADR-0056 (AC-12):
    `vault_block`, when given, is the ALREADY-fenced text `_fetch_vault_block` returns
    (context_pack._mark_untrusted's own per-call nonce, never a second scheme) -- placed
    AHEAD of everything else. None by default; return value is byte-identical to the
    pre-ADR-0056 shape whenever it is omitted."""
    return compose_task_payload(task, supplementary, vault_block, token_hex=secrets.token_hex)


def compose_argv(role: str, model: str, sandbox: str, instructions: str,
                 effort=None, output_path=None) -> list[str]:
    """The exact composed argv (module docstring). The task is NEVER a member — it is
    delivered via stdin (`-` prompt). `developer_instructions`' value intentionally does
    not parse as TOML (a markdown role prompt), so codex adopts it as a literal string
    (documented `-c` behavior, live-verified)."""
    if role.startswith("-") or sandbox not in ("read-only", "workspace-write"):
        raise SpawnError("ARGV_TOKEN_INVALID")
    model_id = codex_model_id("openai-codex", model)
    argv = [CODEX_BIN, "exec", "--ephemeral", "--sandbox", sandbox, "--color", "never",
            "-m", model_id]
    if effort in _CODEX_EFFORT_LEVELS:
        argv += ["-c", f"model_reasoning_effort={effort}"]
    argv += ["-c", f"developer_instructions={instructions}"]
    if output_path is not None:
        argv += ["-o", str(output_path)]
    argv.append("-")
    if any(flag in argv for flag in _FORBIDDEN_FLAGS):
        raise SpawnError("FORBIDDEN_FLAG_COMPOSED")
    return argv


_MODEL_HEADER_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)


def spawn(role: str, task: str, provider: str, model: str, roster, *,
          effort=None, expect_class: str | None = None, supplementary: str | None = None,
          prompt_root=None, cwd=None, timeout: float = CODEX_TIMEOUT_SECONDS,
          vault_block: str | None = None) -> tuple[str, dict]:
    """One codex child. `(outcome, detail)`: `success` / `model_mismatch` / `failure`.
    Never raises for a child-side failure."""
    try:
        role_class = _role_class(role, roster)
        sandbox = _sandbox_mode(role, roster)
        model_id = codex_model_id(provider, model)
    except SpawnError as exc:
        return "failure", {"reason": str(exc)}
    if expect_class is not None and role_class != expect_class:
        return "failure", {"reason": "ROLE_CLASS_MISMATCH"}
    prompt_path = (Path(prompt_root) if prompt_root else CANON_AGENTS) / f"{role}.md"
    if not prompt_path.is_file():
        return "failure", {"reason": "ROLE_PROMPT_MISSING"}
    work_dir = Path(cwd).resolve() if cwd is not None else ROOT
    try:
        work_dir.relative_to(ROOT)
    except ValueError:
        return "failure", {"reason": "CWD_OUTSIDE_ROOT"}
    handle = tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False, encoding="utf-8")
    handle.close()
    try:
        try:
            argv = compose_argv(role, model, sandbox, prompt_path.read_text(encoding="utf-8"),
                                effort=effort, output_path=handle.name)
        except (SpawnError, OSError) as exc:
            return "failure", {"reason": str(exc) if isinstance(exc, SpawnError) else "ROLE_PROMPT_MISSING"}
        try:
            # F-06 (review repair): same child-env hygiene as the opencode lane/probes
            # (CI/NO_COLOR/TERM=dumb) so an interactive TERM can never skew the header
            # `_MODEL_HEADER_RE` parses.
            proc = subprocess.run(argv, cwd=work_dir, input=compose_task(task, supplementary, vault_block),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout, check=False,
                                  env=dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb"))
        except (OSError, subprocess.TimeoutExpired) as exc:
            return "failure", {"reason": "CODEX_CRASH", "detail": _redact(str(exc))[:500]}
        try:
            last_message = Path(handle.name).read_text(encoding="utf-8").strip()
        except OSError:
            last_message = ""
    finally:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
    if proc.returncode != 0 or not last_message:
        return "failure", {"reason": "CODEX_CRASH", "exit_code": proc.returncode,
                           "stderr": _redact(proc.stderr.strip())[-500:]}
    header = _MODEL_HEADER_RE.search(proc.stdout)
    observed = header.group(1) if header else None
    if observed is not None and observed != model_id:
        return "model_mismatch", {"expected": model_id, "observed": observed,
                                  "result": _redact(last_message)[:500]}
    return "success", {"model": model_id, "model_verified": observed == model_id,
                       "result": _redact(last_message)[:500]}


def _persist_audit_binding(run_id: str, role: str, provider: str, model: str, *, routing_test_root=None) -> None:
    try:
        root = RoutingStore(root=Path(routing_test_root) if routing_test_root else None).ensure_cache_root()
        record = {"ts": time.time(), "run_id": run_id, "role": role, "provider": provider, "model": model}
        path = root / AUDIT_LOG_FILENAME
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        os.chmod(path, 0o600)
    except Exception:  # noqa: BLE001
        pass


def _run_app_cli(args, env=None, timeout=60, cwd=ROOT):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run([sys.executable, str(APP_CLI), *args], cwd=cwd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, check=False, env=full_env)


def dispatch_writer(role: str, task: str, run_id: str, provider: str, model: str, roster, *,
                    effort=None, routing_test_root=None, spawn_cwd=None, prompt_root=None,
                    timeout: float = CODEX_TIMEOUT_SECONDS) -> dict:
    """Writer-class ONLY; consumes an existing `run_id`, never re-decides. Same lifecycle
    shape and no-orphaned-run guarantee as the other lanes."""
    try:
        if _role_class(role, roster) != "writer":
            return {"status": "failure", "run_id": run_id, "reason": "ROLE_CLASS_MISMATCH"}
    except SpawnError as exc:
        return {"status": "failure", "run_id": run_id, "reason": str(exc)}
    routing_cwd = Path(spawn_cwd).resolve() if spawn_cwd is not None else ROOT
    try:
        routing_cwd.relative_to(ROOT)
    except ValueError:
        return {"status": "failure", "run_id": run_id, "reason": "CWD_OUTSIDE_ROOT"}
    env = {"SET_AGENTS_ROUTING_TEST_ROOT": routing_test_root} if routing_test_root else None
    # ADR-0056 (AC-12): fetched before the routing store is touched -- a vault-fetch
    # timeout/crash never burns the one-use `single_writer` authorization.
    vault_block = _fetch_vault_block(routing_cwd, routing_test_root=routing_test_root)
    _persist_audit_binding(run_id, role, provider, model, routing_test_root=routing_test_root)
    try:
        dispatched = _run_app_cli(["--route-dispatched", run_id, "--json"], env=env, cwd=routing_cwd)
        if dispatched.returncode != 0:
            _run_app_cli(["--route-terminal", run_id, "failure", "--json"], env=env, cwd=routing_cwd)
            return {"status": "failure", "run_id": run_id, "reason": "DISPATCH_FAILED"}
        started = time.time()
        outcome, detail = spawn(role, task, provider, model, roster, effort=effort,
                                expect_class="writer", prompt_root=prompt_root,
                                cwd=spawn_cwd, timeout=timeout, vault_block=vault_block)
        latency_ms = max(0, int((time.time() - started) * 1000))
        terminal = _run_app_cli(["--route-terminal", run_id,
                                 "success" if outcome == "success" else "failure",
                                 "--latency-ms", str(latency_ms), "--json"], env=env, cwd=routing_cwd)
    except Exception as exc:  # noqa: BLE001 - no orphaned authorized run
        try:
            _run_app_cli(["--route-terminal", run_id, "failure", "--json"], env=env, cwd=routing_cwd)
        except Exception:  # noqa: BLE001
            pass
        return {"status": "failure", "run_id": run_id, "reason": "ORCHESTRATION_EXCEPTION",
                "detail": _redact(str(exc))[:500]}
    return {"status": outcome, "run_id": run_id, "provider": provider, "model": model,
            "effort": effort, "detail": detail, "terminal_exit_code": terminal.returncode}


def dispatch_review(role: str, task: str, provider: str, model: str, roster, *,
                    effort=None, supplementary: str | None = None, prompt_root=None, cwd=None,
                    timeout: float = CODEX_TIMEOUT_SECONDS) -> dict:
    """Review-class ONLY. NO routing-store bookkeeping, ever."""
    try:
        if _role_class(role, roster) != "review":
            return {"status": "failure", "provider": provider, "model": model, "reason": "ROLE_CLASS_MISMATCH"}
    except SpawnError as exc:
        return {"status": "failure", "provider": provider, "model": model, "reason": str(exc)}
    vault_cwd = Path(cwd).resolve() if cwd is not None else ROOT
    vault_block = _fetch_vault_block(vault_cwd)
    outcome, detail = spawn(role, task, provider, model, roster, effort=effort,
                            expect_class="review", supplementary=supplementary,
                            prompt_root=prompt_root, cwd=cwd, timeout=timeout,
                            vault_block=vault_block)
    return {"status": outcome, "provider": provider, "model": model, "effort": effort, "detail": detail}


def dispatch_simulate(role: str, task: str, provider: str, model: str, roster, *,
                      effort=None, prompt_root=None, cwd=None,
                      timeout: float = CODEX_TIMEOUT_SECONDS) -> dict:
    """role_class `other` ONLY — refuses writer/review (ADR-0030 "Never fabricate
    enforcement"): zero bookkeeping, base role prompt at the decided model."""
    try:
        if _role_class(role, roster) != "other":
            return {"status": "failure", "provider": provider, "model": model, "reason": "ROLE_CLASS_MISMATCH"}
    except SpawnError as exc:
        return {"status": "failure", "provider": provider, "model": model, "reason": str(exc)}
    vault_cwd = Path(cwd).resolve() if cwd is not None else ROOT
    vault_block = _fetch_vault_block(vault_cwd)
    outcome, detail = spawn(role, task, provider, model, roster, effort=effort,
                            expect_class="other", prompt_root=prompt_root, cwd=cwd, timeout=timeout,
                            vault_block=vault_block)
    return {"status": outcome, "provider": provider, "model": model, "effort": effort, "detail": detail}


def _read_text_arg(value: str) -> str:
    if value == "-":
        return sys.stdin.read()
    try:
        return Path(value).read_text(encoding="utf-8")
    except OSError as exc:
        raise SpawnError("TASK_FILE_UNREADABLE") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dispatch-writer", action="store_true")
    mode.add_argument("--dispatch-review", action="store_true")
    mode.add_argument("--dispatch-simulate", action="store_true",
                      help="role_class 'other' only: no bookkeeping, base role prompt at the decided model")
    parser.add_argument("--role", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort")
    parser.add_argument("--task", required=True, metavar="FILE",
                        help="task text FILE ('-' = stdin) -- never inline argv text")
    parser.add_argument("--run-id", metavar="RUN_ID")
    parser.add_argument("--supplementary", metavar="FILE")
    parser.add_argument("--spawn-cwd", metavar="DIR")
    parser.add_argument("--cwd", metavar="DIR")
    parser.add_argument("--timeout", type=float, default=CODEX_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    if args.dispatch_writer and not args.run_id:
        parser.error("--dispatch-writer requires --run-id")
    if not args.dispatch_writer and args.run_id:
        parser.error("--run-id is --dispatch-writer only")
    if args.supplementary is not None and not args.dispatch_review:
        parser.error("--supplementary is --dispatch-review only")
    if args.task == "-" and args.supplementary == "-":
        parser.error("--task - and --supplementary - cannot both read stdin")
    roster = models_config.load_roster()
    try:
        task = _read_text_arg(args.task)
    except SpawnError as exc:
        print(json.dumps({"status": "failure", "reason": str(exc)}, sort_keys=True))
        return 1
    if args.dispatch_writer:
        result = dispatch_writer(args.role, task, args.run_id, args.provider, args.model, roster,
                                 effort=args.effort, spawn_cwd=args.spawn_cwd, timeout=args.timeout)
    elif args.dispatch_review:
        supplementary = None
        if args.supplementary is not None:
            try:
                supplementary = _read_text_arg(args.supplementary)
            except SpawnError as exc:
                print(json.dumps({"status": "failure", "reason": str(exc)}, sort_keys=True))
                return 1
        result = dispatch_review(args.role, task, args.provider, args.model, roster,
                                 effort=args.effort, supplementary=supplementary,
                                 cwd=args.cwd, timeout=args.timeout)
    else:
        result = dispatch_simulate(args.role, task, args.provider, args.model, roster,
                                   effort=args.effort, cwd=args.cwd, timeout=args.timeout)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
