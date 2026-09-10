"""Read-only, privacy-bounded model state for the primary SET runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import subprocess
import threading
import time
import tomllib

OUTPUT_BUDGET = 1024 * 1024


class ModelStateReason(str, Enum):
    NOT_CHECKED = "not_checked"
    UNSUPPORTED_RUNTIME = "unsupported_runtime"
    OPENCODE_ABSENT = "opencode_absent"
    PROJECT_UNRESOLVED = "project_unresolved"
    TIMEOUT = "timeout"
    INVALID_JSON = "invalid_json"
    OUTPUT_LIMIT = "output_limit"
    SESSION_LIMIT = "session_limit"
    NO_PROJECT_ROOT = "no_project_root"
    NO_SUBMITTED_MESSAGE = "no_submitted_message"
    CACHE_READ_FAILED = "cache_read_failed"
    PROBE_FAILED = "probe_failed"
    CHILD_FAILED = "child_failed"
    NOT_INSTALLED = "not_installed"
    UNAVAILABLE = "unavailable"


def _refresh():
    return {"status": "unavailable", "checked_at": None, "reason": ModelStateReason.NOT_CHECKED.value}


def empty_state(runtime="unavailable"):
    unavailable = ModelStateReason.UNAVAILABLE.value
    return {
        "schema_version": 1, "scope": {"runtime": runtime, "role": "orchestrator"},
        "observed": {"status": "unobserved", "source": "unavailable", "model": None, "observed_at": None, "reason": unavailable},
        "desired": {"status": "unavailable", "source": "unavailable", "model": None, "reason": unavailable},
        "installed": {"status": "absent", "source": "unavailable", "model": None, "reason": unavailable},
        "routing": {"status": "unavailable", "source": "unavailable", "reason": unavailable},
        "convergence": {"status": "unknown"},
        "refresh": {key: _refresh() for key in ("observed", "desired", "installed", "routing")},
    }


def _unobserved(reason):
    return {"status": "unobserved", "source": "unavailable", "model": None, "observed_at": None, "reason": reason.value}


def _epoch_rfc3339(value):
    """Only OpenCode v1 numeric millisecond epochs are accepted."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return None


def _bounded_child(command, cwd, timeout, budget):
    """Capture both child pipes incrementally, terminate/reap on budget exhaustion."""
    try:
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return "absent", b"", 0
    except OSError:
        return "failed", b"", 0
    lock, stopped, output = threading.Lock(), threading.Event(), bytearray()
    total, limited = [0], [False]

    def consume(stream, retain):
        try:
            while chunk := stream.read(65536):
                with lock:
                    if total[0] + len(chunk) > budget:
                        limited[0] = True
                        stopped.set()
                    else:
                        total[0] += len(chunk)
                        if retain:
                            output.extend(chunk)
                if stopped.is_set():
                    try:
                        process.terminate()
                    except OSError:
                        pass
        finally:
            try:
                stream.close()
            except OSError:
                pass

    threads = [threading.Thread(target=consume, args=(process.stdout, True), daemon=True),
               threading.Thread(target=consume, args=(process.stderr, False), daemon=True)]
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=timeout)
        result = "limited" if limited[0] else ("ok" if process.returncode == 0 else "failed")
    except subprocess.TimeoutExpired:
        try:
            process.terminate()
            process.wait(timeout=0.2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=0.2)
            except (OSError, subprocess.TimeoutExpired):
                pass
        result = "timeout"
    for thread in threads:
        thread.join(timeout=0.2)
    return ("limited" if result == "ok" and limited[0] else result), bytes(output), total[0]


def _runner_child(runner, command, cwd, timeout, budget):
    """Compatibility seam for hermetic tests; production uses bounded Popen."""
    result = runner(command, cwd=cwd, timeout=timeout)
    if not isinstance(result, tuple) or len(result) not in (2, 3):
        raise ValueError
    code, stdout = result[:2]
    stderr = result[2] if len(result) == 3 else ""
    if not isinstance(code, int) or not isinstance(stdout, str) or not isinstance(stderr, str):
        raise ValueError
    size = len(stdout.encode("utf-8")) + len(stderr.encode("utf-8"))
    if size > budget:
        return "limited", b"", size
    return ("ok" if code == 0 else "failed"), stdout.encode("utf-8"), size


