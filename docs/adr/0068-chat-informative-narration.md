# ADR-0068 — Chat informativo; registros duales solo en vault

- Estado: **Accepted** (2026-08-24). Feature `037-harness-humano-universal-y-terceros`.
- Enmienda **parcial** [ADR-0027](0027-milestone-narration-digest.md): hitos en chat pasan a prosa
  informativa (extiende [ADR-0033](0033-end-of-turn-block-informative.md)); los registros `--client` /
  `--tech` **persisten** en JSONL, bitácora y digest.

## Contexto

ADR-0027 movió narración por hito y duplicó transparencia en chat con bloques `Cliente:` / `Ingeniería:`.
Terceros y el dueño perciben eso como plantilla robótica. El vault (`docs/notas/`, bitácora) ya regenera
el detalle; el chat debe informar proceso en lenguaje plano.

Medición plantilla orchestrator (2026-08-24): bloques (a)+(b) ~22 líneas de plantilla con registros
duales; post-0068 ~12 líneas prosa única + ancla `▸ Instancio` / `✓` — ~45% menos texto de plantilla
en chat (sin contar respuestas del modelo).

## Decisión

1. **Chat:** hitos usan prosa informativa (max ~8 líneas por bloque). **Prohibido** prefijar `Cliente:` /
   `Ingeniería:` en chat del orquestador.
2. **Vault:** sin cambio de CLI; `render_bitacora.py` sigue etiquetando Cliente/Ingeniería en archivos.
3. **Universalidad:** vocabulario usuario-facing neutral (encargo, tanda, consulta, arreglo acotado); modos
   internos invariantes.
4. **Tokens:** orquestador lee `docs/notas/00 - Proyecto.md` + digest antes de re-leer specs enteros;
   ADR-0020 sin cambio.
5. **`/explicar`:** salida dual permitida como producto del comando, no plantilla de coordinación.

## Consecuencias

- Tests de harness dejan de exigir `Cliente:` en orchestrator; exigen ausencia en plantillas chat.
- ADR-0057 (`narration_lint`) sigue aplicando a campos **persistidos**, no al chat.
