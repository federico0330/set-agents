# 046 — Design handoff

> `product-analyst`, 2026-08-26. Written to satisfy ADR-0067 §4 (a new feature declares which shipped
> clauses it steps on). **The architect owns the module boundary, the record shape, and the new ADR.**
> Every HOW below is UNVERIFIED until confirmed against the real code.

## Supersedes

| shipped clause | where it lives today | what 046 changes |
|---|---|---|
| The Estado panel's host universe is `HARNESS_CLIS` plus one hand-added `pi` row | `ai/scripts/set_agents_app.py:51` (`HARNESS_CLIS = ("opencode", "claude", "codex")`), rendered at `:3737-3740` inside `_estado_general_lines` (`:3721`) | The host universe becomes the declared seven-name candidate list, with a closed state vocabulary. `HARNESS_CLIS` keeps its meaning for the install/auth flows that already consume it (`auth_state` `:1301`, `_status_data` `:1350-1353`). |

**Explicitly not superseded:**

- **ADR-0042.** `PROVIDERS` (`ai/scripts/provider_registry.py:56-73`) remains the one source for
  provider-keyed tables (`:1-8`), and its insertion order remains a contract because
  `_MODEL_PREFERENCE_PROVIDERS` derives from `tuple(PROVIDERS)` and that order reaches user-facing
  validation messages (`:18-21`). The host axis is a **third** registry, following the precedent 022
  PKG-4 already set with "a SECOND, INDEPENDENT registry in this same neutral module" (`:76-89`).
- **M-1 for the `github-copilot` OpenCode provider** (`ai/scripts/routing_core/catalog.py:144-154`):
  authenticated credential, `Provider not found` from `opencode models github-copilot --pure`, no pair
  added. Reaffirmed, not lifted, until someone re-measures it.
- **ADR-0038** keeps exclusive ownership of installing anything (`cmd_tools_install`'s `TOOL_UNKNOWN`
  tail, `set_agents_app.py:2138-2142`; the `tools.local.toml` revalidation at `:2143-2167`).
- **ADR-0043** keeps defining what a probe proves, and the probe cache root
  (`_probe_cache_root`, used at `set_agents_app.py:3752`).

## Mother functions this feature enters

| entry | anchor | why it is the entry |
|---|---|---|
| `_estado_general_lines()` | `ai/scripts/set_agents_app.py:3721` | The "vidriera" surface (022 AC-19, its own docstring `:3732-3736`); builds the `Harnesses` table at `:3737-3740`. |
| `_status_data()` | `ai/scripts/set_agents_app.py:1335` | Produces the rows `_estado_general_lines` reuses; `rows=True` is where the per-CLI probes happen (`:1349-1353`). |
| `PROVIDERS` | `ai/scripts/provider_registry.py:56` | The axis the host registry must stay out of, and the module whose zero-dependency property (`:10-16`) makes it the natural neighbour. |
| `_tools_data()` / `load_catalog()` | `ai/scripts/set_agents_app.py:2121`, `:1568` | The developer-tool catalog axis, which the seven host candidates are deliberately *not* part of. |
| `_pi_lane_state()` | `ai/scripts/set_agents_app.py:921` | The one existing host-shaped row, today special-cased into the panel. |

## UNVERIFIED — architecture must resolve before implementation

1. **Where the registry lives.** `provider_registry.py` (zero imports beyond `dataclasses`, `:24-30`,
   which is why all three consumers can import it at module scope) versus a new neutral module — and
   if new, its cost at the two gates that scan `ai/scripts/`: `py_compile` in `ai/scripts/verify.sh`
   and the encoding guardian in `tests/test_harness.py`.
2. **The record shape.** What a host row carries beyond name and state: detected path, version
   (`version_of`, `set_agents_app.py:1327`), auth state, lane id.
3. **Candidate list form.** Python constant versus tracked TOML, and whether a user may extend it
   (which would collide with AC-05's propose→approve exclusivity if done carelessly).
4. **`pi`'s row.** Whether `_pi_lane_state()` (`:921`, rendered `:3739-3740`) is replaced by a host row
   or kept alongside it. Two rows for one host would be exactly the duplicated-axis defect this
   feature exists to remove.
5. **Where `unlistable` is computed.** Panel-paint time is `PATH`-only by AC design, so the verified /
   unverified distinction must come from a cached probe (ADR-0043) rather than a synchronous CLI call
   in `menu()`'s hot path.
6. **Cross-feature ordering with 047.** 046 owns the state vocabulary; 047 may only move a host
   between existing states. Architecture confirms that 046 lands first.