def observe_opencode(project: Path | None, *, runtime: str, runner=None, deadline=5.0):
    """Observe exactly one official OpenCode 1.18.14 root, retaining allow-listed fields only."""
    if runtime != "opencode":
        return _unobserved(ModelStateReason.UNSUPPORTED_RUNTIME)
    if project is None:
        return _unobserved(ModelStateReason.PROJECT_UNRESOLVED)
    try:
        canonical_project = Path(project).resolve()
    except OSError:
        return _unobserved(ModelStateReason.PROJECT_UNRESOLVED)
    started, used = time.monotonic(), [0]

    def invoke(command):
        remaining = deadline - (time.monotonic() - started)
        if remaining <= 0:
            return "timeout", b""
        try:
            call = _runner_child if runner is not None else _bounded_child
            args = (runner, command, str(canonical_project), remaining, OUTPUT_BUDGET - used[0]) if runner is not None else (command, str(canonical_project), remaining, OUTPUT_BUDGET - used[0])
            status, output, size = call(*args)
        except FileNotFoundError:
            return "absent", b""
        except subprocess.TimeoutExpired:
            return "timeout", b""
        except (PermissionError, OSError):
            return "failed", b""
        except (TypeError, ValueError, UnicodeError):
            return "invalid", b""
        used[0] += size
        return status, output

    reason_for = {"absent": ModelStateReason.OPENCODE_ABSENT, "failed": ModelStateReason.CHILD_FAILED,
                  "timeout": ModelStateReason.TIMEOUT, "limited": ModelStateReason.OUTPUT_LIMIT,
                  "invalid": ModelStateReason.INVALID_JSON}
    status, raw = invoke(["opencode", "session", "list", "--format", "json", "--pure"])
    if status != "ok":
        return _unobserved(reason_for[status])
    try:
        sessions = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return _unobserved(ModelStateReason.INVALID_JSON)
    if not isinstance(sessions, list):
        return _unobserved(ModelStateReason.INVALID_JSON)
    roots = []
    for session in sessions:
        if not isinstance(session, dict) or session.get("parentID") is not None:
            continue
        timing = session.get("time")
        session_id, directory = session.get("id"), session.get("directory")
        updated = timing.get("updated") if isinstance(timing, dict) else None
        if not isinstance(session_id, str) or not session_id or not isinstance(directory, str) or not directory or _epoch_rfc3339(updated) is None:
            return _unobserved(ModelStateReason.INVALID_JSON)
        try:
            if Path(directory).resolve() == canonical_project:
                roots.append((updated, session_id))
        except OSError:
            return _unobserved(ModelStateReason.PROJECT_UNRESOLVED)
    if len(roots) > 20:
        return _unobserved(ModelStateReason.SESSION_LIMIT)
    if not roots:
        return _unobserved(ModelStateReason.NO_PROJECT_ROOT)
    _, selected_id = max(roots, key=lambda item: (item[0], item[1]))
    if used[0] >= OUTPUT_BUDGET:
        return _unobserved(ModelStateReason.OUTPUT_LIMIT)
    status, raw = invoke(["opencode", "export", "--sanitize", "--pure", selected_id])
    if status != "ok":
        return _unobserved(reason_for[status])
    try:
        exported = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return _unobserved(ModelStateReason.INVALID_JSON)
    messages = exported.get("messages") if isinstance(exported, dict) else None
    if not isinstance(messages, list):
        return _unobserved(ModelStateReason.INVALID_JSON)
    candidates = []
    for message in messages:
        info = message.get("info") if isinstance(message, dict) else None
        if not isinstance(info, dict) or info.get("role") != "user":
            continue
        message_id, timing, model = info.get("id"), info.get("time"), info.get("model")
        created = timing.get("created") if isinstance(timing, dict) else None
        provider = model.get("providerID") if isinstance(model, dict) else None
        model_id = model.get("modelID") if isinstance(model, dict) else None
        timestamp = _epoch_rfc3339(created)
        if not isinstance(message_id, str) or not message_id or not isinstance(provider, str) or not provider or not isinstance(model_id, str) or not model_id or timestamp is None:
            return _unobserved(ModelStateReason.INVALID_JSON)
        candidates.append((created, message_id, timestamp, provider + "/" + model_id))
    if not candidates:
        return _unobserved(ModelStateReason.NO_SUBMITTED_MESSAGE)
    _, _, timestamp, model = max(candidates, key=lambda item: (item[0], item[1]))
    return {"status": "observed", "source": "opencode-sanitized-export", "model": model, "observed_at": timestamp, "reason": None}


_RUNTIME_FIELD = {"opencode": "opencode", "codex": "codex", "claude-code": "claude", "cursor": "cursor"}


def _resolved_or_unavailable(model):
    if not isinstance(model, str) or not model:
        return {"status": "unavailable", "source": "unavailable", "model": None, "reason": ModelStateReason.UNAVAILABLE.value}
    return {"status": "resolved", "source": "set-effective-config", "model": model, "reason": None}


def desired_state(config, row, runtime):
    field = _RUNTIME_FIELD.get(runtime)
    if field is None:
        return {"status": "unavailable", "source": "unavailable", "model": None, "reason": ModelStateReason.UNSUPPORTED_RUNTIME.value}
    try:
        model = config.get("roles", {}).get(row["role"], {}).get(field, config["areas"][row["duty"]].get(field))
    except (KeyError, TypeError):
        model = None
    return _resolved_or_unavailable(model)


