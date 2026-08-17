#!/usr/bin/env python3
"""OpenCode-lane CLI subprocess spawn primitive (ADR-0032, closes ADR-0030's gap).

Why this exists: the OpenCode-hosted orchestrator delegates in-process via the harness's
own task tool, where the child's model is whatever the installed agent file's `model:`
line says — a STATIC value. Only the six tiered roles have `<role>@<tier>` variants that
embody a routed model choice; the ~22 non-tiered roles always ran their curated
`models.toml` default and recorded `MODEL_STATIC_FALLBACK` (ADR-0030 named that a
visible degrade, this module retires it as the NORMAL path). Here, the decided model is
applied AT SPAWN TIME for ANY roster role: `opencode run -m <provider-mapped-model>
[--variant <effort>] --agent <role> --format json` (task via stdin) — live-verified against the
installed opencode 1.18.10 this feature's own evidence session (`opencode run --help`:
`-m, --model  model to use in the format of provider/model`; `--variant  model variant
(provider-specific reasoning effort, e.g., high, max, minimal)`; a run with
`-m opencode/north-mini-code-free --variant xhigh` completed normally).

Structural precedent: `ai/scripts/claude_code_spawn.py` (contract 015). Same discipline,
never a call into that module: separate lane, separate curated model-id mapping, same
three-way outcome shape, same redaction/containment posture. The `@tier` variants and
the in-process delegation path KEEP existing — this module is the additive dynamic path
(ADR-0030: "this change adds a dynamic road, it does not delete the variants").

Model-id mapping (catalog identity -> opencode `provider/model` ref), ADR-0034 (019
PKG-1, AC-03): read from `routing_core.catalog._OPENCODE_CLI_IDS` -- the SAME table the
catalog itself probes and validates identities against, never a second hand-kept copy:
  - `openai-codex` -> `openai/<model>` (the exact prefix every `models.toml`
    opencode-lane value already uses for this provider, e.g. `openai/gpt-5.6-sol`).
  - `opencode-zen` -> `opencode/<model>`; `opencode-go` -> `opencode-go/<model>`
    (the provider ids `routing_core.catalog`'s own `opencode models <provider>` probes
    use — reachable only through ADR-0029/ADR-0034's discovered-routes path).
  - `anthropic` fails closed (`PROVIDER_UNSUPPORTED`) even though the shared table
    carries an entry for it: anthropic decisions are served by the `claude-code`
    cross-lane redirect (`service._PROVIDER_RUNTIME_REDIRECTS`), never ad-hoc through an
    unverified opencode auth surface. `PROVIDER_UNSUPPORTED` is reserved for that one
    deliberate exclusion plus anything genuinely absent from the shared table -- never
    for a provider the router already authorized through a different, desynced copy of
    this mapping (the exact defect this ADR closes).

Effort: `--variant <effort>` for the closed routing universe {low, medium, high, xhigh}
only — advisory, exactly like pi's `--thinking` (ADR-0030 effort extension): an absent
or unknown effort omits the flag, never fails a spawn. opencode itself treats a variant
a model does not define as a no-op (live-verified above), so this can degrade silently
by CLI design; the decision's effort is still recorded via `record-spawn --effort`.

Model verification limit (documented, not silent): opencode's `--format json` event
stream (step_start/text/step_finish observed live) does not echo the serving model id,
so this lane has no post-hoc model-mismatch classification — `detail["model_verified"]`
is always False. An invalid `-m` ref fails the run itself (nonzero exit -> failure).

Task delivery (F-01, this feature's own review repair): via STDIN, never a trailing
argv positional — live-verified this session (`echo <prompt> | opencode run --pure -m
opencode/north-mini-code-free --format json` answered the prompt normally). A positional
would hit Linux's MAX_ARG_STRLEN (128 KiB per argv element — a real package-review diff
exceeds it routinely) and expose the full task in `/proc/<pid>/cmdline`; stdin has
neither problem and removes the flag-injection channel a positional would carry
(`claude_code_spawn` R2-07 / `codex_spawn` use stdin for the same reasons).

Role classes and lifecycle (mirrors `claude_code_spawn`, plus ONE new mode):
  - `--dispatch-writer` (code-rw): CONSUMES an existing `--route-decide` `run_id`;
    drives `--route-dispatched -> spawn -> --route-terminal`. Never re-decides.
  - `--dispatch-review` (review-ro audit/judge): zero routing-store bookkeeping (review
    decisions carry no run_id by construction); nonce-fenced `--supplementary`.
  - `--dispatch-simulate` (every OTHER role class — the ADR-0030 simulate universe):
    zero bookkeeping (a simulate decision authorizes nothing durable — "Never fabricate
    enforcement"), plain spawn of the BASE agent with the decided model applied. This
    mode REFUSES code-rw and audit/judge review-ro roles (ROLE_CLASS_MISMATCH): a writer
    without an authorized run, or a reviewer without independence routing, must never
    enter through this unbookkept door.

Tool ceiling: the installed `~/.config/opencode/agent/<role>.md` file carries the
role's generated permission map (`generate.py::oc_permissions`) and opencode enforces it
natively per agent — `--agent <role>` is therefore the ceiling selector; this module
never composes a wider surface than the agent file grants, and never passes `--auto`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config  # noqa: E402
from spawn_task_fence import compose_task_payload  # noqa: E402
from routing_core.store import RoutingStore  # noqa: E402  (audit-binding sink, SEC-P1-003 precedent)
from routing_core.usage import normalize_opencode  # noqa: E402  (023 PKG-B2: the ONE translator for this
# lane's own `{"tokens": {...}}` wire shape into the store's flat vocabulary -- never a second,
# independently-drifting copy of that mapping here; see `routing_core/usage.py`'s module docstring)

ROOT = Path(__file__).resolve().parents[2]
APP_CLI = ROOT / "ai/scripts/set_agents_app.py"

OPENCODE_BIN = "opencode"
OPENCODE_TIMEOUT_SECONDS = 300.0
AUDIT_LOG_FILENAME = "opencode_spawn_audit.jsonl"

# ADR-0030 effort extension: closed set on purpose — anything outside it (None included)
# omits the flag; an advisory knob never fails a spawn or reaches argv unvalidated.
_OPENCODE_VARIANT_LEVELS = frozenset({"low", "medium", "high", "xhigh"})

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
# cerrado", per-process cache). Duplicated here, not imported: this module is, by this
# feature's own deliberate architecture (module docstring above, "never a call into"
# `claude_code_spawn`), a SEPARATE lane module.
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
# ADR-0034 (019 PKG-1, AC-03): this used to be a SEPARATE, partial copy of
# `routing_core.catalog._OPENCODE_CLI_IDS` (missing `anthropic`, kept in sync only by
# hand) -- a provider the router authorized through the discovered-routes path could
# reach here, find no entry, and die `PROVIDER_UNSUPPORTED` AFTER already being
# authorized (Codex audit finding #4). `opencode_model_ref` below now reads the SAME
# table the catalog probes and validates against, imported lazily (this module is a
# leaf, `routing_core.catalog` is not on its normal import path) -- one source, never
# two copies to desync again. `anthropic` is EXCLUDED here on purpose even though the
# catalog table carries it: anthropic decisions are served by the `claude-code`
# cross-lane redirect (`service._PROVIDER_RUNTIME_REDIRECTS`), never through an
# unverified opencode auth surface, so it stays a hard `PROVIDER_UNSUPPORTED` here
# regardless of what the shared table says.


def opencode_model_ref(provider: str, model: str) -> str:
    """Catalog (provider, model) -> opencode `provider/model` ref. Fails closed for
    anthropic (the claude-code redirect owns it) and any unknown provider."""
    from routing_core.catalog import _OPENCODE_CLI_IDS  # lazy: this module is a leaf
    prefix = None if provider == "anthropic" else _OPENCODE_CLI_IDS.get(provider)
    if prefix is None:
        raise SpawnError("PROVIDER_UNSUPPORTED")
    if not _MODEL_TOKEN_RE.fullmatch(model or ""):
        raise SpawnError("MODEL_TOKEN_INVALID")
    return f"{prefix}/{model}"


def _role_class(role: str, roster) -> str:
    """`writer` (code-rw) / `review` (review-ro audit|judge) / `other` — the same closed
    classification `RoutingService._role_class` derives, recomputed from the roster row
    (never imported from the sealed service composition)."""
    if isinstance(roster, dict):
        item = roster.get(role)
    else:
        item = next((row for row in roster if row.get("role") == role), None)
    if item is None:
        raise SpawnError("ROLE_UNKNOWN")
    if item.get("capability") == "code-rw":
        return "writer"
    if item.get("capability") == "review-ro" and item.get("duty") in {"audit", "judge"}:
        return "review"
    return "other"


def compose_task(task: str, supplementary: str | None = None, vault_block: str | None = None) -> str:
    """SEC-004 precedent (`claude_code_spawn.compose_task`): review supplementary content
    is untrusted data-under-review, fenced by a per-call random nonce delimiter. ADR-0056
    (AC-12): `vault_block`, when given, is the ALREADY-fenced text `_fetch_vault_block`
    returns (context_pack._mark_untrusted's own per-call nonce, never a second scheme) --
    placed AHEAD of everything else. None by default; return value is byte-identical to
    the pre-ADR-0056 shape whenever it is omitted."""
    return compose_task_payload(task, supplementary, vault_block, token_hex=secrets.token_hex)


def compose_argv(role: str, provider: str, model: str, effort=None) -> list[str]:
    """`opencode run -m <ref> [--variant <effort>] --agent <role> --format json` — the
    task itself is appended by `spawn()` as the trailing positional AFTER the SEC-A01
    guard passes; it is never a member of this list."""
    if role.startswith("-"):
        raise SpawnError("ARGV_TOKEN_INVALID")
    ref = opencode_model_ref(provider, model)
    variant = ("--variant", effort) if effort in _OPENCODE_VARIANT_LEVELS else ()
    return [OPENCODE_BIN, "run", "-m", ref, *variant, "--agent", role, "--format", "json"]


def _probe_env():
    return dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")


def _parse_events(stdout: str) -> list[dict]:
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    return events


def spawn(role: str, task: str, provider: str, model: str, roster, *,
          effort=None, expect_class: str | None = None, supplementary: str | None = None,
          cwd=None, timeout: float = OPENCODE_TIMEOUT_SECONDS,
          vault_block: str | None = None) -> tuple[str, dict]:
    """One opencode child. Returns `(outcome, detail)` — `success` / `failure`; this lane
    has NO `model_mismatch` classification (module docstring: the JSON event stream never
    echoes the serving model), so `detail["model_verified"]` is always False on success.
    Never raises for a child-side failure."""
    try:
        role_class = _role_class(role, roster)
    except SpawnError as exc:
        return "failure", {"reason": str(exc)}
    if expect_class is not None and role_class != expect_class:
        return "failure", {"reason": "ROLE_CLASS_MISMATCH"}
    try:
        argv = compose_argv(role, provider, model, effort=effort)
    except SpawnError as exc:
        return "failure", {"reason": str(exc)}
    stdin_text = compose_task(task, supplementary, vault_block)
    work_dir = Path(cwd).resolve() if cwd is not None else ROOT
    try:
        work_dir.relative_to(ROOT)
    except ValueError:
        return "failure", {"reason": "CWD_OUTSIDE_ROOT"}
    # F-01 (review repair): the task rides STDIN, never argv — no MAX_ARG_STRLEN
    # ceiling, no /proc/<pid>/cmdline exposure, no flag-injection channel.
    try:
        proc = subprocess.run(argv, cwd=work_dir, input=stdin_text,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              check=False, env=_probe_env())
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "failure", {"reason": "OPENCODE_CRASH", "detail": _redact(str(exc))[:500]}
    events = _parse_events(proc.stdout)
    if proc.returncode != 0 or not events:
        return "failure", {"reason": "OPENCODE_CRASH", "exit_code": proc.returncode,
                           "stderr": _redact(proc.stderr.strip())[-500:]}
    text_parts = [event["part"].get("text", "") for event in events
                  if event.get("type") == "text" and isinstance(event.get("part"), dict)]
    tokens = next((event["part"].get("tokens") for event in reversed(events)
                   if event.get("type") == "step_finish" and isinstance(event.get("part"), dict)), None)
    if not any(event.get("type") == "step_finish" for event in events):
        return "failure", {"reason": "OPENCODE_NO_STEP_FINISH", "exit_code": proc.returncode,
                           "stderr": _redact(proc.stderr.strip())[-500:]}
    return "success", {"model_ref": opencode_model_ref(provider, model), "model_verified": False,
                       "result": _redact("\n".join(text_parts))[:500],
                       "tokens": tokens if isinstance(tokens, dict) else {}}


def _persist_audit_binding(run_id: str, role: str, provider: str, model: str, *, routing_test_root=None) -> None:
    """SEC-P1-003 precedent: durable decision-to-spawn binding, purely observational."""
    try:
        root = RoutingStore(root=Path(routing_test_root) if routing_test_root else None).ensure_cache_root()
        record = {"ts": time.time(), "run_id": run_id, "role": role, "provider": provider, "model": model}
        path = root / AUDIT_LOG_FILENAME
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        os.chmod(path, 0o600)
    except Exception:  # noqa: BLE001 - never gates the dispatch
        pass


def _run_app_cli(args, env=None, timeout=60, cwd=ROOT):
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run([sys.executable, str(APP_CLI), *args], cwd=cwd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, check=False, env=full_env)


def dispatch_writer(role: str, task: str, run_id: str, provider: str, model: str, roster, *,
                    effort=None, routing_test_root=None, spawn_cwd=None,
                    timeout: float = OPENCODE_TIMEOUT_SECONDS) -> dict:
    """Writer-class ONLY. CONSUMES an already-authorized `run_id` (the caller already ran
    `--route-decide`); drives `--route-dispatched -> spawn -> --route-terminal`. Never
    re-decides (a second decide call burns a second one-use `single_writer`
    authorization). Any exception past dispatch closes the run failure, best-effort —
    an authorized run is never left open (SEC-A03/PKG-N01 precedent)."""
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
                                expect_class="writer", cwd=spawn_cwd, timeout=timeout,
                                vault_block=vault_block)
        latency_ms = max(0, int((time.time() - started) * 1000))
        terminal_args = ["--route-terminal", run_id, "success" if outcome == "success" else "failure",
                         "--latency-ms", str(latency_ms), "--json"]
        # 023-senales-de-consumo PKG-B2 (ADR-0045): this lane's own `tokens` sub-object
        # (the `step_finish` event's `part.tokens`, module docstring/`spawn()` above) is
        # genuinely what opencode reports -- never invented here -- but it is not the
        # store's flat vocabulary, so `_usage_row` could not recognize it (PKG-B1
        # hardening turned that mismatch into a COUNTED `invalid`, never a silent NULL
        # row). `normalize_opencode` is the ONE place that already measured this exact
        # wire shape and translates it; this is the wiring, not a second translation.
        tokens = detail.get("tokens")
        base_terminal_args = list(terminal_args)
        if isinstance(tokens, dict) and tokens:
            translated = normalize_opencode({"tokens": tokens})
            if translated:
                terminal_args += ["--usage", json.dumps(translated)]
        terminal = _run_app_cli(terminal_args, env=env, cwd=routing_cwd)
        # F-05 (review repair): usage telemetry is advisory — if the close WITH --usage
        # was rejected (e.g. a hostile/oversized tokens blob failing parse_usage), retry
        # once WITHOUT it so the authorized run still closes instead of staying open.
        if terminal.returncode != 0 and terminal_args is not base_terminal_args and "--usage" in terminal_args:
            terminal = _run_app_cli(base_terminal_args, env=env, cwd=routing_cwd)
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
                    effort=None, supplementary: str | None = None, cwd=None,
                    timeout: float = OPENCODE_TIMEOUT_SECONDS) -> dict:
    """Review-class ONLY. NO routing-store bookkeeping, ever (review decisions carry
    `run_id=None` by construction)."""
    try:
        if _role_class(role, roster) != "review":
            return {"status": "failure", "provider": provider, "model": model, "reason": "ROLE_CLASS_MISMATCH"}
    except SpawnError as exc:
        return {"status": "failure", "provider": provider, "model": model, "reason": str(exc)}
    vault_cwd = Path(cwd).resolve() if cwd is not None else ROOT
    vault_block = _fetch_vault_block(vault_cwd)
    outcome, detail = spawn(role, task, provider, model, roster, effort=effort,
                            expect_class="review", supplementary=supplementary, cwd=cwd, timeout=timeout,
                            vault_block=vault_block)
    return {"status": outcome, "provider": provider, "model": model, "effort": effort, "detail": detail}


def dispatch_simulate(role: str, task: str, provider: str, model: str, roster, *,
                      effort=None, cwd=None, timeout: float = OPENCODE_TIMEOUT_SECONDS) -> dict:
    """The ADR-0030 simulate universe ONLY (role_class `other`). A simulate decision
    authorizes nothing durable — this mode does zero bookkeeping and REFUSES writer and
    review roles: a code-rw child without an authorized run, or an audit/judge reviewer
    without independence routing, must never enter through this door."""
    try:
        if _role_class(role, roster) != "other":
            return {"status": "failure", "provider": provider, "model": model, "reason": "ROLE_CLASS_MISMATCH"}
    except SpawnError as exc:
        return {"status": "failure", "provider": provider, "model": model, "reason": str(exc)}
    vault_cwd = Path(cwd).resolve() if cwd is not None else ROOT
    vault_block = _fetch_vault_block(vault_cwd)
    outcome, detail = spawn(role, task, provider, model, roster, effort=effort,
                            expect_class="other", cwd=cwd, timeout=timeout, vault_block=vault_block)
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
                      help="role_class 'other' only: no bookkeeping, base agent at the decided model")
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
    parser.add_argument("--timeout", type=float, default=OPENCODE_TIMEOUT_SECONDS)
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
