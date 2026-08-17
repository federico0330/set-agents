# D2-trabajo-visible — delta review final, ciclo 2

Package: `D2-trabajo-visible`
Base declarada: `489ecff52a7c8aca84ce931180c6f0005cb8a63c`
Repair commit: `d30f94f8276efb0b9d54f5682cbbf7ef5a36de37`
Evidence commit: `0d20287372a6eacb8ad60875b83b4d0b84b39be4`
Modo: delta review focal; ninguna mutación de producto, tests, estado ni commits.

## Checkpoint inicial

- Leídos completos, en este orden, `context/D2-trabajo-visible.md`, `evidence/D2-delta-review.md`,
  `evidence/D2-cycle2-verification.md`, `evidence/D2-cycle2-repair.md` y
  `evidence/D2-repair.md`; también `spec.md:48-52` (AC-04/AC-05).
- Findings bajo juicio: `D2-F01`, `D2-DR01`, `D2-DR02`. Regresión inmediata limitada a AC-04 y
  AC-05; no se reabre la review completa salvo cambio sustancial de arquitectura, contrato o riesgo.
- El worktree compartido ya contiene modificaciones y evidencia no trackeada ajenas. Se preservan;
  este archivo es la única escritura de esta instancia.
- Gates autorizados: pruebas focales, `git diff --check` del rango exacto y medición del repair
  ceiling. No se ejecutarán suite global, `verify.sh`, `build.sh --check` ni paquete posterior.
- Próximo paso: inspeccionar el delta exacto de los dos commits, verificar cada cierre en código y
  tests, ejecutar las reproducciones focales y registrar comando, salida y exit.

## Resultado

VERDICT: `pass`.

## Delta inspeccionado

- `d30f94f8276efb0b9d54f5682cbbf7ef5a36de37` es hijo directo de la base declarada;
  `0d20287372a6eacb8ad60875b83b4d0b84b39be4` es hijo directo del repair y es `HEAD` durante
  esta revisión.
- El rango `489ecff..0d20287` toca cinco archivos: `ai/scripts/set_agents_app.py`,
  `tests/test_provider_registry.py`, `tests/test_menu_ui.py`, `evidence/D2-repair.md` y
  `evidence/D2-cycle2-repair.md`. Son 151 inserciones y 6 eliminaciones (157 líneas cambiadas
  según `--numstat`); no cambia arquitectura, contratos públicos ni otra superficie de riesgo.
- El worktree no tiene cambios posteriores a `0d20287` en los archivos de producto, tests y
  evidencia de reparación enumerados arriba. Las modificaciones ajenas observadas al inicio no
  entraron en el juicio.

## Cierre de findings

### D2-F01 — `closed`

- `ai/scripts/set_agents_app.py:2723-2745` conserva la firma pública de
  `cmd_provider_verify()` y envuelve su cuerpo con `tui.with_progress`, explícitamente sobre
  `sys.stderr`; la fase lenta real sigue en `_provider_liveness` en `:2775-2779` y las líneas
  `PROVIDER_*` continúan escribiéndose por stdout en `:2772,2784,2787,2791`.
- `tests/test_provider_registry.py:293-313` demora liveness 350 ms, fija el entorno degradado
  (`NO_COLOR=1`, `TERM=dumb`), exige progreso plano y línea final persistente en stderr y prohíbe
  el indicador en stdout. La ejecución focal independiente pasó.
- Outcome: la espera antes silenciosa activa señal al cruzar ~300 ms sin contaminar el protocolo
  máquina y deja estado persistente. Satisface AC-04 (`spec.md:50-51`) y la parte aplicable de
  AC-05 (`spec.md:52`).

### D2-DR01 — `closed`

- En post-update, `ai/scripts/set_agents_app.py:1451-1461` sólo usa animación concurrente cuando
  `--yes` vuelve no interactivo al hijo. Sin `--yes`, `subprocess.run` posee el terminal dentro de
  `suspend_terminal()` y la línea final se escribe únicamente después de su retorno.
- `run_tty()` aplica el mismo handoff en `ai/scripts/set_agents_app.py:3631-3642`: no hay renderer
  mientras el wizard puede imprimir y leer un prompt, y queda `ejecutando instalador: listo` tras
  finalizar.
- `tests/test_menu_ui.py:180-228` fuerza prompts de 350 ms en ambas rutas, verifica que no haya
  `\r` entre el prompt y `CHILD_DONE`, comprueba que post-update sigue sin `--yes` y exige la línea
  final persistente. Ambas pruebas pasaron.
