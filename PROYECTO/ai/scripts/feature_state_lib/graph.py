"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from feature_state_lib.model import StateError
from feature_state_lib.render_notes import _short, _note_packages, _normalize_note_state


# --------------------------------------------------------------------------- P3-graph-view
#
# AC-20..AC-27, AC-29: the execution graph is derived in READ from the state files that
# already exist -- no new store, no materialized index (see ADR-0013). `build_execution_graph`
# walks one or more `ai/state/features/<fid>.json` files and produces nodes/edges by
# STRUCTURAL join only (membership in a list, an id matching another record's id) -- never
# by timestamp proximity, even when two entries share a timestamp by construction.
# `render_mermaid` is the one place that turns that graph into text; both `graph` (AC-22)
# and `render_notes` (AC-24) call the same two functions, never a second copy of either.

GRAPH_NODE_TYPES = ("feature", "package", "finding", "review", "verification", "repair", "commit", "blocker",
                    "spawn")
# The closed, five-member edge vocabulary this feature promises. Spanish on purpose --
# these are the verbs the spec and the ADR name, and inventing an English pair for the
# same concept would just be a second vocabulary nobody asked for.
GRAPH_EDGE_TYPES = ("produjo", "verificó", "refutó", "reparó", "bloqueó")
# Mermaid keywords a bare (unquoted) id can never collide with. Checked in lowercase
# because `_norm()` already lowercases every id this module mints.
MERMAID_RESERVED_WORDS = frozenset({"end", "graph", "subgraph", "o", "x"})


def _norm(text: Any) -> str:
    """AC-22's `norm()`: lowercase, then every character outside [a-z0-9] becomes `_`."""
    return re.sub(r"[^a-z0-9]", "_", str(text if text is not None else "").lower())


# SEC-001/PR-04: mermaid has NO backslash-escape mechanism inside a quoted label -- a
# `"` "escaped" with a leading backslash still closes the string exactly as if the
# backslash were not there (the previous implementation of this function relied on a
# Python/JS-only convention mermaid never implements, which let a crafted label break
# out of its `["..."]`/`subgraph ...["..."]` quotes and inject arbitrary mermaid text,
# including `click` directives, into a committed, rendered document). Mermaid's actual
# escape mechanism is HTML entities.
_MERMAID_ESCAPE_MAP = {
    "#": "#35;",
    '"': "#quot;",
    "\\": "#92;",
    "[": "#91;",
    "]": "#93;",
    "(": "#40;",
    ")": "#41;",
    "<": "#60;",
    ">": "#62;",
    "%": "#37;",
    ";": "#59;",
    "|": "#124;",
}
# A SINGLE pass over the ORIGINAL text, substituting every matched character for its
# entity via a callback -- `re.sub` never re-scans the replacement text it just
# produced. Every entity above contains `#` and/or `;`, both themselves in the escape
# table; a sequence of independent `str.replace()` calls (the first cut of this fix)
# re-escaped the `;`/`#` an EARLIER replacement in the same pass had just inserted,
# corrupting labels containing more than one escaped character. One pass closes that.
_MERMAID_ESCAPE_RE = re.compile("[" + re.escape("".join(_MERMAID_ESCAPE_MAP)) + "]")


def _mermaid_escape(text: Any) -> str:
    """Escape a value for a quoted mermaid label using mermaid's OWN escape mechanism
    (HTML entities), never backslashes. `_short()` runs first -- the same truncation
    every other agent-authored field rendered into a generated document gets, and its
    whitespace collapse also removes newlines before the entity table below ever sees
    them, so a label can never smuggle a real line break into the document either.
    """
    value = _short(text)
    return _MERMAID_ESCAPE_RE.sub(lambda m: _MERMAID_ESCAPE_MAP[m.group(0)], value)


