"""set-agents: routing decision helpers with NO dependency on the mutable, per-invocation
routing store (`_routing_store`) -- extracted from set_agents_app.py (mechanical,
behavior-preserving split).

Deliberately NOT moved here (stay in set_agents_app.py, documented deviation): every routing
command that needs `_routing_store()` (`routing_catalog`, `cmd_route_explain`,
`cmd_routing_report`, `cmd_route_decide`, `_lifecycle_command`, `cmd_route_dispatched`,
`cmd_route_quota_exhausted`, `cmd_route_terminal`, `cmd_routing_open_runs`,
`cmd_routing_recent_writers`, `cmd_routing_migrate`, `cmd_doctor`) and `_routing_output`
(reads the mutable `ROUTING_WARNINGS` global that only `main()` reassigns). `_routing_store`
itself reads the mutable `PROJECT_KEY` global that only `set_agents_app.main()` ever
reassigns (via `global PROJECT_KEY`) -- residue anchors are enumerated in
`docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-residue-matrix.md`, and
`tests/test_harness.py:788-796` registers `set_agents_app` only for `exec_module` then
restores `sys.modules` afterward (correcting the stale claim that `_import()` leaves it
unregistered). This module only
holds the functions tests/test_routing.py calls directly against the plain, cached
`set_agents_app` module (`parse_usage`, `_decide_status`, `_validate_context_pack_path`,
`_resolve_context_pack`, `_load_feature_doc`) plus their own small, self-contained helpers --
none of which ever needs `_routing_store`/`_routing_output`.

`_project_root_or_harness` (needed by `_validate_context_pack_path`/`_resolve_context_pack`)
stays in set_agents_app.py too (hard requirement -- it resolves the mutable `PROJECT_ROOT`/
`ROOT` globals against ITS OWN `__globals__`, which must be set_agents_app.py's). It is
reached here via a CALL-TIME (lazy, inside the function body) `import set_agents_app`, never
a module-level one: tests/test_routing.py always reaches these functions through a plain,
already-registered `import set_agents_app`, so the lazy lookup finds the real, live module
correctly. `_MAX_FEATURE_BYTES`/`_MAX_FEATURE_FILES` are duplicated here (identical values,
never monkeypatched by any test) rather than imported back, for the same reason.
"""

import decimal
import json
import os
import re
import stat
from datetime import datetime

from project_identity import _real_directory, _safe_read

_MAX_FEATURE_BYTES = 1024 * 1024
_MAX_FEATURE_FILES = 256

_SAFE_STATE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
# F03: a feature phase or package status this terminal never has an "active" context pack —
# naming it explicitly can never flip CONTEXT_MISSING, and it is never chosen by default
# resolution either.
_TERMINAL_FEATURE_PHASES = {"DONE", "BLOCKED", None}
_TERMINAL_PACKAGE_STATUS = {"accepted", "done", "blocked", "cancelled"}

# F01: the ONLY two "non-executable but still ok=true" shapes a decision can take — a
# non-executable decision for a non-writer, non-review role class, and the explicit,
# doctrine-named REVIEW_IDENTITY_UNVERIFIED reviewer report. Every other non-executable
# decision (FACTS_INCOMPLETE, NO_ELIGIBLE_ROUTE, REVIEW_IDENTITY_INVALID,
# PROVIDER_UNAUTHENTICATED, REVIEWER_INDEPENDENCE_UNAVAILABLE, AUTHORIZATION_INVALID,
# AUTHORIZATION_REPLAY, CATALOG_INVALID, STATE_CONFLICT, ROUTING_UNAVAILABLE, ...) is a
# real failure: ok=false, exit 1. Centralized so P3's Pi lane inherits the same table.
_DECIDE_OK_NON_EXECUTABLE_REASONS = ((), ("REVIEW_IDENTITY_UNVERIFIED",))

_MAX_USAGE_TEXT_LEN = 1024 * 1024


def _role_class_of(row):
    if row["capability"] == "code-rw": return "writer"
    if row["capability"] == "review-ro" and row["duty"] in {"audit", "judge"}: return "review"
    return "other"