- Outcome: ninguna animación compite con input y ninguna de las dos rutas pierde el indicador
  persistente. Satisface AC-05 (`spec.md:52`).

### D2-DR02 — `closed`

- `docs/specs/025-consola-minima-y-flexible/evidence/D2-repair.md:3-4` ya no contiene los dos
  espacios finales que hacían falso el gate documentado.
- Tanto el repair delta (`489ecff..0d20287`) como el acumulado que incluye el commit defectuoso
  original (`489ecff^..0d20287`) pasan `git diff --check` sin salida.
- Outcome: el árbol final y la evidencia coinciden; el defecto de whitespace no sobrevive.

## Regresión inmediata AC-04/AC-05

- No se detectó regresión nueva. El wrapper agregado a provider liveness conserva stdout y usa el
  primitivo ya revisado `tui.with_progress` (`ai/scripts/tui.py:577-640`), que degrada por el stream
  real, espera 300 ms y siempre deja línea final en retorno normal.
- Las pruebas focales también reejecutaron las regresiones de routing para stdout byte-idéntico y
  degradación sin `\r`/ANSI (`tests/test_menu_ui.py:231-277`) y doctor-all con estado persistente
  (`tests/test_menu_ui.py:282-303`); pasaron junto con las tres pruebas de cierre.
- No hay scope creep relacionado: el helper privado `_cmd_provider_verify` separa implementación de
  presentación sin cambiar la firma pública; los dos cambios interactivos reducen writers
  concurrentes y mantienen los códigos de retorno.

## Comandos, salidas y exits

1. Help obligatorio:

   ```text
   $ python3 ai/scripts/check-repair-ceiling.py --help
   usage: check-repair-ceiling.py [-h] --state-file STATE_FILE
                                  --package-id PACKAGE_ID [--baseline BASELINE]
                                  [--changed-lines CHANGED_LINES]
   ```

   Exit `0`.

2. Comando aplicable al paquete:

   ```text
   $ python3 ai/scripts/check-repair-ceiling.py --state-file ai/state/features/025-consola-minima-y-flexible.json --package-id D2-trabajo-visible --baseline 489ecff52a7c8aca84ce931180c6f0005cb8a63c
   {
     "ok": true,
     "package_id": "D2-trabajo-visible",
     "reason": "no repair_ceiling frozen for this package -- nothing to check"
   }
   REPAIR_CEILING_PASS
   ```

   Exit `0`. Interpretación precisa: el gate pasa como no aplicable; no prueba que 157 líneas estén
   bajo un presupuesto. El estado tiene `candidate_identity: null` y `repair_ceiling: null` en
   `ai/state/features/025-consola-minima-y-flexible.json:1386,1506`, y el script define esa rama
   aditiva como PASS en `ai/scripts/check-repair-ceiling.py:59-68`.

3. Pruebas focales:

   ```text
   $ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_provider_registry.ProviderVerifyLivenessScopeTests tests.test_menu_ui.InteractiveInstallerProgressTests tests.test_menu_ui.RouteDoctorProgressTests tests.test_menu_ui.DoctorAllProgressTests -v
   Ran 13 tests in 2.148s
   OK
   ```

   Exit `0`. No se ejecutó suite global ni `verify.sh`.

4. Whitespace y alcance:

   ```text
   $ git diff --check 489ecff52a7c8aca84ce931180c6f0005cb8a63c 0d20287372a6eacb8ad60875b83b4d0b84b39be4
   $ git diff --check 489ecff52a7c8aca84ce931180c6f0005cb8a63c^ 0d20287372a6eacb8ad60875b83b4d0b84b39be4
   ```

   Ambos exit `0`, sin salida. El `git diff --numstat` focal sobre `489ecff..0d20287` también
   terminó exit `0` y midió 157 líneas cambiadas.

## Revisión completa

`requires_full_review`: `false`. El repair no alteró arquitectura, contrato público ni superficie
de riesgo; los cambios son el cierre mínimo de tres findings y quedaron cubiertos por la pasada
focal. No hay findings nuevos o reabiertos.

```json
{
  "package_id": "D2-trabajo-visible",
  "verdict": "pass",
  "closed_findings": ["D2-F01", "D2-DR01", "D2-DR02"],
  "new_findings": [],
  "new_or_reopened_findings": [],
  "requires_full_review": false,
  "requires_full_review_reason": "El repair conserva arquitectura y contratos; el riesgo quedó limitado a progreso y handoff interactivo ya cubiertos por pruebas focales."
}
```
