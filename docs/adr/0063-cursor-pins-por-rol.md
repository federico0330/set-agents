# ADR-0063 — Pins Cursor por rol; 032 AC-06 superseded en parte

- Estado: **Accepted** (2026-08-19). Feature `034-cuota-organica-y-writer-barato`, PKG-D.
  Aprobado con el Feature Contract (hash `539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`).
- Enmienda el contrato **032** (spec shippeado): supersede **parcial** de AC-06
  entero y de la cláusula `model: inherit` de AC-01. El archivo 032 no se
  reedita. Extiende ADR-0003 (`AREA_FIELDS` gana `cursor`) **sin** hacer de
  Cursor una lane de ruteo (ADR-0030/0032 intactos: Cursor sigue fuera de
  `RUNTIMES`).
- Independencia: ADR-0011 D3 (degradación ruidosa cuando no hay dos familias).

## Contexto

032 eligió `model: inherit` en todos los agentes Cursor para que el harness no
gastara una suscripción que el usuario no eligió en el picker. Medido y vigente:

- Emisión: `generate.py:572-574` hardcodea `"model: inherit"`.
- Validador: `generate.py:735-748` muere si no hay `\nmodel: inherit\n`.
- Test: `tests/test_harness.py:14016-14022` `test_no_cursor_agent_pins_a_model`.
- Doctrina: `generate.py:136-139` (“every role inherits the single model you
  picked in Cursor”); `Global/cursor/AGENTS.md`; live
  `Global/cursor/agents/implementer.md:4`.
- `models.toml` **no tiene** clave `cursor` (`AREA_FIELDS` en
  `models_config.py:39` es `claude/codex/codex_effort/opencode`).
  `RUNTIMES` (`:44`) no incluye cursor.

DEC-CURSOR-PIN: Federico eligió explícitamente que Cursor pinnee modelo por
rol. Eso rompe 032 AC-06 a propósito. Docs de Cursor (citadas por 032,
verificadas 2026-08-18): el campo `model` existe y default `inherit`; un id
concreto es legal. Catálogo vivo de slugs al 2026-08-19: **UNVERIFIED**
(fetch a `https://cursor.com/docs/subagents` timeout en spec y en esta
sesión de architecture).

## Decisión

1. **Fuente del pin = `models.toml`, dimensión `cursor`, merge ADR-0003.**
   `[roles.<role>].cursor` gana a `[areas.<duty>].cursor`. `AREA_FIELDS`
   incluye `"cursor"`. `resolve_role` expone `cursor_model`.
   `[catalog].cursor` es la lista cerrada de slugs **medidos**; un pin fuera
   de la lista hace `die` (fail-closed, patrón claude/codex). Cursor **no**
   entra a `RUNTIMES` ni a `SELECTED_RUNTIMES`. `--route-decide` y
   `*_spawn.py` siguen prohibidos en el anfitrión (`generate.py:125-132`).

2. **`generate.py` emite `model: {cursor_model}`.** Deja de hardcodear
   `inherit`. Roles `code-rw` pinnean el barato de ADR-0060 (slug Cursor
   mapeado — UNVERIFIED hasta V-D01). DEC-ROLES-FRONTIER pinnean otra
   familia. `product-analyst` y `architect` **pueden** frontier; no están
   forzados al pin barato.

3. **Validador y test se reescriben, no se borran.** Exigen: pin presente,
   roster completo, `readonly` como 032 AC-01 (predicado Codex reusado),
   **no** todos `inherit`, independencia o degradación explícita. El
   comentario cita 034 y 032 AC-06 superseded. `inherit` universal pone el
   test en rojo.

