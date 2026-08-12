# P4-doctrine-human-layer — evidencia de reparación

Feature 019-harness-evolution, PKG-4. Review independiente: aprobado-con-findings (2 findings,
ambos `low`, ambos de calidad de la evidencia — sin código, doctrina ni tests tocados). Único
archivo modificado: `docs/specs/019-harness-evolution/evidence/P4-implementer.md`.

## F-01 (low) — contradicción interna en el conteo de tests

**Finding**: `P4-implementer.md:6` y `:17` decían "los 8 tests nuevos"; el conteo real es 7,
coincidente con `:51` ("7 tests nuevos") y `:157`.

**Verificación del conteo real**:

```
$ grep -c "def test_ac2" tests/test_harness.py
7
```

**Cambio**:
- `docs/specs/019-harness-evolution/evidence/P4-implementer.md:6` — "los 8 tests nuevos" → "los 7
  tests nuevos".
- `docs/specs/019-harness-evolution/evidence/P4-implementer.md:17` — "los 8 tests nuevos" → "los 7
  tests nuevos".

**Verificación post-cambio**: las cuatro menciones del conteo (§0 intro, tabla AC-29, §3 header,
§5 cierre) dicen ahora "7" de forma consistente entre sí y con `grep -c` arriba.

## F-02 (low) — la prueba de mordida de AC-25 tenía el comando elidido

**Finding**: `:64-66` mostraba el heredoc de neutralización de AC-25 con el cuerpo elidido
(`... corta desde "**At a package close specifically**" hasta "**c) At the end of EVERY
turn**"`) en vez del script real, violando el estándar declarado por el propio paquete (ADR-0026:
cada afirmación de verificación viene con el comando pegado y su salida real).

**Reparación**: corrí yo mismo la mordida de AC-25 y pegué el comando literal con la salida real.

Backup:
```
$ cp Global/_canonical/agents/orchestrator.md /var/tmp/orchestrator.md.bak
```

Estado del árbol antes de tocar nada (para comparar al final):
```
$ git status --porcelain > /var/tmp/status_before.txt
$ git diff --stat > /var/tmp/diffstat_before.txt
$ wc -l /var/tmp/status_before.txt /var/tmp/diffstat_before.txt
  122 /var/tmp/status_before.txt
   89 /var/tmp/diffstat_before.txt
  211 total
```

Neutralización del sub-bloque `Impacto humano` (borra desde `**At a package close
specifically**` hasta, sin incluir, `**c) At the end of EVERY turn**`):
```
$ python3 - <<'EOF'
import re
p = "Global/_canonical/agents/orchestrator.md"
text = open(p, encoding="utf-8").read()
start = text.index("**At a package close specifically**")
end = text.index("**c) At the end of EVERY turn**")
text = text[:start] + text[end:]
open(p, "w", encoding="utf-8").write(text)
EOF
$ grep -n "Impacto humano\|At a package close specifically" Global/_canonical/agents/orchestrator.md
NOT_FOUND
```

Rojo confirmado:
```
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac25_package_close_narrates_impacto_humano_subblock_additively
F
======================================================================
FAIL: test_ac25_package_close_narrates_impacto_humano_subblock_additively (test_harness.HarnessTests.test_ac25_package_close_narrates_impacto_humano_subblock_additively)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_harness.py", line 7724, in test_ac25_package_close_narrates_impacto_humano_subblock_additively
    self.assertIn("Impacto humano:", orchestrator)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Impacto humano:' not found in '# Orchestrator — read-only coordinator of the package-based delivery lifecycle\n...'
FAILED (failures=1)
```

Restauración desde backup y verde confirmado:
```
$ cp /var/tmp/orchestrator.md.bak Global/_canonical/agents/orchestrator.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac25_package_close_narrates_impacto_humano_subblock_additively
.
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

Árbol idéntico al estado previo a la ronda de mordida:
```
$ git status --porcelain > /var/tmp/status_after.txt && diff /var/tmp/status_before.txt /var/tmp/status_after.txt && echo STATUS_IDENTICAL
STATUS_IDENTICAL
$ git diff --stat > /var/tmp/diffstat_after.txt && diff /var/tmp/diffstat_before.txt /var/tmp/diffstat_after.txt && echo DIFFSTAT_IDENTICAL
DIFFSTAT_IDENTICAL
```

**Cambio**: `docs/specs/019-harness-evolution/evidence/P4-implementer.md:62-73` (bloque de
mordida de AC-25) reemplazado por la transcripción real de arriba, con comando pegado y salida
pegada, igual que las otras seis secciones de mordida (AC-26, AC-27a, AC-27b, AC-28a, AC-28b,
AC-29).

Nota de proceso: el reviewer independiente ya había reproducido esta neutralización de forma
independiente y confirmado la aserción (rojo, verde tras revertir, árbol limpio) antes de este
finding — F-02 no cuestionaba la veracidad de la afirmación, sino que la evidencia no era
autosuficiente. Esta reparación no fabrica ninguna afirmación nueva: cada línea pegada arriba es
la salida real de un comando que corrí en esta misma sesión.

## Gates de cierre (post-reparación, sobre el árbol restaurado)

```
$ ./ai/scripts/verify.sh
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

```
$ git diff --check
(sin salida, exit 0)
```

## Alcance respetado

Único archivo modificado de forma permanente:
`docs/specs/019-harness-evolution/evidence/P4-implementer.md` (líneas 6, 17, y el bloque
62-73 reemplazado). Ningún cambio a `Global/**`, `tests/**`, `docs/adr/**`, `ai/scripts/**`.
`orchestrator.md` fue mutado transitoriamente para la mordida y restaurado desde backup,
confirmado byte a byte contra el estado previo (`git status --porcelain` y `git diff --stat`
idénticos antes/después). No se mutó estado de feature (`feature-state.py`) — queda para el
orquestador.
