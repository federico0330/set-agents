# ADR 0003 — models.toml as the model-routing source of truth

## Status
Accepted (2026-07-22).

## Context
Model assignment lived in five columns of `roles.tsv` (one per opencode profile plus
claude/codex) with the valid model ids hardcoded in `generate.py` (profile→column map, codex
regex, claude alias set, family suffixes). Reacting to a subscription change meant editing 27
rows by hand and touching generator code; there was no way to express "this area now runs on
X" or to detect which roles were orphaned by a cancelled subscription.

## Decision
- `roles.tsv` keeps structure only: `role, mode, temperature, capability, duty`.
- `models.toml` declares `[subscriptions]`, `[catalog]`, optional `[families]`/`[providers]`,
  `[session]` (opencode small_model per lane), one `[areas.<duty>]` block per area, and
  `[roles.<role>]` partial overrides. The go-zen/zen/local profiles survive as lanes of the
  opencode dimension, so `active-profile`, `--profile`, `use-*.sh`, and drift detection are
  untouched.
- `ai/scripts/models_config.py` owns loading, resolution (role > area, lane by lane),
  doctrine validation (implementer/reviewer family separation, mandatory adversarial judge,
  capability/duty coherence), subscription checks by provider prefix, and a deterministic
  emitter. `generate.py` and `install.py` delegate to it.
- `./setup-models.sh` is the editing surface: interactive wizard plus scriptable
  `--status/--check/--set/--add-model/--add/--drop`; `--drop` blocks until every orphaned
  cell is reassigned. Invalid configurations are never written.

## Consequences
- Adding a model or subscription is data (`--add-model`, `[providers]`), not generator code.
- The migration commit was proven byte-faithful: `Global/` did not change when the switch
  landed, and `check-drift` stayed `DRIFT_OK` without reinstalling.
- A legacy-format `roles.tsv` fails with an explicit hint pointing at `models.toml`, covering
  half-applied pulls or stashes.
- The wizard's deterministic emitter does not preserve standalone comments in `models.toml`.
