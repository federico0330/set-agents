# 028 — review independiente de N1, N2 y N3b

**Fecha**: 2026-08-17. **Base revisada**: commit `f688531` sobre HEAD `1014b02`.
**Independencia (ADR-0011)**: package-reviewer read-only, contexto limpio, proveedor y modelo
distintos al escritor (el implementer fue Cursor/Copilot).

El código de 028 estaba integrado pero los tres paquetes figuraban `planned` con **cero gates y cero
reviews**. Esta es la revisión que faltaba.

Suites corridas por el revisor: `tests.test_narracion_contrato` (41/41 OK antes de la reparación),
`tests.test_digest` (24/24 OK), `./build.sh --check` → `BUILD_CHECK_PASS`.

## Veredicto original

| Paquete | Veredicto |
|---|---|
| N1-campos-que-obligan | **fail** |
| N2-doctrina-que-explica | **fail** |
| N3b-los-campos-donde-se-leen | **repair_required** |

## Hallazgos y reparación

### N1-F01 — alta — la guarda era ciega a la caja

`ai/scripts/narration_lint.py`. Las familias de punteros estaban escritas con `[A-Z]`/`[PDR]` sin
`re.IGNORECASE`, así que **el mismo texto pasaba o no según la caja**. Medido:

```
minuscula 'pkg 007' -> []                        <- atraviesa la guarda
MAYUSCULA 'PKG 007' -> ['TECH_POINTER_DENSITY']  <- la guarda muerde
```

`pkg 007` es literalmente **B0, el caso que originó la feature**, en minúscula. Ningún test, ADR ni
la spec lo declaraban como límite conocido.

**Reparado, y no con `re.IGNORECASE` a todo.** Bajar la caja a ciegas sobre `flex_sep`
(`[A-Z]{2,6}[ _]\d{2,4}`) convierte la evidencia numérica que ADR-0026 exige en punteros — medido:
`"corrió 528"`, `"en 300"`, `"el 2026"`, `"de 1256"` matchean todas. La mayúscula era el
desambiguador; al perderla hay que reponerlo con vocabulario. Se agregó una familia
`lower_ident` acotada a los prefijos que el repo usa de verdad, medidos sobre `docs/specs/`,
`docs/adr/` y `ai/state/`: AC 9516, ADR 3159, PKG 2047, SEC 849, SPAWN 416, PR 357, RP 346, DR 236,
FD 164, SC 154, RF 87, REV 61, DLT 28.

Resultado: `pkg 007`, `adr-0057`, `d5-f01` y `Sec_012` ahora muerden; `corrio 528`, `en 300`,
`el 2026` y `de 1256` siguen limpios. Tests
`test_lowercase_identifiers_are_pointers_too` y `test_numeric_prose_is_not_mistaken_for_an_identifier`.

### N1-F02 — alta — el relleno diluía la densidad

`ai/scripts/narration_lint.py`, `clause_count`. El docstring del módulo afirmaba como invariante que
*"agregar cláusulas de relleno exige agregar cláusulas reales"*. Era falso y se midió:

```
tech = 'listo, bien, hecho, avanza, cerrado, PKG-007 reparado, seguimos, todo en orden, ok.'
densidad = 0.111  ->  pasa limpio
```

Un `tech` que en los hechos era sólo `"PKG-007 reparado"` envuelto en muletillas atravesaba la
guarda.

**Reparado**: `clause_count` sólo cuenta al denominador las cláusulas con al menos
`_MIN_WORDS_PER_CLAUSE` (2) palabras. La misma entrada da ahora densidad **0.5** y es rechazada. El
test que documentaba la limitación por conjunciones —y que pedía por escrito *"si esto empieza a
fallar, la heurística mejoró: actualizar el comentario"*— fue reemplazado por
`test_padding_with_contentless_clauses_no_longer_dilutes_density`, que afirma que **ninguna** de las
dos formas de relleno diluye.

### N1-F03 — media — la apertura salía sin pasar por nada