def _decide_status(decision):
    """(ok, exit_code) for a `route-decide` RouteDecision — the reason->exit table (F01).

    P2F-01: `RUNTIME_REDIRECTED requested=X effective=Y` is informational only (AC-09,
    non-blocking runtime redirection) and never participates in the ok/exit classification.
    It is filtered out of the reason codes before the closed-table membership check below,
    so a redirect-only decision still matches `()` and a redirect alongside
    REVIEW_IDENTITY_UNVERIFIED still matches that single-element tuple — both exactly as
    before this code existed. ADR-0035 (AC-14): `BILLING_RANK provider=X rank=N` is the same
    kind of purely-observational, always-present marker (never a failure signal on its own,
    per the ADR's own "never changes success/runtime/identity/fallback") — filtered out here
    the same way, so a decision that would have been ok=true/executable before this ADR stays
    exactly that after it. D-5/AC-07 (027 PKG-3): `MODEL_PINNED provider/model` (ADR-0032)
    and the two NAMED `MODEL_REQUEST_*` codes — `MODEL_REQUEST_APPLIED provider/model`
    and `MODEL_REQUEST_UNAVAILABLE requested=provider/model reason=...` (026/P2 AC-06) —
    are the same purely-additive, always-informational shape — service.py never lets any
    of them change success/runtime/identity/fallback, so they are filtered here too. Each
    is matched by its full name plus a trailing space, never by the bare `MODEL_REQUEST_`
    family prefix (P3-F01 repair, 027 PKG-3 repair round 1): the family prefix would also
    auto-classify any future/unknown `MODEL_REQUEST_*` code as informational, which is
    exactly the fail-open failure mode `test_decide_status_helper_matrix` now pins down —
    see its `MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE` case. Deliberately NOT
    `MODEL_PIN_UNAVAILABLE`: this is a known, measured gap, not a semantic claim that it is
    "purely additive" (service.py:503-509 says otherwise for its own name). Filtering it
    is out of AC-07's approved scope (spec.md D-5 names only MODEL_PINNED and the two named
    MODEL_REQUEST_* codes) — the orchestrator recorded the gap with `log-decision`
    (P3-F02 repair, 027 PKG-3 repair round 1) rather than widening this AC unreviewed. It
    keeps participating in the closed reason table unfiltered. Every other (hard-failure)
    reason code is untouched.
    """
    codes = tuple(code for code in decision.reason_codes
                  if not code.startswith("RUNTIME_REDIRECTED")
                  and not code.startswith("BILLING_RANK ")
                  and not code.startswith("MODEL_PINNED ")
                  and not code.startswith("MODEL_REQUEST_APPLIED ")
                  and not code.startswith("MODEL_REQUEST_UNAVAILABLE "))
    if decision.execution_enabled or codes in _DECIDE_OK_NON_EXECUTABLE_REASONS:
        return True, 0
    return False, 1


def _load_feature_doc(path):
    raw = _safe_read(path, limit=_MAX_FEATURE_BYTES)
    try:
        doc = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(doc, dict):
        return None
    # Only this small structural subset is consumed.  Rejecting a malformed
    # document up-front keeps every later traversal total and data-only.
    if not isinstance(doc.get("packages", []), list):
        return None
    if any(not isinstance(package, dict) for package in doc["packages"]):
        return None
    return doc


def _safe_state_id(value):
    return value if isinstance(value, str) and len(value) <= 64 and _SAFE_STATE_ID.fullmatch(value) else None


def _validate_context_pack_path(pack):
    """SEC-A02: a foreign/malformed feature-state.json must never crash route-decide nor
    escape the project. Project content is untrusted data, never instructions. Non-str, empty, absolute, or traversal-outside-PROJECT_ROOT all degrade to 'no
    pack' — never a bare `ROOT / pack` (an absolute right-hand side silently DISCARDS ROOT
    under pathlib's own semantics, which would let a crafted state file probe arbitrary
    filesystem paths)."""
    if not isinstance(pack, str) or not pack or os.path.isabs(pack):
        return None
    import set_agents_app  # lazy: see module docstring
    root = set_agents_app._project_root_or_harness().resolve()
    candidate = (root / pack).resolve()
    try:
        if os.path.commonpath([str(candidate), str(root)]) != str(root):
            return None
    except ValueError:
        return None
    return candidate


def _package_context_ok(doc, package_id):
    """Existence AND freshness (F03b): a pack older than the package's own last recorded
    mutation (falling back to the feature doc's) is stale and reports False, conservatively."""
    if not isinstance(doc, dict) or not isinstance(doc.get("packages", []), list):
        return False
    for package in doc["packages"]:
        if not isinstance(package, dict):
            return False
        if package.get("package_id") != package_id:
            continue
        path = _validate_context_pack_path(package.get("context_pack"))
        if path is None:
            return False
        try:
            st = path.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            return False
        reference = package.get("updated_at") or doc.get("updated_at")
        if isinstance(reference, str):
            try:
                ref_epoch = datetime.fromisoformat(reference).timestamp()
            except ValueError:
                ref_epoch = None
            if ref_epoch is not None and st.st_mtime < ref_epoch:
                return False  # stale: the pack predates the package's last recorded mutation
        return True
    return False