4. **Independencia.** `family()` (`models_config.py:560-568`) gana rama
   `cursor_model`: `[families]` si hay entrada, si no el valor crudo.
   Writer y `package-reviewer` / `adversarial-judge` no comparten familia.
   Si el catálogo Cursor medido no ofrece dos familias: pins de **modelo
   distinto** + evidencia no vacía en `record-subreview --evidence` /
   `finalize-review-panel --evidence`. Mismo modelo que el escritor mientras
   exista alternativa = fallo. **UNVERIFIED** si `family()` alcanza (V-D02).

5. **Doctrina instalada.** `CURSOR_DELEGATION_OVERRIDE`, `AGENTS.md` Cursor y
   `00-harness.mdc` dejan de decir “No model is pinned”. Dicen: pin por rol,
   independencia o degradación ruidosa, sin `--route-decide`. 032 AC-07
   (no `hooks.json`) intacto.

6. **Salvage y promoción en Cursor (ADR-0062 / ADR-0061).** Frontmatter de
   `repair-agent` y del resto `code-rw` = barato (AC-D.1). El pesado (salvage
   o `writer_rung != "base"`) es override de invocación — **UNVERIFIED**
   (V-D03). Si V-D03 falla: `HUMAN_DECISION_REQUIRED`. **No** se pinnea
   `repair-agent` pesado. Las variantes `<role>@<tier>` son OpenCode-only
   (`generate.py:581-585`); Cursor no genera `@balanced`/`@frontier`. No se
   vuelve a `inherit` universal si V-D01 no mide slugs: `HUMAN_DECISION_REQUIRED`
   con lo observado.

## Opciones rechazadas

- **Tabla `[cursor_pins]` paralela a `[areas]`/`[roles]`.** Segundo
  decision-maker (ADR-0018 lo rechazó para preferencias). El merge role >
  area ya existe; una dimensión más es el precedente de `claude`/`codex`/
  `opencode`.
- **Traducir `opencode_model` → slug Cursor con un mapa de identidades.**
  Los slugs no coinciden; los jueces pueden querer familia distinta a su
  celda OpenCode. Sería una segunda fuente.
- **Meter Cursor en `RUNTIMES` y rutearlo con `--route-decide`.** 032 lo
  prohibió para no gastar la lane de otro runtime desde el anfitrión. 034
  pinnea; no rutea.
- **Volver a `inherit` universal si el catálogo Cursor no se deja medir.**
  Revierte DEC-CURSOR-PIN en silencio. Fail-closed a humano.
- **Borrar `test_no_cursor_agent_pins_a_model`.** Perdería la guarda de
  roster/`readonly`/pin presente. Se reescribe, igual que el `-fast` (0060).
- **Pinnear `repair-agent` pesado en el frontmatter si V-D03 no da override.**
  Viola AC-D.1. El fallback es `HUMAN_DECISION_REQUIRED`, no un pin que
  haría pesados despachos que no son salvage.
- **Promoción Cursor vía `<role>@<tier>`.** `generate.py:581-585` emite esas
  variantes solo a OpenCode. Cursor no las tiene.
- **Mismo pin writer/reviewer “porque Cursor no tiene familias” sin evidencia
  en el panel.** ADR-0011 D3 exige degradación **ruidosa**, no silenciosa.

## Consecuencias

- 032 shippeado sigue siendo la referencia de target Cursor (skills,
  install, `--check`, bootstrap, no-hooks). Solo AC-06 y la cláusula inherit
  de AC-01 quedan superseded por este ADR + spec 034.
- Un `./build.sh` sin `[catalog].cursor` medido no genera un árbol Cursor
  mentiroso: falla cerrado.
- Independencia en Cursor deja de apoyarse solo en contexto limpio; el pin
  es la primera palanca, el contexto la segunda, la evidencia de degradación
  la tercera.

## Evidencia

`docs/specs/034-cuota-organica-y-writer-barato/design.md` §4.
`generate.py:125-139`, `:572-574`, `:581-585`, `:735-748`.
`tests/test_harness.py:14016-14022`.
`models_config.py:39,44,560-568`.
`Global/cursor/agents/implementer.md:4`.
