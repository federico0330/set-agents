#!/usr/bin/env python3
"""Pi lane CLI-subprocess spawner (contract 004 T-303/T-304, ADR-0007).

Architecture (deliberate deviation from the original plan, proven live by the T-300
spike): pi is spawned as a CLI subprocess — `pi --model <provider>/<id> --print --mode
json --no-session --no-extensions --tools <allowlist> --append-system-prompt <role.md>
<task>` — never through an in-process TypeScript/SDK host. This mirrors how the harness
already spawns opencode/codex (ai/scripts/set_agents_app.py). No agent tree is
generated for pi: the canonical role prompt already installed at
`Global/_canonical/agents/<role>.md` IS the role artifact, passed verbatim via
`--append-system-prompt` (see docs/adr/0007-pi-lane.md).

Guards-as-flags (002 AC-04 doctrine, enforced AT THIS EXTENSION per contract 004
AC-11g): `--no-session` (fresh ephemeral context, nothing persisted), `--no-extensions`
(pi-subagents — the ONLY delegation path Pi ships — never loads, so a spawned child has
no delegation tool and is depth 0), and `--no-context-files` (a project-local
`spawn_cwd` can never auto-load its own AGENTS.md/CLAUDE.md config into the child) are
UNCONDITIONAL on every invocation `spawn()` builds, regardless of the tool allowlist
tier. Only the `-t` allowlist widens from GUARD_TOOLS_READONLY to GUARD_TOOLS_CODE_RW —
and `route_and_spawn`/`main()` (the routed/CLI path this package actually wires up) never
expose a way to select that wider tier at all (SEC-A02, repair R1): `GUARD_TOOLS_CODE_RW`
is reachable only by a caller of the low-level `spawn()` primitive directly (e.g. a
future package's own tests), never through this package's own lifecycle entry points,
until a bash-sandbox story exists that prevents a code-rw child from re-invoking pi
itself (see docs/adr/0007-pi-lane.md Decision 2).

SEC-A01 (repair R1): the untrusted `task` is the trailing positional in pi's argv, and
pinned pi 0.81.1 REJECTS a bare `--` end-of-options sentinel (`Unknown option: --`), so
`--` can never be used to separate it from the flags that precede it. Live confirmation
(2026-07-27, pinned 0.81.1): a task of exactly `--offline` is silently consumed by pi's
OWN argument parser as a recognized boolean flag rather than reaching pi as message
text — proving a hostile trailing token can override or add to the invocation's own
options, last-wins, rather than merely being ignored. `spawn()` therefore fails closed
BEFORE ever building the argv or starting a subprocess whenever `task.lstrip()` starts
with `-` (`SpawnError`-shaped `("failure", {"reason": "TASK_LOOKS_LIKE_FLAG"})`).

Lifecycle (T-303): the caller (or `main()` below) drives P1's durable lifecycle over the
SAME dispatch CLI the OpenCode lane uses — `--route-decide` -> (writer authorized) ->
`--route-dispatched` -> spawn the pi child -> `--route-terminal <success|failure>`. A
non-executable decision never spawns a session; the refusal reason IS the tool result
(AC-11). A crash (exit code != 0, or a completed process missing the `agent_settled`
terminal event) always closes the run as `failure` — never left open.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from routing_core import catalog
from routing_core.domain import classify_pi_terminal_error
from routing_core.store import RoutingStore

ROOT = Path(__file__).resolve().parents[2]
APP_CLI = ROOT / "ai/scripts/set_agents_app.py"
CANON_AGENTS = ROOT / "Global/_canonical/agents"

# T-304/AC-11g: read-only until each guard's test is green (protected-path write,
# argv/cwd/env manipulation, delegation attempt — see tests/test_routing.py). Children
# get exactly this allowlist by default; code-rw is a documented FUTURE state, never the
# default composed by route_and_spawn/spawn below.
GUARD_TOOLS_READONLY = ("read", "grep", "find", "ls")
# SEC-A02 (repair R1): a code-rw child has `bash`, which can re-invoke the very same
# `pnpm dlx ... pi ...` command this spawner uses and spawn ITS OWN pi children —
# `--no-extensions` only blocks pi's in-process pi-subagents extension, it does nothing
# to stop a shell re-exec of the pi binary itself. Widening to this tier therefore
# requires a bash-sandbox story (a restricted shell / container / seccomp profile that
# denies re-invoking pi or reaching the network pi needs) that does not exist yet — see
# docs/adr/0007-pi-lane.md Decision 2. Until then this tuple is a documented future
# constant only: no code path in this module (route_and_spawn, main()) ever composes it;
# only a direct, out-of-package caller of the low-level `spawn()` primitive can reach it.
GUARD_TOOLS_CODE_RW = ("read", "grep", "find", "ls", "bash", "edit", "write")

PI_TIMEOUT_SECONDS = 300.0
DOCTOR_TIMEOUT_SECONDS = 60.0  # pi --list-models may cold-install via pnpm on first run.

# SEC-A05 (repair R1, DiD): the child inherits the full `os.environ` (T-304 argv/cwd/env
# guard only promises the TASK text has no channel into env — it says nothing about what
# pi itself might echo back on stderr from that inherited environment or a provider error
# body). Raw stderr is therefore never persisted verbatim; known secret shapes are
# redacted first, then every persisted/returned text field stays short.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+"),
)


def _redact(text: str) -> str:
    """Best-effort redaction of common secret shapes; never raises, never widens input."""
    if not text:
        return ""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class SpawnError(Exception):
    """A stable, non-secret reason string; never a bare traceback."""


# ADR-0056 (amends ADR-0012, AC-12, 025/D5): see `claude_code_spawn._fetch_vault_block`'s
# own docstring for the full rationale (sanctioned `--context --json` channel, why an
# in-process re-implementation would be a circular import here in particular -- this
# module is what `set_agents_app.py` itself imports at its own top level, `set_agents_
# app.py:37`, so a `import set_agents_app` from THIS module would be a direct, guaranteed
# cycle, not merely a theoretical one -- "obligatorio" != "falla cerrado", per-process
# cache). Duplicated here, not imported: this module is, by this feature's own deliberate
# architecture, a SEPARATE lane module from the other three spawners.
_VAULT_FETCH_TIMEOUT_SECONDS = 10.0
_VAULT_NONE_LINKED_NOTE = "[vault: none linked for this project; spawn proceeds without it]"
_VAULT_DEGRADED_NOTE = "[vault: lookup failed; spawn proceeds without it]"
VAULT_DEGRADATION_LOG_FILENAME = "vault_degradation.jsonl"
# Cache only settled outcomes. Transient failures must be retried by the next spawn.
_vault_block_cache: dict[str, str] = {}


def _persist_vault_degradation(reason: str, *, routing_test_root=None) -> None:
    """Record a failed vault lookup without making the spawn fail."""
    try:
        root = RoutingStore(root=Path(routing_test_root) if routing_test_root else None).ensure_cache_root()
        path = root / VAULT_DEGRADATION_LOG_FILENAME
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"ts": time.time(), "reason": reason}, sort_keys=True) + "\n")
        os.chmod(path, 0o600)
    except Exception:  # noqa: BLE001 - observational only
        pass


def _fetch_vault_block(cwd, *, timeout: float = _VAULT_FETCH_TIMEOUT_SECONDS,
                       routing_test_root=None) -> str:
    key = str(Path(cwd).resolve()) if cwd is not None else str(ROOT)
    if key in _vault_block_cache:
        return _vault_block_cache[key]
    try:
        proc = subprocess.run(
            [sys.executable, str(APP_CLI), "--context", "--json", "--project", key],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout, check=False,
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


def _probe_env():
    # Same CI/NO_COLOR/TERM hygiene routing_core.catalog uses for the other probes: pi's
    # TUI must never block on a non-tty stdout, and locale/ANSI noise must never enter
    # parsed output. This dict is the ENTIRE child environment surface the spawner
    # controls; task text has no channel into it (T-304 argv/cwd/env guard).
    return dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")


def pi_model_id(provider: str, model: str) -> str:
    """Catalog (provider, model) -> Pi `provider/id` (ADR-0007's model-id map). Raises
    SpawnError('MODEL_ID_UNMAPPED') for an anthropic short name with no curated mapping —
    fails closed, never guesses a Pi id."""
    if provider == "openai-codex":
        return f"openai-codex/{model}"
    if provider == "anthropic":
        mapped = catalog.PI_MODEL_MAP.get("anthropic", {}).get(model)
        if not mapped:
            raise SpawnError("MODEL_ID_UNMAPPED")
        return f"anthropic/{mapped}"
    raise SpawnError("PROVIDER_UNSUPPORTED")


def doctor(timeout: float = DOCTOR_TIMEOUT_SECONDS) -> dict:
    """Redacted pi doctor report (AC-09): pinned-version resolution, auth.json
    KEY-SET (provider names only, never values), and `pi --list-models` OK/FAIL. Never
    reads or returns credential contents — set_agents_app's `--doctor --harness pi`
    prints exactly this dict."""
    result = {
        "pinned_version": catalog.PI_PINNED_VERSION,
        "version_ok": False,
        "auth_providers": [],
        "list_models_ok": False,
    }
    try:
        proc = subprocess.run(catalog.pi_pinned_argv("--version"), stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              timeout=timeout, check=False, env=_probe_env())
        result["version_ok"] = proc.returncode == 0 and proc.stdout.strip() == catalog.PI_PINNED_VERSION
    except (OSError, subprocess.TimeoutExpired):
        pass
    result["auth_providers"] = sorted(catalog.pi_auth_provider_keys())
    try:
        proc = subprocess.run(catalog.pi_pinned_argv("--list-models"), stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              timeout=timeout, check=False, env=_probe_env())
        result["list_models_ok"] = proc.returncode == 0 and bool(proc.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    result["doctor_green"] = bool(
        result["version_ok"] and result["list_models_ok"]
        and {"anthropic", "openai-codex"} & set(result["auth_providers"])
    )
    return result


def _parse_events(stdout: str) -> list[dict]:
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue  # a stray non-JSON line (banner/noise) never aborts the rest of the stream
        if isinstance(parsed, dict):
            events.append(parsed)
    return events


# SEC-A04 (repair R1, DiD): pi 0.81.1's CLI subprocess mode never threads the SDK's
# `modelFallbackMessage` into the --mode json stdout stream (verified against the pinned
# source: `createAgentSession`'s `modelFallbackMessage` is only forwarded into
# `InteractiveMode`, never into `runPrintMode`). But pi's own CLI model resolver
# (`resolveCliModel`) DOES emit an equivalent plain-text warning to STDERR whenever it
# silently substitutes a different real model's underlying config under the requested,
# unmatched id ("Using custom model id.") or fails to restore a saved session's model
# ("Could not restore model ...") — confirmed live (2026-07-27, pinned 0.81.1,
# `--model openai-codex/not-a-real-model`): the assistant message still ECHOES the
# requested (fake) id, so the plain `observed == target_id` check below cannot see this
# on its own. Any of these markers on stderr means the decided model may not be what
# actually ran and is scanned for on every spawn, not just the crash path.
_MODEL_FALLBACK_MARKERS = ("Using custom model id.", "Could not restore model", "No models available")


def _model_fallback_marker(stderr_text: str) -> str | None:
    if not stderr_text:
        return None
    for marker in _MODEL_FALLBACK_MARKERS:
        if marker in stderr_text:
            return _redact(stderr_text.strip())[-500:]
    return None


# ADR-0030 (effort extension): the route decision's effort maps 1:1 onto pi's own
# `--thinking` levels. Closed set on purpose — anything outside it (None included)
# simply omits the flag: an advisory knob must never fail a spawn or reach argv
# unvalidated.
_PI_THINKING_LEVELS = frozenset({"off", "minimal", "low", "medium", "high", "xhigh", "max"})


def spawn(role: str, task: str, provider: str, model: str, prompt_path,
          guard_tools=GUARD_TOOLS_READONLY, cwd=None, timeout: float = PI_TIMEOUT_SECONDS,
          effort=None, vault_block: str | None = None):
    """One guarded pi child (T-303/T-304). Returns `(outcome, detail)`:

    - `("success", {"model": ..., "usage": ...})` — agent_settled reached, exit 0, the
      decided model matched, and the final turn did not end in an API error.
    - `("model_mismatch", {"expected": ..., "observed": ...})` — pi echoed back a
      different `provider/model` than requested (AC-11: never treated as success), or
      (SEC-A04) pi's stderr carries a fallback/no-restore marker even though the echoed
      model matched — a silent substitution is never trusted just because the reported
      id lines up.
    - `("failure", {"reason": ..., ...})` — crash (exit != 0 or no `agent_settled`), an
      unmapped model id, a missing role prompt, a task that lexically looks like a flag
      (SEC-A01), or a final turn that ended in an API error (`stopReason == "error"`) — a
      defensive extra beyond the literal T-303 crash rule, since an errored-but-exit-0
      turn is not a usable result either.

    Never raises for a child-side failure; only SpawnError-shaped reasons are returned.
    `cwd` defaults to a fresh, isolated scratch directory that is removed afterward (pi
    mutates its cwd — spike note) — never the caller's own working directory.
    """
    try:
        target_id = pi_model_id(provider, model)
    except SpawnError as exc:
        return "failure", {"reason": str(exc)}
    prompt_path = Path(prompt_path)
    if not prompt_path.is_file():
        return "failure", {"reason": "ROLE_PROMPT_MISSING"}
    # SEC-A01: fail closed BEFORE building the argv or starting any subprocess whenever
    # the untrusted task lexically looks like a flag — pinned pi cannot be given a `--`
    # end-of-options sentinel (it rejects it outright), and a task that pi's OWN parser
    # recognizes as an option is consumed as one, last-wins, never reaching pi as message
    # text (live-confirmed, see module docstring).
    if task.lstrip().startswith("-"):
        return "failure", {"reason": "TASK_LOOKS_LIKE_FLAG"}
    # ADR-0056 (AC-12, D5-F05): the fenced vault is composed AHEAD of the task in the
    # single positional prompt payload (`composed_task`) so the child sees one linear
    # context block exactly like the other lanes' `compose_task` output. The SEC-A01
    # flag-lookalike check above runs on the ORIGINAL caller-supplied `task` only -- a
    # vault block can never suppress it.
    own_scratch = cwd is None
    work_dir = Path(cwd) if cwd is not None else Path(tempfile.mkdtemp(prefix="pi-spawn-"))
    # T-304 guards: --no-session, --no-extensions, --no-context-files, --no-skills, and
    # --no-prompt-templates are UNCONDITIONAL — never gated by guard_tools, never
    # omitted. Only the -t allowlist varies by tier. The last two close 013-
    # pi-interactive-target AC-01/AC-12: once Global/pi/skills/** and
    # Global/pi/prompts/** are installed under ~/.pi/agent/, every dispatch-lane pi
    # child would otherwise auto-discover and load this harness's own skill catalog
    # and prompt library too — added context weight the dispatch lane's original,
    # minimal-and-auditable design never accounted for (see docs/adr/0007-pi-lane.md,
    # amended by docs/adr/0017-pi-interactive-target.md).
    thinking = ("--thinking", effort) if effort in _PI_THINKING_LEVELS else ()
    composed_task = f"{vault_block}\n\n{task}" if vault_block else task
    argv = catalog.pi_pinned_argv(
        "--model", target_id, *thinking, "--print", "--mode", "json", "--no-session", "--no-extensions",
        "--no-context-files", "--no-skills", "--no-prompt-templates", "--tools", ",".join(guard_tools),
        "--append-system-prompt", str(prompt_path), composed_task,
    )
    try:
        proc = subprocess.run(argv, cwd=work_dir, input="", stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=timeout, check=False, env=_probe_env())
    except (OSError, subprocess.TimeoutExpired) as exc:
        # SEC-A05: never persist a raw exception string verbatim (it can embed the fixed
        # argv/cwd, which is not secret, but is kept short and redacted anyway for DiD).
        return "failure", {"reason": "PI_CRASH", "detail": _redact(str(exc))[:500]}
    finally:
        if own_scratch:
            shutil.rmtree(work_dir, ignore_errors=True)
    events = _parse_events(proc.stdout)
    settled = any(event.get("type") == "agent_settled" for event in events)
    if proc.returncode != 0 or not settled:
        # SEC-A05: stderr is redacted and capped well short of a raw dump — the child
        # inherits the full os.environ, so an unexpected value here is never trusted as
        # secret-free by default.
        return "failure", {"reason": "PI_CRASH", "exit_code": proc.returncode,
                           "stderr": _redact(proc.stderr.strip())[-500:]}
    # 007-P2 review finding (F-PR-02, upheld by finding-verifier): this loop used to run
    # AFTER the `model_mismatch`/`PI_TURN_ERROR` returns below, so `last_assistant` did not
    # exist yet at those points and none of the three non-success-but-settled outcomes ever
    # reported usage — a spawn that burned real tokens and then mismatched or errored was
    # recorded `usage_status='absent'` ("never spawned") instead of `ok`/`invalid`, the
    # exact blindness this feature exists to end. Hoisted so every outcome below it can see
    # whatever usage the last assistant turn actually reported, if any.
    last_assistant = None
    for event in events:
        message = event.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            last_assistant = message
    fallback = _model_fallback_marker(proc.stderr)
    if fallback is not None:
        return "model_mismatch", {"expected": target_id, "observed": target_id,
                                  "reason": "PI_MODEL_FALLBACK", "detail": fallback,
                                  "usage": (last_assistant or {}).get("usage") or {}}
    if last_assistant is None:
        return "failure", {"reason": "PI_NO_ASSISTANT_MESSAGE"}
    observed = f"{last_assistant.get('provider')}/{last_assistant.get('model')}"
    if observed != target_id:
        return "model_mismatch", {"expected": target_id, "observed": observed,
                                  "usage": last_assistant.get("usage") or {}}
    if last_assistant.get("stopReason") == "error":
        raw_error = last_assistant.get("error")
        normalized = {"settled": True, "provider": provider}
        if isinstance(raw_error, dict):
            normalized.update({"http_status": raw_error.get("status"), "type": raw_error.get("type"),
                               "marker": raw_error.get("message")})
        detail = {"reason": "PI_TURN_ERROR", "detail": _redact(last_assistant.get("errorMessage") or "")[:500],
                  "usage": last_assistant.get("usage") or {}}
        if classify_pi_terminal_error(normalized) == "quota_exhausted":
            # Only the fixed allowlist crosses the boundary; raw provider output is never stored.
            detail["quota_error"] = normalized
        return "failure", detail
    return "success", {"model": target_id, "usage": last_assistant.get("usage") or {}}


def _run_app_cli(args, env=None, timeout=60, cwd=ROOT):
    """An `env` entry whose value is None UNSETS that variable in the child.

    027 isolation follow-up, and the reason this convention exists at all. The lifecycle
    contract (ADR-0008 D5, restated in `route_and_spawn`'s own opening comment) is "the
    routing CLI discovers PROJECT_ROOT from its cwd" -- but this function hands the child a
    copy of `os.environ`, and `resolve_project_root` (project_identity.py:56) ranks an
    inherited `SET_AGENTS_PROJECT` ABOVE that cwd walk-up. `set_agents_app.main()` exports
    exactly that variable into its own process (set_agents_app.py:4141), so any orchestrator
    that ran a routing command in-process -- or any shell that merely exported the variable
    -- silently re-anchored EVERY child of every later spawn to its own project, and the
    persisted `dispatches.project_key` attributed the user's work to the wrong project. That
    is precisely the corruption ADR-0008's "minimal change" was introduced to prevent.

    Expressing the removal through the EXISTING `env` parameter, rather than a new keyword,
    is deliberate: `_run_app_cli` is mocked by name across several test modules whose fakes
    declare exactly `(args, env=None, timeout=60, cwd=None)`, so a new call-site keyword is
    a TypeError in every one of them (measured: tests/test_pi_effort.py). `env` is a channel
    they already accept and ignore. Only the CHILD's copy is touched; this process's own
    `os.environ` is never mutated.
    """
    full_env = dict(os.environ)
    for key, value in (env or {}).items():
        if value is None:
            full_env.pop(key, None)
        else:
            full_env[key] = value
    return subprocess.run([sys.executable, str(APP_CLI), *args], cwd=cwd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          timeout=timeout, check=False, env=full_env)


def _last_json_line(text):
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return {}
    try:
        return json.loads(lines[-1])
    except ValueError:
        return {}


def route_and_spawn(role, task_class, task, *, risk=None, review_of_run_id=None, feature_id=None,
                    package_id=None, routing_test_root=None, spawn_cwd=None, prompt_root=None):
    """Full T-303 lifecycle over the CLI: `--route-decide` -> (writer authorized) ->
    `--route-dispatched` -> guarded pi spawn -> `--route-terminal`. Never raises for a
    routing or child failure — the returned dict IS the tool result contract (AC-11's
    refusal path: a non-executable decision never spawns a session, the refusal reason
    is reported here instead).

    SEC-A02 (repair R1): this, the routed lifecycle entry point, ALWAYS spawns with
    `GUARD_TOOLS_READONLY` — there is deliberately no `guard_tools` parameter here (unlike
    the low-level `spawn()` primitive), so a code-rw child is never reachable through this
    function or through `main()`'s CLI, which calls it with no override of any kind.

    SEC-A03/PKG-N01 (repair R1): once `--route-decide` has authorized a run (`run_id` is
    live), every following step — dispatch, spawn, and the terminal close itself — runs
    inside one guarded block. ANY exception in that block (a `_run_app_cli` subprocess
    surprise like `TimeoutExpired`/`OSError`, or anything else) is caught and answered
    with a best-effort `--route-terminal <run_id> failure` call of its own (itself
    wrapped so it can never raise back out) before returning a `failure` result — an
    authorized run is never left open just because the orchestration code around it
    misbehaved.
    """
    # The routing CLI discovers PROJECT_ROOT from its cwd. Keep this separate from
    # Pi's execution cwd: the latter intentionally retains the caller's exact value.
    routing_cwd = Path(spawn_cwd).resolve() if spawn_cwd is not None else Path.cwd().resolve()
    descriptor = {"role": role, "task_class": task_class, "selected_runtime": "pi"}
    if risk:
        descriptor["risk"] = risk
    if review_of_run_id:
        descriptor["review_of_run_id"] = review_of_run_id
    if feature_id:
        descriptor["feature_id"] = feature_id
    if package_id:
        descriptor["package_id"] = package_id
    env = {"SET_AGENTS_ROUTING_TEST_ROOT": routing_test_root} if routing_test_root else {}
    if spawn_cwd is not None:
        # An explicit spawn target is this lane's analogue of `--project`: the most specific
        # signal there is, so it must outrank an inherited `SET_AGENTS_PROJECT`, which would
        # otherwise beat the cwd walk-up (project_identity.py:56) and re-anchor the whole
        # lifecycle to whatever project the ORCHESTRATOR happens to sit in. None == unset in
        # the child (see `_run_app_cli`). With no explicit spawn target the variable is left
        # alone, so ADR-0008's documented precedence (`--project` > env > walk-up) still
        # holds for a plain ambient run -- this narrows nothing that was ever intentional.
        env["SET_AGENTS_PROJECT"] = None
    # One kwargs bundle for all SIX lifecycle CLI calls (decide, dispatched, both terminal
    # closes, the quota replacement close, and the best-effort close in the except block).
    # Bundling is structural, not cosmetic: the child's project scoping MUST be identical
    # across every call of one run -- a close that resolved a different PROJECT_ROOT than
    # its own decide would write the terminal state into another project's routing store.
    # Sharing one dict makes forgetting a call site impossible.
    cli_kwargs = {"env": env, "cwd": routing_cwd}
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    try:
        json.dump(descriptor, handle)
        descriptor_path = handle.name
    finally:
        handle.close()
    try:
        decide = _run_app_cli(["--route-decide", descriptor_path, "--json"], **cli_kwargs)
    finally:
        try:
            os.unlink(descriptor_path)
        except OSError:
            pass
    envelope = _last_json_line(decide.stdout)
    data = envelope.get("data") if isinstance(envelope.get("data"), dict) else {}
    if not envelope.get("ok") or not data.get("execution_enabled"):
        # AC-11 refusal path: no session, ever, for a non-executable decision.
        return {"status": "refused", "reason_codes": envelope.get("reason_codes", []),
               "decide_exit_code": decide.returncode}
    run_id, provider, model = data.get("run_id"), data.get("provider"), data.get("model")
    # ADR-0056 (AC-12): fetched before the routing store's own dispatch call -- a
    # vault-fetch timeout/crash never burns the one-use `single_writer` authorization the
    # `--route-decide` call above already produced.
    vault_block = _fetch_vault_block(routing_cwd, routing_test_root=routing_test_root)
    try:
        dispatched = _run_app_cli(["--route-dispatched", run_id, "--json"], **cli_kwargs)
        if dispatched.returncode != 0:
            _run_app_cli(["--route-terminal", run_id, "failure", "--json"], **cli_kwargs)
            return {"status": "failure", "run_id": run_id, "reason": "DISPATCH_FAILED"}
        started = time.time()
        role_prompt = (Path(prompt_root) if prompt_root else CANON_AGENTS) / f"{role}.md"
        # SEC-A02: always the read-only tier; this routed path never accepts an override.
        # ADR-0030: the decision's effort rides along as pi's --thinking level (validated
        # against the closed set inside spawn(); absent/unknown just omits the flag).
        outcome, detail = spawn(role, task, provider, model, role_prompt,
                                guard_tools=GUARD_TOOLS_READONLY, cwd=spawn_cwd, vault_block=vault_block,
                                effort=data.get("effort"))
        latency_ms = max(0, int((time.time() - started) * 1000))
        terminal_outcome = "success" if outcome == "success" else "failure"
        terminal_args = ["--route-terminal", run_id, terminal_outcome, "--latency-ms", str(latency_ms), "--json"]
        # AC-10: attach `--usage` whenever `detail` carries one, regardless of `outcome` —
        # `spawn()` now reports usage for `model_mismatch`/`PI_TURN_ERROR` too (F-PR-02), not
        # only `success`. A genuine `PI_CRASH`/missing-role-prompt/etc. `detail` has no
        # "usage" key at all, so this naturally omits --usage for those, same as the two
        # failure closes below that never reach this line at all.
        #
        # 007-P2 review finding (F-SEC-02, upheld by finding-verifier): `spawn()`'s contract
        # promises `usage` is a dict (`usage or {}`), but nothing enforced it — a
        # non-dict value here would reach `--usage`, which `parse_usage` correctly rejects
        # at the CLI (ROUTING_INPUT_INVALID), but `--usage` and `--route-terminal` are the
        # SAME call, so rejecting the usage rejected the ENTIRE close, leaving the run
        # `dispatched` forever. `isinstance` is checked here, at the one place this argument
        # is composed, so a malformed shape is simply never attached — the run still closes,
        # with `usage_status='absent'` for that one field.
        usage = detail.get("usage")
        if detail.get("quota_error") and classify_pi_terminal_error(detail["quota_error"]) == "quota_exhausted":
            terminal_args = ["--route-quota-exhausted", run_id, "--quota-error", json.dumps(detail["quota_error"]),
                             "--latency-ms", str(latency_ms), "--json"]
        if isinstance(usage, dict):
            terminal_args += ["--usage", json.dumps(usage)]
        terminal = _run_app_cli(terminal_args, **cli_kwargs)
        quota_result = _last_json_line(terminal.stdout).get("data", {}) if detail.get("quota_error") else {}
        replacement_id = quota_result.get("replacement_run_id") if isinstance(quota_result, dict) else None
        replacement_provider = quota_result.get("replacement_provider") if isinstance(quota_result, dict) else None
        replacement_model = quota_result.get("replacement_model") if isinstance(quota_result, dict) else None
        if replacement_id and isinstance(replacement_provider, str) and isinstance(replacement_model, str):
            replacement_outcome, replacement_detail = spawn(role, task, replacement_provider, replacement_model, role_prompt,
                                                             guard_tools=GUARD_TOOLS_READONLY, cwd=spawn_cwd,
                                                             vault_block=vault_block)
            replacement_args = ["--route-terminal", replacement_id,
                                "success" if replacement_outcome == "success" else "failure", "--json"]
            if isinstance(replacement_detail.get("usage"), dict):
                replacement_args += ["--usage", json.dumps(replacement_detail["usage"])]
            replacement_terminal = _run_app_cli(replacement_args, **cli_kwargs)
            detail = dict(detail, replacement_run_id=replacement_id, replacement_status=replacement_outcome,
                          replacement_terminal_exit_code=replacement_terminal.returncode)
    except Exception as exc:  # noqa: BLE001 - SEC-A03/PKG-N01: no orphaned authorized run
        # Any exception past authorization (a lifecycle-CLI subprocess surprise or
        # anything else) must never leave `run_id` open. The best-effort close itself is
        # never allowed to raise back out — if it also fails, the run is simply reported
        # as failure without a durable close; a caller that observes this reason should
        # treat `run_id` as needing a manual audit, but the process here never crashes.
        try:
            _run_app_cli(["--route-terminal", run_id, "failure", "--json"], **cli_kwargs)
        except Exception:  # noqa: BLE001
            pass
        return {"status": "failure", "run_id": run_id, "reason": "ORCHESTRATION_EXCEPTION",
               "detail": _redact(str(exc))[:500]}
    return {
        "status": outcome, "run_id": run_id, "provider": provider, "model": model,
        "detail": detail, "terminal_exit_code": terminal.returncode,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--role")
    parser.add_argument("--task-class")
    parser.add_argument("--task")
    parser.add_argument("--risk")
    parser.add_argument("--review-of-run-id")
    parser.add_argument("--feature-id")
    parser.add_argument("--package-id")
    args = parser.parse_args()
    if args.doctor:
        print(json.dumps(doctor(), sort_keys=True))
        return 0
    if not (args.role and args.task_class and args.task):
        parser.error("--role/--task-class/--task are required unless --doctor")
    result = route_and_spawn(args.role, args.task_class, args.task, risk=args.risk,
                             review_of_run_id=args.review_of_run_id, feature_id=args.feature_id,
                             package_id=args.package_id)
    print(json.dumps(result, sort_keys=True, default=str))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
