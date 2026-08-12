"""ADR-0029 (017 PKG-B1) — tier/family inference for DISCOVERED, uncurated models.
Extended by ADR-0034 (019 PKG-1): tier is capped at `balanced` UNCONDITIONALLY (no
suffix can ever promote to `frontier` anymore), and vendor-stem resolution is now a
first-class, separately-observable outcome (`stem_resolved`) so the decision layer can
fail closed when a synthesized reviewer's own stem never matched anything.

Pure functions only: no subprocess, no filesystem, no config mutation. The rules
are deliberately conservative:

- **family** is the coarse vendor stem (`claude`, `gpt`, `kimi`, ...) — coarser
  than the curated families on purpose. A coarse family collapses more candidates
  into "same family", which produces MORE review-independence conflicts, never
  fewer: inference can only remove independence, never grant it (ADR-0029 d.3).
- **tier** maps suffix conventions to the closed fast/balanced/frontier set; an id
  nothing matches lands on `balanced`. ADR-0034: a synthesized route can NEVER reach
  `frontier`, full stop — a provider-chosen model NAME (`-pro`, `-max`, `-opus`, ...)
  is not a credential a curator granted, so it cannot self-promote to the tier that
  plans or audits critical work. `_FAST_HINTS` (degrading to `fast`) is the opposite
  direction and stays: it can only ever narrow what an unknown model is trusted with,
  never widen it — consistent with "inference only removes, never grants" (d.3).

Every synthesized route is marked `inferred` so the decision layer can surface
`MODEL_METADATA_INFERRED` instead of passing curation-grade metadata off as fact.
"""

from __future__ import annotations

import re

# Ordered: first match wins. Stems are matched against the bare model id (the part
# after a `provider/` prefix, lowercased).
_VENDOR_STEMS = (
    ("claude", re.compile(r"^claude|^(opus|sonnet|haiku)\b")),
    ("gpt", re.compile(r"^gpt-|^o[0-9]|codex")),
    ("kimi", re.compile(r"^kimi")),
    ("glm", re.compile(r"^glm")),
    ("deepseek", re.compile(r"^deepseek")),
    ("minimax", re.compile(r"^minimax")),
    ("qwen", re.compile(r"^qwen")),
    ("gemini", re.compile(r"^gemini")),
    ("grok", re.compile(r"^grok")),
    ("nemotron", re.compile(r"^nemotron|^llama-nemotron")),
    ("llama", re.compile(r"^llama")),
    ("mistral", re.compile(r"^mistral|^magistral|^devstral")),
    ("north", re.compile(r"^north")),
)

_FAST_HINTS = re.compile(r"(-mini|-nano|-flash|-lite|-luna|-spark|-haiku|-free|-fast)(\b|$)|haiku")
# ADR-0034 (AC-05): _FRONTIER_HINTS is DELETED, not merely unused — a synthesized route
# is capped at `balanced` unconditionally; see the module docstring for why the removed
# promotion-by-suffix rule was the wrong direction for inference.


def bare_id(model: str) -> str:
    """`provider/model` -> `model`, lowercased; already-bare ids pass through."""
    return model.rsplit("/", 1)[-1].lower()


def _match_stem(bare: str) -> str | None:
    """First `_VENDOR_STEMS` pattern that matches, or None — the one place that knows
    whether a bare id genuinely resolved to a known vendor family, as opposed to falling
    back to its own id (`vendor_stem`'s behavior). Kept separate from `vendor_stem` so
    ADR-0034's `stem_resolved` can observe "did anything match" without ever confusing an
    unknown vendor whose OWN id happens to equal some stem name."""
    for stem, pattern in _VENDOR_STEMS:
        if pattern.search(bare):
            return stem
    return None


def vendor_stem(model: str) -> str:
    """Coarse family for an uncurated model. Unknown vendors get their own full id
    as family — never merged into someone else's, never granted independence from
    anything that shares the id."""
    bare = bare_id(model)
    return _match_stem(bare) or bare


def stem_resolved(model: str) -> bool:
    """ADR-0034 (AC-06): True only when `model`'s bare id matched one of the KNOWN
    `_VENDOR_STEMS` patterns — never true merely because `vendor_stem`'s fallback (the
    bare id itself) happens to look plausible. `service.py` uses this to exclude a
    synthesized route from reviewer eligibility outright (fail-closed,
    `REVIEW_IDENTITY_UNRESOLVED_INFERRED`) when it can never even be proven to differ
    from the writer's real vendor -- inference removing independence, never granting it,
    same discipline as the family-conflict check next to it (ADR-0029 d.3)."""
    return _match_stem(bare_id(model)) is not None


def infer_tier(model: str) -> str:
    """ADR-0034 (AC-05): fast/balanced only -- a synthesized route can never reach
    `frontier`, no matter what suffix its own name carries (the promotion rule this
    replaced is deleted, not merely bypassed; see module docstring)."""
    bare = bare_id(model)
    if _FAST_HINTS.search(bare):
        return "fast"
    return "balanced"


def synthesize_route_row(provider: str, model: str, roles: tuple[str, ...]) -> dict:
    """One routes.v1.toml-shaped row for a discovered model, metadata inferred.

    `effort` follows the provider conventions build_snapshot already enforces for
    curated rows (anthropic must be medium; others default medium too). `tools`
    is the full standard set — capability enforcement lives in the role layer
    (generate.py permissions), not here. `curated_priority` sits BELOW every
    curated row's default so a curated alternative always outranks a synthesized
    one at the final tie-break.
    """
    return {
        "provider": provider,
        "model": model,
        "family": vendor_stem(model),
        "effort": "medium",
        "tier": infer_tier(model),
        "roles": list(roles),
        "tools": ["read", "shell", "write"],
        "curated_priority": 1000,
        "inferred": True,
    }