`ai/scripts/narration_lint.py`. La detección de "cierre disfrazado de apertura" sólo disparaba si el
llamador **incluía** alguno de `--milestone/--learned/--next/--why/--alternative`. Omitirlos —que es
justamente lo que haría quien esquiva la guarda a propósito, no por descuido— devolvía cero
violaciones, y después el digest filtra los `started`, así que el trabajo descrito no le llegaba a
nadie.

**Reparado**: las reglas de **calidad** (AC-05 topes, AC-04a densidad, AC-04c registro Cliente:) se
extrajeron a `_quality_violations` y se aplican en los dos caminos. Las obligaciones de **cierre**
(milestone, learned/next/why, feature-id) siguen exentas para una apertura legítima, como debe ser.
Test `test_started_still_faces_the_quality_bar`.

### N2-F01 — alta — AC-18 no estaba implementado

Ningún archivo de doctrina decía **cuándo** correr `feature-state.py digest`. Los cinco decían que el
comando existe y qué produce; ninguno decía "cierre de fase" ni "cierre de turno". Y el test que
debía cubrirlo, `tests/test_digest.py::DoctrineTests`, hacía
`assertIn("feature-state.py digest", text)` — **presencia del nombre del comando**, una cadena que ya
existía antes del commit que decía implementar AC-18. Pasaba en verde con o sin trabajo real: es el
mismo falso verde (D-3) que toda la feature 028 existe para erradicar, reproducido en su propio test
de aceptación.

**Reparado**: la cadencia está en los cinco archivos (`Global/_canonical/agents/orchestrator.md` y
los cuatro `Global/_shared/`), y el test nuevo
`test_doctrine_says_WHEN_to_run_digest_not_only_that_it_exists` afirma `PHASE CLOSE` y `TURN CLOSE`
en cada uno.

### N3b-F01 — media — dos topes en desacuerdo

`narration_lint.LONG_FIELD_LIMIT = 400` decidía qué se puede **escribir** (AC-05 concede 400
explícitamente) y `render_bitacora` cortaba en **300**, así que un `tech` de 350 caracteres era
perfectamente legal al escribirlo y salía **siempre** mutilado al leerlo. AC-15 pide alinearlos; lo
implementado los dejó en desacuerdo y sólo hizo ruidoso el corte.

**Reparado**: un solo número. `render_bitacora.NARRATION_FIELD_LIMIT = 400`, usado por los seis
campos, y `test_write_limit_and_render_limit_are_the_same_number` impide que vuelvan a separarse en
silencio. El marcador `_(truncado al render)_` sigue existiendo para lo que sí exceda.

## Hallazgos de proceso — no reparados, anotados

- **Evidencia inexistente**: `docs/adr/0057-...md:154-156` citaba
  `docs/specs/028-narracion-que-ensena/evidence/N1-implementer.md`, y ese directorio no existía. Este
  archivo lo inaugura.
- **Desvío de `owned_paths`**: la spec asignaba a N3a/N3b un archivo nuevo
  `tests/test_narracion_digest.py`; la cobertura equivalente se agregó dentro de
  `tests/test_digest.py`. Funciona, pero es un desvío no declarado.
- **AC-16 sin confirmación registrada**: el AC pedía confirmar *antes* de unificar si la divergencia
  de `AGENTS.codex.md` era deliberada. El revisor lo verificó por su cuenta (`git show 7ee50fd
  --stat`: el commit de ADR-0027 tocó `CLAUDE.md`, `AGENTS.opencode.md` y `AGENTS.pi.md` pero **no**
  `AGENTS.codex.md` — fue deriva, no decisión). El resultado es correcto; el paso de confirmación no
  quedó registrado.

## Lo que ya funcionaba (verificado, no sólo leído)

AC-01 (compatibilidad por ausencia de clave), AC-02 (`--milestone` sin default), AC-03
(`--alternative` en los dos casos correctos), AC-05/AC-05b, AC-06 (el mensaje de rechazo enseña),
AC-07 (`--feature-id` exigido de verdad al cerrar), AC-09/AC-10 (bloque de cierre idéntico en los
cinco archivos, con `GLOBAL_TREE_SYNC_OK` garantizándolo mecánicamente), AC-19 (los campos nuevos se
ven en bitácora y digest, sin `None`), y la exención escrita de `log-quickfix`.