class _GraphState:
    """Accumulates nodes/edges and their feature/package grouping while
    `build_execution_graph` walks one or more state files. One small object instead of a
    handful of dicts threaded by hand through every join helper below.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, str]] = {}       # node_id -> {"type": ..., "label": ...}
        self.edges: list[tuple[str, str, str]] = []       # (src_id, dst_id, edge_label)
        self._counters: dict[tuple[str, str, str | None], int] = {}
        self.feature_order: list[str] = []
        # feature_id -> {"members": [node_id, ...] (feature-scoped only),
        #                "packages": {package_id: {"members": [node_id, ...], "order": int}}}
        self.features: dict[str, dict[str, Any]] = {}
        # PR-03: `_norm()` is lossy by design (AC-22) -- two distinct raw ids like
        # "P1-a b" and "P1-a-b" both norm to "p1_a_b". `scope -> norm text -> {raw: index}`
        # remembers, per disambiguation scope, which raw value first claimed a given
        # norm text (index 0, no suffix -- every existing id shape is unchanged) and
        # assigns any later, DISTINCT raw value that collides with it a numeric suffix
        # instead of silently reusing the first value's node/subgraph id.
        self._collision_index: dict[tuple[Any, ...], dict[str, dict[str, int]]] = {}

    def disambiguated_norm(self, scope: tuple[Any, ...], raw: Any) -> str:
        table = self._collision_index.setdefault(scope, {})
        normed = _norm(raw)
        seen = table.setdefault(normed, {})
        raw_key = str(raw)
        if raw_key not in seen:
            seen[raw_key] = len(seen)
        index = seen[raw_key]
        return normed if index == 0 else f"{normed}_dup{index}"

    def _feature_slot(self, feature_id: str) -> dict[str, Any]:
        if feature_id not in self.features:
            self.features[feature_id] = {"members": [], "packages": {}}
            self.feature_order.append(feature_id)
        return self.features[feature_id]

    def _package_slot(self, feature_id: str, package_id: str) -> dict[str, Any]:
        feature = self._feature_slot(feature_id)
        if package_id not in feature["packages"]:
            feature["packages"][package_id] = {"members": [], "order": len(feature["packages"])}
        return feature["packages"][package_id]

    def add_node(self, node_type: str, feature_id: str, package_id: str | None, label: str) -> str:
        """AC-22's id scheme: `{type}_{norm(feature_id)}[_{norm(package_id)}]_{ordinal}` --
        an explicit ordinal, never reliance on `norm()`/`slugify()` alone, which collides
        distinct raw ids inside the same package. PR-03: the feature/package components
        themselves go through `disambiguated_norm` rather than bare `_norm()`, so two
        raw ids that collide under `_norm()` alone still mint distinct node ids."""
        key = (node_type, feature_id, package_id)
        self._counters[key] = self._counters.get(key, 0) + 1
        ordinal = self._counters[key]
        node_id = f"{node_type}_{self.disambiguated_norm(('feature',), feature_id)}"
        if package_id is not None:
            node_id += f"_{self.disambiguated_norm(('package', feature_id), package_id)}"
        node_id += f"_{ordinal}"
        self.nodes[node_id] = {"type": node_type, "label": label}
        if package_id is not None:
            self._package_slot(feature_id, package_id)["members"].append(node_id)
        else:
            self._feature_slot(feature_id)["members"].append(node_id)
        return node_id

    def add_edge(self, src_id: str, dst_id: str, label: str) -> None:
        self.edges.append((src_id, dst_id, label))


def _review_label(role: str, verdict: str | None) -> str:
    """AC-27: role+verdict for a record that carries a role (subreview/late-review);
    `late_reviews[]` entries carry no `verdict` field at all, so this degrades to the
    role alone rather than printing a label that promises data the record doesn't have.
    """
    role = role or "?"
    return f"{role}: {verdict}" if verdict else role


def _add_package_findings(state: _GraphState, fid: str, pid: str, package: dict[str, Any],
                          data: dict[str, Any]) -> None:
    findings_by_id = {
        item["id"]: item for item in package.get("findings", []) or []
        if isinstance(item, dict) and item.get("id")
    }
    finding_nodes: dict[str, str] = {}
    for finding_id, finding in findings_by_id.items():
        # AC-27: id + severity always; verified_by only once the finding has one.
        label = f"{finding_id} ({finding.get('severity', '?')})"
        if finding.get("verified_by"):
            label += f" verified_by={finding['verified_by']}"
        finding_nodes[finding_id] = state.add_node("finding", fid, pid, label)

    # produjo: review_panels[].subreviews[] -- AC-20's primary source, always carries a role.
    for panel in package.get("review_panels", []) or []:
        if not isinstance(panel, dict):
            continue
        for subreview in panel.get("subreviews", []) or []:
            if not isinstance(subreview, dict):
                continue
            ids = [i for i in subreview.get("findings", []) or [] if i in finding_nodes]
            if not ids:
                continue
            review_node = state.add_node(
                "review", fid, pid, _review_label(subreview.get("role", "?"), subreview.get("verdict")))
            for finding_id in ids:
                state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # produjo: late_reviews[] -- a reviewer that returned after its panel closed (AC-10 of
    # the P2 contract this package extends); always carries a role, never a verdict.
    for late in package.get("late_reviews", []) or []:
        if not isinstance(late, dict):
            continue
        ids = [i for i in late.get("findings", []) or [] if i in finding_nodes]
        if not ids:
            continue
        review_node = state.add_node("review", fid, pid, _review_label(late.get("role", "?"), None))
        for finding_id in ids:
            state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # produjo: delta_reviews[] -- PR-02: a delta review can raise NEW or reopened
    # findings (`new_or_reopened_findings`), and until now this was the one AC-20 source
    # with a real finding-producing field that never fed the join at all (45/195 real
    # findings, 23%, had no produjo edge for exactly this reason). Same shape as
    # late_reviews[] above: the record itself carries everything the label needs, no
    # history join required.
    for delta in package.get("delta_reviews", []) or []:
        if not isinstance(delta, dict):
            continue
        ids = [i for i in delta.get("new_or_reopened_findings", []) or [] if i in finding_nodes]
        if not ids:
            continue
        review_node = state.add_node("review", fid, pid, f"delta: {delta.get('verdict', '?')}")
        for finding_id in ids:
            state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # produjo: reviews[] entries with no panel_id -- the plain `record-review` path (no
    # panel, no role field on the record itself). `finalize-review-panel` also appends to
    # `reviews[]`, but WITH a panel_id and listing every still-open finding at close time
    # (a summary, not a production event) -- already covered above via subreviews, so
    # panel-tagged entries are skipped here to avoid a second, misleading produjo edge.
    # PR-01: `cmd_record_review` now stamps `actor` directly on the record it appends to
    # `reviews[]`, so that is the primary, per-record source -- never fabricated by
    # pairing with something else. Older records from before that stamp existed (or a
    # future record written by a caller that skips it) have no `actor` key at all;
    # for THOSE, and only when the two lists are still in lockstep (`len` equal), a
    # positional join against the `record-review` history events degrades to the
    # legacy behaviour. When a `verdict: blocked` call appended to `reviews[]` and then
    # returned before emitting its own `record-review` history event (see
    # `cmd_record_review`), the two lists permanently diverge in length -- and rather
    # than let every review after that point pair against the WRONG history event, the
    # positional fallback is skipped entirely and the label just omits the actor.
    plain_reviews = [item for item in package.get("reviews", []) or []
                     if isinstance(item, dict) and not item.get("panel_id")]
    review_events = [event for event in data.get("history", []) or []
                     if isinstance(event, dict) and event.get("event") == "record-review"
                     and event.get("package_id") == pid]
    positional_join_safe = len(plain_reviews) == len(review_events)
    for index, review in enumerate(plain_reviews):
        ids = [i for i in review.get("findings", []) or [] if i in finding_nodes]
        if not ids:
            continue
        actor = review.get("actor")
        if not actor and positional_join_safe:
            actor = review_events[index].get("actor")
        verdict = review.get("verdict")
        label = f"{verdict} ({actor})" if actor else str(verdict)
        review_node = state.add_node("review", fid, pid, label)
        for finding_id in ids:
            state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # verificó/refutó: verifications[]. A normal verification call stamps EVERY finding it
    # touches with the same `verified_by` (the same `--actor`), so any touched finding's
    # own field is the structural source for the node's label -- no history join needed.
    for verification in package.get("verifications", []) or []:
        if not isinstance(verification, dict) or verification.get("skipped"):
            continue
        refuted = [i for i in verification.get("refuted", []) or []]
        upheld = [i for i in verification.get("upheld", []) or []]
        touched = [i for i in (*refuted, *upheld) if i in finding_nodes]
        if not touched:
            continue
        actor = findings_by_id[touched[0]].get("verified_by")
        verification_node = state.add_node(
            "verification", fid, pid, f"verified_by={actor}" if actor else "verification")
        for finding_id in refuted:
            if finding_id in finding_nodes:
                state.add_edge(verification_node, finding_nodes[finding_id], "refutó")
        for finding_id in upheld:
            if finding_id in finding_nodes:
                state.add_edge(verification_node, finding_nodes[finding_id], "verificó")

    # A waived verification (`record-verification --skip-reason`) touches no finding at
    # all, so AC-27's actor comes from the triggering `record-verification` history event
    # instead -- paired by position against the skip records, same structural join as the
    # plain-reviews case above. AC-22 still requires the node to exist (no finding edges).
    # D-05: same divergence guard PR-01 gave the plain-reviews join above -- today
    # `cmd_record_verification` always appends the record and its history event in the
    # same call with no early return between them, so the two lists stay in lockstep in
    # practice, but the invariant this join relies on (index N of one list is the SAME
    # call as index N of the other) belongs at every positional-join site, not only the
    # one where a divergence is currently reachable.
    skip_records = [item for item in package.get("verifications", []) or []
                    if isinstance(item, dict) and item.get("skipped")]
    skip_events = [event for event in data.get("history", []) or []
                   if isinstance(event, dict) and event.get("event") == "record-verification"
                   and event.get("package_id") == pid and (event.get("metadata") or {}).get("skipped")]
    skip_positional_join_safe = len(skip_records) == len(skip_events)
    for index, _skip in enumerate(skip_records):
        actor = skip_events[index].get("actor") if skip_positional_join_safe else None
        label = f"waived verified_by={actor}" if actor else "verification: waived"
        state.add_node("verification", fid, pid, label)

    # reparó: repairs[], and its commit when AC-21 declared one. "stops at the finding"
    # (AC-21) is not a special case here: the second edge is simply not added when there
    # is no commit sha on the record.
    for repair in package.get("repairs", []) or []:
        if not isinstance(repair, dict):
            continue
        changed_files = repair.get("changed_files", []) or []
        repair_node = state.add_node("repair", fid, pid, f"{len(changed_files)} changed files")
        for finding_id in repair.get("finding_ids", []) or []:
            if finding_id in finding_nodes:
                state.add_edge(repair_node, finding_nodes[finding_id], "reparó")
        commit_sha = repair.get("commit")
        if commit_sha:
            commit_node = state.add_node("commit", fid, pid, commit_sha[:7])
            state.add_edge(repair_node, commit_node, "reparó")


def _add_package_spawns(state: _GraphState, fid: str, pid: str, package: dict[str, Any]) -> None:
    """AC-02 (010-spawn-provenance): a `spawn` node per `package["spawns"]` entry --
    inventory only, no edges. `--caused-by-spawn` and the provenance chain it would join
    are out of this feature's scope (see ADR-0014); this makes a package's spawn spend
    visible next to its findings/reviews/repairs in the same graph, nothing more. A
    package with no `spawns` key at all (every package written before this feature)
    contributes zero nodes here, never an error -- same posture AC-29 already established
    for legacy history predating `--commit`.
    """
    for spawn in package.get("spawns", []) or []:
        if not isinstance(spawn, dict):
            continue
        # AC-02: spawn_id + role are the label floor; purpose is appended only when
        # non-empty (the CLI's own default is ""), never as a dangling empty segment.
        label = f"{spawn.get('spawn_id', '?')} {spawn.get('role', '?')}"
        purpose = spawn.get("purpose")
        if purpose:
            label += f" {purpose}"
        # ADR-0031: the routed model, when the spawn record carries one — same
        # non-empty-only posture as purpose above.
        model = spawn.get("model")
        if model:
            label += f" [{model}]"
        state.add_node("spawn", fid, pid, label)


def _add_feature_to_graph(state: _GraphState, fid: str, data: dict[str, Any]) -> None:
    # D-04: computed BEFORE the feature node is added -- `packages` can be a malformed
    # non-list/non-dict shape (e.g. `null` or an int from a hand-edited state file),
    # which raises `TypeError` inside `_note_packages`/`_normalize_note_state`. Doing
    # this first means that TypeError (caught by `build_execution_graph`, which then
    # treats the whole feature as `missing`) propagates before any node for this
    # feature exists, instead of leaving a dangling empty feature subgraph behind.
    # PR-08: the SAME legacy-tolerant normalization the notes renderer already applies
    # (`_normalize_note_state` for camelCase keys, `_note_packages` for `packages` as a
    # dict indexed by id or `id` instead of `package_id`) -- never a second, narrower
    # assumption that `packages` is always a modern list of `package_id`-keyed dicts.
    # Without this, every one of those legacy shapes made this function silently drop
    # every package (only the feature node was ever emitted).
    packages = _note_packages(_normalize_note_state(data))
    feature_node = state.add_node("feature", fid, None, f"feature: {fid}")
    package_nodes: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, dict):
            continue
        pid = package.get("package_id")
        if not pid:
            continue
        package_nodes[pid] = state.add_node("package", fid, pid, f"package: {pid}")
        _add_package_findings(state, fid, pid, package, data)
        _add_package_spawns(state, fid, pid, package)

    # bloqueó: AC-26. Feature-level `data["blockers"]` alone, never `history`, and never
    # conditioned on resolution state -- every entry gets an edge, resolved or not.
    for entry in data.get("blockers", []) or []:
        if not isinstance(entry, dict):
            continue
        label = "resolved" if entry.get("resolved_at") else "open"
        entry_pid = entry.get("package_id")
        if entry_pid and entry_pid in package_nodes:
            container = package_nodes[entry_pid]
            blocker_node = state.add_node("blocker", fid, entry_pid, f"blocker: {label}")
        else:
            # AC-26's three feature-anchored cases: package_id is None, unset, or set
            # but matching no known package -- all real, none silently dropped.
            container = feature_node
            blocker_node = state.add_node("blocker", fid, None, f"blocker: {label}")
        state.add_edge(container, blocker_node, "bloqueó")


# SEC-002/SEC-005: the closed charset a `feature_id` must satisfy before it is ever
# used to build a filesystem path or interpolated into the generated document. Nothing
# in `validate_state` constrains `feature_id`'s charset (only non-empty), and `graph`'s
# `--feature-id`/`render_notes`'s `data.get("feature_id")` are both reachable with a
# value that never went through `validate_state` at all (an explicit `init --state-file`
# decouples the on-disk filename from the `feature_id` field the JSON body carries) --
# so this module enforces its own gate rather than trusting either source.
_ID_CHARSET_RE = re.compile(r"^[A-Za-z0-9._-]+$")
# Charset-safe on purpose (see _ID_CHARSET_RE): never the raw out-of-charset value, so
# this placeholder always round-trips through `_mermaid_escape` and the `%%` line
# oracle below unchanged, and it can never itself carry an injection.
_INVALID_FEATURE_ID_PLACEHOLDER = "invalid-feature-id"


def build_execution_graph(root: Path, feature_ids: list[str] | None,
                          features_dir: Path | None = None) -> tuple[_GraphState, list[str]]:
    """AC-22/AC-23. With no `feature_ids`, every `<root>/ai/state/features/*.json` present
    is processed. A requested feature with no state file contributes nothing to `state`
    and its id to the returned `missing` list -- the caller renders the AC-23 skeleton
    comment for it instead of aborting the whole run (AC-22's partial-multi-feature rule).

    PR-05: `features_dir` is optional and, when given, used AS-IS instead of being
    re-derived from `root`. `render_notes` already has its own `features_dir` from
    `status_root()` -- the one function that owns "where does this project's state
    live" -- so passing it straight through here means this function's own
    `root / "ai" / "state" / "features"` convention only has to be right in the one
    place that still relies on it, `cmd_graph`'s CLI entry point, instead of being
    re-derived a second time by chaining `.parent` off a DIFFERENT path
    (`render_notes`'s `out_dir`) and trusting the two conventions to stay in lockstep.
    """
    if features_dir is None:
        features_dir = root / "ai" / "state" / "features"
    if feature_ids:
        wanted = list(dict.fromkeys(feature_ids))  # de-dup, preserve caller order
    elif features_dir.is_dir():
        wanted = sorted(path.stem for path in features_dir.glob("*.json"))
    else:
        wanted = []
    state = _GraphState()
    missing: list[str] = []
    resolved_features_dir = features_dir.resolve() if features_dir.exists() else None
    for fid in wanted:
        if not _ID_CHARSET_RE.fullmatch(fid):
            # SEC-002: a feature_id this shape is either a mermaid-injection attempt
            # (quotes, `%`, newlines -- newlines already collapsed by `_short` inside
            # `_mermaid_escape`, but this gate stops it before it is even considered
            # "missing data" rather than relying on escaping alone) or SEC-005's path
            # traversal attempt. Never echoed, escaped or not: a fixed placeholder.
            missing.append(_INVALID_FEATURE_ID_PLACEHOLDER)
            continue
        path = features_dir / f"{fid}.json"
        try:
            resolved_path = path.resolve()
        except OSError:
            missing.append(fid)
            continue
        if resolved_features_dir is None or not resolved_path.is_relative_to(resolved_features_dir):
            # SEC-005 defense in depth: the charset gate above already forbids `/` and
            # rules out traversal through this exact join, but a symlink inside
            # `features_dir` (or a future looser charset) must not be trusted either --
            # the resolved path must still land inside `features_dir`.
            missing.append(fid)
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            missing.append(fid)
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            missing.append(fid)
            continue
        if not isinstance(data, dict):
            missing.append(fid)
            continue
        try:
            _add_feature_to_graph(state, fid, data)
        except (TypeError, AttributeError, KeyError):
            # D-04: a state file with a malformed `packages` (e.g. `null` or an int
            # instead of a list/dict) or a non-string `repairs[].commit` raises here
            # rather than degrading like every other malformed-input case above. In
            # whole-repo mode (glob of every `*.json`), one hand-edited file must not
            # be able to take the entire `graph` command down -- treated the same way
            # as "missing" (unreadable/undecodable/non-dict) rather than propagating.
            missing.append(fid)
            continue
    return state, missing


_MERMAID_ID_RE = re.compile(r"^[a-z0-9_]+$")
# SEC-001: no `\\.` alternative -- mermaid has no backslash-escape mechanism, so a raw
# `"` or `\` inside a label is a structural violation, never an accepted escaped form.
_MERMAID_NODE_LINE_RE = re.compile(r'^(?P<id>[a-z0-9_]+)\["(?P<label>[^"\\]*)"\]$')
_MERMAID_SUBGRAPH_LINE_RE = re.compile(r'^subgraph\s+(?P<id>\S+)\["(?P<label>[^"\\]*)"\]$')
_MERMAID_EDGE_LINE_RE = re.compile(r'^(?P<src>[a-z0-9_]+)\s*-->\|(?P<label>[^|]+)\|\s*(?P<dst>[a-z0-9_]+)$')
# SEC-002: the ONLY two shapes of `%%` line this module ever emits. Any other `%%`
# line -- including a `%%{init: ...}%%` directive -- is a structural violation, not
# silently skipped, so an out-of-band comment can never smuggle mermaid syntax past
# this oracle. PR-06: the second alternative is `cmd_graph`'s whole-repo-with-no-state-
# directory announcement; its `root` interpolation always goes through `_mermaid_escape`
# first (never the raw value). D-03: `.*` there used to accept ANY text -- strictly
# looser than "no data for"'s `[A-Za-z0-9._-]+` charset for no real reason, since a
# properly-escaped `root` can never contain `"`, `\\`, or `%` (all three are in
# `_MERMAID_ESCAPE_MAP`). Denying exactly those three keeps the common case (a real
# filesystem path, which can legitimately contain `/`, spaces, `:`, etc. that an
# allow-list charset would reject) working while still refusing an unescaped or
# mis-escaped value outright instead of rubber-stamping it.
_MERMAID_MISSING_COMMENT_RE = re.compile(
    r'^%% no data for [A-Za-z0-9._-]+$|^%% no state directory at [^"\\%]*$'
)


def validate_mermaid_structure(text: str) -> list[str]:
    """AC-22's oracle for "valid mermaid": concrete structural assertions, not the
    unfalsifiable phrase alone. Returns a list of violations (empty means valid):
    first non-empty line is exactly `flowchart TD`; every node id matches [a-z0-9_]+ and
    is never a mermaid reserved word; every `subgraph` has a matching `end` (balanced);
    labels are quoted with their `"`, `[`, `(`, and newlines escaped; no `subgraph` id
    equals any node id (the disjoint `sg_` prefix exists exactly to make that impossible);
    the only `%%` lines this module ever emits are `%% no data for <id>` (per-feature,
    AC-23) and `%% no state directory at <root>` (PR-06, whole-repo mode with no state
    directory at all) -- any other comment line, including a mermaid directive, is a
    structural violation.
    """
    problems: list[str] = []
    lines = text.split("\n")
    non_empty = [line for line in lines if line.strip()]
    if not non_empty or non_empty[0] != "flowchart TD":
        problems.append("first non-empty line must be exactly 'flowchart TD'")
    node_ids: set[str] = set()
    subgraph_ids: set[str] = set()
    duplicate_node_ids: set[str] = set()
    duplicate_subgraph_ids: set[str] = set()
    depth = 0
    for raw_line in lines[1:]:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("%%"):
            if not _MERMAID_MISSING_COMMENT_RE.fullmatch(line):
                problems.append(f"disallowed comment line: {raw_line!r}")
            continue
        if line == "end":
            depth -= 1
            if depth < 0:
                problems.append(f"unbalanced 'end' with no open subgraph: {raw_line!r}")
            continue
        if line.startswith("subgraph"):
            match = _MERMAID_SUBGRAPH_LINE_RE.match(line)
            depth += 1
            if not match:
                problems.append(f"malformed subgraph line: {raw_line!r}")
                continue
            sg_id = match.group("id")
            if not sg_id.startswith("sg_"):
                problems.append(f"subgraph id not in the disjoint sg_ prefix: {sg_id}")
            if sg_id in subgraph_ids:  # PR-03: a repeated subgraph id is a real collision
                duplicate_subgraph_ids.add(sg_id)
            subgraph_ids.add(sg_id)
            continue
        edge = _MERMAID_EDGE_LINE_RE.match(line)
        if edge:
            for node_id in (edge.group("src"), edge.group("dst")):
                if not _MERMAID_ID_RE.fullmatch(node_id) or node_id in MERMAID_RESERVED_WORDS:
                    problems.append(f"invalid edge endpoint id: {node_id}")
            if edge.group("label") not in GRAPH_EDGE_TYPES:
                problems.append(f"edge label outside the closed vocabulary: {edge.group('label')}")
            continue
        node = _MERMAID_NODE_LINE_RE.match(line)
        if node:
            node_id = node.group("id")
            if node_id in MERMAID_RESERVED_WORDS:
                problems.append(f"node id is a mermaid reserved word: {node_id}")
            if node_id in node_ids:  # PR-03: a repeated node id means one node's
                duplicate_node_ids.add(node_id)  # data silently overwrote another's
            node_ids.add(node_id)
            continue
        problems.append(f"unrecognized line: {raw_line!r}")
    if depth != 0:
        problems.append(f"unbalanced subgraph/end: {depth} still open at end of document")
    if duplicate_node_ids:
        problems.append(f"duplicate node id: {sorted(duplicate_node_ids)}")
    if duplicate_subgraph_ids:
        problems.append(f"duplicate subgraph id: {sorted(duplicate_subgraph_ids)}")
    collisions = subgraph_ids & node_ids
    if collisions:
        problems.append(f"subgraph id collides with a node id: {sorted(collisions)}")
    return problems


def render_mermaid(state: _GraphState, missing: list[str]) -> str:
    """AC-22/AC-23: the one renderer both `graph` and `render_notes` call. With nothing
    to render at all (no feature processed, none missing) this degrades to the bare
    `flowchart TD\\n` header, which is itself valid per `validate_mermaid_structure`.
    """
    lines = ["flowchart TD"]
    for fid in state.feature_order:
        feature = state.features[fid]
        # PR-03: the SAME disambiguated components `add_node` used for this instance's
        # node ids, never a fresh bare `_norm()` call -- otherwise a colliding raw id
        # pair could still mint two identical subgraph ids even after add_node's own
        # node ids were disambiguated.
        fid_component = state.disambiguated_norm(("feature",), fid)
        lines.append(f'subgraph sg_{fid_component}["{_mermaid_escape(fid)}"]')
        for node_id in feature["members"]:
            node = state.nodes[node_id]
            lines.append(f'  {node_id}["{_mermaid_escape(node["label"])}"]')
        for pid, package_slot in feature["packages"].items():
            pid_component = state.disambiguated_norm(("package", fid), pid)
            lines.append(f'  subgraph sg_{fid_component}_{pid_component}["{_mermaid_escape(pid)}"]')
            for node_id in package_slot["members"]:
                node = state.nodes[node_id]
                lines.append(f'    {node_id}["{_mermaid_escape(node["label"])}"]')
            lines.append("  end")
        lines.append("end")
    for fid in missing:
        # AC-23's skeleton, folded into the same combined document AC-22 requires for a
        # partial multi-feature run instead of a second code path. SEC-002: escaped like
        # every other interpolation in this function -- `build_execution_graph` already
        # gates `fid`'s charset before it ever reaches `missing`, so this is defense in
        # depth, not the only thing standing between `fid` and the document.
        lines.append("%% no data for " + _mermaid_escape(fid))
    for src_id, dst_id, label in state.edges:
        lines.append(f"{src_id} -->|{label}| {dst_id}")
    text = "\n".join(lines) + "\n"
    problems = validate_mermaid_structure(text)
    if problems:
        # This module's own generator producing structurally-invalid mermaid is a real
        # bug, never a caller error -- surfaced loudly instead of shipped silently.
        raise StateError("generated an invalid mermaid document: " + "; ".join(problems))
    return text