def _resolve_context_pack(feature_id, package_id):
    """AM-1/F03: context flags derive from the active package's context pack — EXISTENCE AND
    FRESHNESS, never presence alone. Returns `(context_ok, feature_id, package_id)`:
    `context_ok` is True/False once a package is identified (pack good, or missing/stale/the
    feature or package is terminal), or None when the package itself could not even be
    resolved (CONTEXT_UNRESOLVED at the caller — distinct from a resolved-but-missing pack,
    contract 004 AC-03's "no resolvable package ⇒ context flags false" applies to the
    EXPLICIT-id case; the ambiguous DEFAULT case is a distinct signal).
    """
    import set_agents_app  # lazy: see module docstring
    root = set_agents_app._project_root_or_harness()
    state_dir = root / "ai/state/features"
    if not (_real_directory(root / "ai") and _real_directory(root / "ai/state") and _real_directory(state_dir)):
        return None, None, None
    if feature_id:
        if not _SAFE_STATE_ID.fullmatch(feature_id):
            return False, feature_id, package_id
        # N10: with an explicit feature_id, open ONLY that one file — never glob the directory.
        doc = _load_feature_doc(state_dir / f"{feature_id}.json")
        if doc is None or doc.get("feature_id") != feature_id:
            return False, feature_id, package_id
        target = _safe_state_id(package_id) if package_id else _safe_state_id(doc.get("current_package_id"))
        # F03a: naming a BLOCKED/DONE feature can never flip CONTEXT_MISSING — the same
        # non-terminal filter used by default resolution applies here too. `target` is still
        # resolved above so the audit payload always shows the effective package_id.
        if doc.get("phase") in _TERMINAL_FEATURE_PHASES:
            return False, feature_id, target
        return _package_context_ok(doc, target), feature_id, target
    # No feature_id: resolve the single feature whose CURRENT package is actively executing
    # (package status non-terminal) — "exactly one non-terminal FEATURE" under-resolves
    # whenever more than one feature is mid-flight (e.g. one sitting at PACKAGE_ACCEPTED for
    # its current package while another is still mid-repair).
    candidates = []
    try:
        entries = sorted(state_dir.glob("*.json"))
        if len(entries) > _MAX_FEATURE_FILES:
            return None, None, None
        for candidate_path in entries:
            doc = _load_feature_doc(candidate_path)
            if doc is None or doc.get("phase") in _TERMINAL_FEATURE_PHASES:
                continue
            current = _safe_state_id(doc.get("current_package_id"))
            if current is None:
                continue
            package = next((p for p in doc["packages"] if p.get("package_id") == current), None)
            if package is not None and isinstance(package, dict) and package.get("status") not in _TERMINAL_PACKAGE_STATUS:
                candidates.append((doc, current))
    except OSError:
        return None, None, None
    if len(candidates) != 1:
        return None, None, None  # CONTEXT_UNRESOLVED at the caller, distinct from NO_ELIGIBLE_ROUTE
    doc, target = candidates[0]
    return _package_context_ok(doc, target), _safe_state_id(doc.get("feature_id")), target


def parse_usage(text):
    """AC-13: local, not imported across scripts. `feature-state.py:parse_json_object` is
    not the model to copy: it raises `StateError`, a `RuntimeError` subclass, and
    `_lifecycle_command` does not catch `RuntimeError` -- a bare copy would leak a
    traceback and break the one-JSON-line contract. The model is `cmd_route_decide`'s idiom
    instead: a bare `ValueError` as a control-flow signal, one flat `except` at the caller.

    AC-11: malformed means unparseable -- not JSON, or JSON that is not an object. Nothing
    else is checked here. There is no closed key whitelist like `cmd_route_decide`'s,
    because AC-12 requires accepting shapes this harness cannot map; that edge is the
    store's job (`routing_core.store._usage_row`), not the CLI's.

    `parse_float=decimal.Decimal` keeps `cost.total` as the exact decimal text the provider
    wrote, which is what makes AC-12's round-half-up rule well-defined at all.

    007-P2 review finding (F-SEC-03, upheld by finding-verifier): a deeply nested JSON
    array (`"[[[...]]]"`) drives CPython's recursive `json` decoder into `RecursionError`,
    which the original `except` did not list -- a raw traceback instead of
    `ROUTING_INPUT_INVALID`, breaking the one-JSON-line contract this function exists to
    protect. Measured: ~55k levels of nesting (~110KB of text) is enough to trigger it.
    Not reachable from a real Pi spawn (nothing this deep ever appears in a `usage`
    object), but reachable from any direct CLI invocation.

    007-P2 delta-review finding (N-01): a length ceiling shared between "malformed" and
    "merely large" reopens the invariant F-SEC-02 closed for a different reason --
    `route_and_spawn` attaches `--usage` whenever it is a dict, `--usage` and
    `--route-terminal` are the SAME call, and a ceiling low enough to matter for a real
    (if verbose) provider payload leaves a legitimate run "dispatched" forever. The
    ceiling below is sized to bound worst-case parse cost (a `~1MiB` JSON parse is cheap
    regardless of shape), not to sit close to any real `usage` object -- the one live Pi
    sample this package has ever measured is ~90 bytes. It is still comfortably above the
    ~110KB needed to trigger `RecursionError` by nesting, so that `except` clause is
    load-bearing here, not dead code shadowed by the length check.
    """
    if len(text) > _MAX_USAGE_TEXT_LEN:
        raise ValueError
    try:
        doc = json.loads(text, parse_float=decimal.Decimal)
    except (json.JSONDecodeError, ValueError, TypeError, RecursionError):
        raise ValueError
    if not isinstance(doc, dict):
        raise ValueError
    return doc
