"""ADR-0029 (017 PKG-B1) — tier/family inference for DISCOVERED, uncurated models.

Pure functions only: no subprocess, no filesystem, no config mutation. The rules
are deliberately conservative:

- **family** is the coarse vendor stem (`claude`, `gpt`, `kimi`, ...) — coarser
  than the curated families on purpose. A coarse family collapses more candidates
  into "same family", which produces MORE review-independence conflicts, never
  fewer: inference can only remove independence, never grant it (ADR-0029 d.3).
- **tier** maps suffix conventions to the closed fast/balanced/frontier set; an
  id nothing matches lands on `balanced`, NEVER `frontier` — an unknown model is
  not allowed to plan or audit by default.

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

_FRONTIER_HINTS = re.compile(r"(-pro|-max|-ultra|-terra|-opus|-plus)(\b|$)|opus")
_FAST_HINTS = re.compile(r"(-mini|-nano|-flash|-lite|-luna|-spark|-haiku|-free|-fast)(\b|$)|haiku")


def bare_id(model: str) -> str:
    """`provider/model` -> `model`, lowercased; already-bare ids pass through."""
    return model.rsplit("/", 1)[-1].lower()


def vendor_stem(model: str) -> str:
    """Coarse family for an uncurated model. Unknown vendors get their own full id
    as family — never merged into someone else's, never granted independence from
    anything that shares the id."""
    bare = bare_id(model)
    for stem, pattern in _VENDOR_STEMS:
        if pattern.search(bare):
            return stem
    return bare


def infer_tier(model: str) -> str:
    """fast/balanced/frontier from suffix conventions; unknown -> balanced."""
    bare = bare_id(model)
    if _FAST_HINTS.search(bare):
        return "fast"
    if _FRONTIER_HINTS.search(bare):
        return "frontier"
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