def _desired_from_resolved(resolved, runtime):
    field = {"opencode": "opencode_model", "codex": "codex_model", "claude-code": "claude_model", "cursor": "cursor_model"}.get(runtime)
    return _resolved_or_unavailable(resolved.get(field) if field else None)


def _installed_path(runtime, home):
    home = Path(home)
    return {"opencode": (home / ".config/opencode/agents/orchestrator.md", "frontmatter"),
            "codex": (home / ".codex/agents/orchestrator.toml", "toml"),
            "claude-code": (home / ".claude/agents/orchestrator.md", "frontmatter"),
            "cursor": (home / ".cursor/agents/orchestrator.md", "frontmatter")}.get(runtime)


def _frontmatter_model(raw):
    if not raw.startswith("---\n"):
        return None
    end = raw.find("\n---", 4)
    if end < 0:
        return None
    for line in raw[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "model":
            return value.strip() or None
    return None


def installed_state(runtime, home):
    target = _installed_path(runtime, home)
    if target is None:
        return {"status": "absent", "source": "unavailable", "model": None, "reason": ModelStateReason.UNSUPPORTED_RUNTIME.value}
    path, kind = target
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"status": "absent", "source": "installed-role-artifact", "model": None, "reason": ModelStateReason.NOT_INSTALLED.value}
    except OSError:
        return {"status": "unreadable", "source": "installed-role-artifact", "model": None, "reason": ModelStateReason.UNAVAILABLE.value}
    try:
        model = tomllib.loads(raw).get("model") if kind == "toml" else _frontmatter_model(raw)
    except tomllib.TOMLDecodeError:
        return {"status": "unreadable", "source": "installed-role-artifact", "model": None, "reason": ModelStateReason.INVALID_JSON.value}
    if not isinstance(model, str) or not model:
        return {"status": "absent", "source": "installed-role-artifact", "model": None, "reason": ModelStateReason.UNAVAILABLE.value}
    return {"status": "installed", "source": "installed-role-artifact", "model": model, "reason": None}


def routing_state(path):
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"status": "dynamic", "source": "model-preference.toml", "reason": None}
    except OSError:
        return {"status": "unavailable", "source": "unavailable", "reason": ModelStateReason.UNAVAILABLE.value}
    try:
        pins = tomllib.loads(raw).get("model_pin", {})
    except tomllib.TOMLDecodeError:
        return {"status": "unavailable", "source": "model-preference.toml", "reason": ModelStateReason.INVALID_JSON.value}
    return {"status": "pinned" if ("orchestrator" in pins or "*" in pins) else "dynamic", "source": "model-preference.toml", "reason": None}


def _checked(evidence):
    return {"status": "fresh" if evidence.get("reason") is None else "error",
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "reason": evidence.get("reason")}


def collect_model_state(root, *, home=None, project=None, runner=None):
    import models_config
    root, home = Path(root), (Path.home() if home is None else Path(home))
    try:
        factory = models_config.load_config(root / "models.toml")
        effective = models_config.effective_models_config(factory, models_config.load_models_overlay(home / ".local/state/set-agentes/models.local.toml"))
        runtime = effective["runtime"]["primary"]
        row = next(item for item in models_config.load_roster(root / "roles.tsv") if item["role"] == "orchestrator")
        desired = _desired_from_resolved(models_config.resolve_role(row, effective), runtime)
    except (OSError, ValueError, KeyError, StopIteration, tomllib.TOMLDecodeError):
        runtime, desired = "unavailable", _resolved_or_unavailable(None)
    observed, installed = observe_opencode(project, runtime=runtime, runner=runner), installed_state(runtime, home)
    routing = routing_state(home / ".local/state/set-agentes/model-preference.toml")
    state = empty_state(runtime)
    state.update({"observed": observed, "desired": desired, "installed": installed, "routing": routing})
    state["refresh"] = {key: _checked(state[key]) for key in ("observed", "desired", "installed", "routing")}
    if desired["status"] == "resolved":
        state["convergence"] = {"status": "applied" if installed.get("model") == desired.get("model") and installed["status"] == "installed" else "pending_apply"}
    return state


def _safe_human(value):
    return "".join(ch if 32 <= ord(ch) <= 126 or ord(ch) >= 160 else f"\\x{ord(ch):02x}" for ch in str(value))


def render_human(state):
    lines = ["Estado de modelos (último envío observado; no es el modelo actual)"]
    for key, label in (("observed", "Último envío observado"), ("desired", "Default de SET"), ("installed", "Instalado"), ("routing", "Routing")):
        evidence = state[key]
        value = evidence.get("model") or evidence["status"]
        reason = f" ({_safe_human(evidence['reason'])})" if evidence.get("reason") else ""
        lines.append(f"{label}: {_safe_human(value)}{reason}")
    return "\n".join(lines)
