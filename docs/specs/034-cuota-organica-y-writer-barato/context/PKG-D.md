# Context pack — PKG-D pins-cursor-por-rol

Spec hash `539a4ff6…d9721`. **AC-D.1–AC-D.6**. Después de PKG-B (el pin `code-rw` **es** el barato de B). HOW: ADR-0063. Supersede **parcial** 032 AC-06 + cláusula `inherit` de 032 AC-01. El archivo 032 **no** se reedita.

**Objetivo.** `./build.sh` emite `model:` por rol en `Global/cursor/agents/<rol>.md`. No todos `inherit`. `code-rw` incl. `repair-agent` = barato de B. Jueces = otra familia. Independencia o degradación ruidosa. Cursor sigue **sin** ser lane.

## Paths

- `ai/scripts/generate.py:572-574` — deja de hardcodear `"model: inherit"`; emite `model: {cursor_model}`.
- `generate.py:125-139` `CURSOR_DELEGATION_OVERRIDE` — ya no “every role inherits”. Dice: pin por rol, independencia o degradación ruidosa, **sigue** prohibido `--route-decide` (`:125-132` intacto).
- `generate.py:735-748` `validate_cursor_target` — reescribir: pin presente, roster completo, `readonly` 032, no todos `inherit`, independencia o degradación explícita. **No borrar.**
- `generate.py:581-585` — variantes `@tier` siguen OpenCode-ONLY. Cursor no recibe `implementer@balanced.md`. Salvage/promoción Cursor = override de invocación (V-D03) o `HUMAN_DECISION_REQUIRED`; **no** pin pesado de `repair-agent`.
- `ai/scripts/models_config.py:39` `AREA_FIELDS` — gana `"cursor"`. `resolve_role` expone `cursor_model`. `RUNTIMES` (`:44`) **no** cambia.
- `models_config.py:560-568` `family()` — rama `cursor_model` (`[families]` o valor crudo).
- `models.toml` — dimensión `cursor` por área/rol (merge ADR-0003: rol gana a área). `[catalog].cursor` = slugs **medidos**; pin fuera de lista → `die`.
- `tests/test_harness.py:14016-14022` `test_no_cursor_agent_pins_a_model` — reescribir, no borrar. Comentario cita 034 y 032 AC-06 superseded.
- Doctrina emitida: `Global/cursor/AGENTS.md` y `.cursor/rules/00-harness.mdc` salen de `generate.py` / `write_cursor_rule`. **No editar `Global/cursor/` a mano.**

**Antes de pinnear (UNVERIFIED):**

- V-D01 — slugs `model:` vivos (https://cursor.com/docs/subagents + picker de la sesión). Timeout de fetch **no** cuenta. Fail-closed: `HUMAN_DECISION_REQUIRED` con slugs observados; **no** volver a `inherit` universal.
- V-D02 — ¿`family()` distingue dos familias? Si no: pins de modelo **distinto** + evidencia no vacía en `record-subreview --evidence`.
- V-D03 — ¿Cursor acepta override de modelo al despachar subagente? Si no: humano; frontmatter `code-rw` sigue barato.

DEC-ROLES-FRONTIER pinnean otra familia: `spec-challenger`, `package-reviewer`, `adversarial-judge`, `architect`. `product-analyst` / `architect` **pueden** frontier (AC-D.2).

## ADRs / invariantes

- ADR-0063 — pin desde `models.toml`; Cursor ∉ `RUNTIMES`.
- ADR-0003 — merge área/rol. ADR-0011 D3 — degradación ruidosa si no hay dos familias.
- 032 AC-01 resto (roster, name/description, readonly), AC-02..05, AC-07 (no `hooks.json`) **intactos**.

## Validación local

```
./build.sh --check
./build.sh --output /tmp/034-pkg-d-out
# frontmatter: implementer y repair-agent = barato; package-reviewer ≠ familia implementer (o distinto + nota)
python3 -m unittest tests.test_harness.CursorRuntimeTargetTests
git diff --check
rg -n 'No model is pinned|every role inherits' Global/cursor ai/scripts/generate.py
```

Mordida: pin ausente → `die`; inherit universal → test sucesor ROJO.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer", "security-auditor"]` — ruteo de cuota en el anfitrión.
- `runtime_surface`: **false**. test owner: **implementer**. `strict_tdd`: **false**.
- `selected_role`/`model`: implementer / inherit (este paquete **cambia** lo que inherit significa para el resto de roles).

## Fuera de alcance

Meter Cursor en `RUNTIMES` · `--route-decide` en anfitrión · pin pesado de `repair-agent` · reeditar `docs/specs/032-*` · 033 · Engram · `hooks.json`.

## Mordida

`validate_cursor_target` con todos `inherit` → rojo. `repair-agent.md` pesado → rojo (debe ser barato).
