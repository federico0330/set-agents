# Context pack — C3-primer-arranque-honesto

Spec: `docs/specs/024-listo-para-terceros/spec.md`, **AC-06, AC-07, AC-08**. Depende de **C2**, ya
aceptada: el repo ya no declara las credenciales de nadie.

## Los tres defectos, medidos

### AC-06 — el loop infinito con `--yes`

`install.sh:56-62`:

```bash
confirm() {
  [ "$YES" -eq 1 ] && return 0
  ...
}
```

y `install.sh:309-311`:

```bash
while confirm "¿Correr 'opencode auth login' (una vez por proveedor)?"; do
  opencode auth login || true
done
```

Con `--yes`, `confirm` devuelve 0 **siempre**. El `while` **nunca termina**. Una instalación
desatendida —CI, un script, alguien probando el producto— cuelga ahí para siempre.

### AC-07 — el recién llegado recibe un error mudo

Cuando ninguna credencial está viva, todas las rutas se excluyen y la decisión sale
`NO_ELIGIBLE_ROUTE` (`service.py:437`). Eso es **correcto** como fail-closed, pero no dice **qué
hacer**. Alguien que acaba de clonar recibe un `HUMAN_DECISION_REQUIRED` sin instrucción.

**Código aditivo `ROUTING_UNCONFIGURED`** cuando **todas** las exclusiones fueron
`PROVIDER_UNAUTHENTICATED` (`catalog.py:306,321`). Sigue siendo fail-closed; deja de ser ciego. El
mensaje nombra los comandos exactos de login por runtime.

**Aditivo quiere decir aditivo**: `NO_ELIGIBLE_ROUTE` sigue existiendo para todo lo demás. Si tu
cambio hace que una exclusión genuina de catálogo también reporte `ROUTING_UNCONFIGURED`, rompiste
el diagnóstico.

### AC-08 — el harness reescribe los globales del usuario sin avisar

`install.py:193-194` y `merge_codex` (`:237`), con `roster_codex_orchestrator()` (`:267`): el
install **le cambia el `model` de su `~/.codex/config.toml`**.

No es hipotético: en esta sesión el `--install` le cambió a Federico `gpt-5.6-luna` por
`gpt-5.6-terra`. Se le avisó porque el orquestador lo miró antes; el harness no dijo nada.

Es la misma familia que 022/P4 cerró para `opencode.json`: **el harness no pisa lo del usuario sin
diff y consentimiento**.

## TAREA

Los tres, en ese orden de riesgo: AC-08 es el que toca archivos ajenos, AC-06 el que cuelga, AC-07
el que informa.

## La trampa

**AC-08 no puede convertirse en "no configurar nada".** El harness necesita que el modelo del
coordinador sea el que el perfil dice, o el ruteo miente. Lo que cambia es **cómo**: mostrar el
diff y pedir consentimiento, no decidir en silencio. Con `--yes`, consentimiento dado — pero el
diff se muestra igual, para que quede en el log.

## Restricciones

- **ADR-0049** (`ls docs/adr/` para confirmar, indexalo en `docs/adr/README.md`): primer arranque
  honesto.
- **No toques el sort key** ni la lógica de selección.
- **No relajes el fail-closed.** `ROUTING_UNCONFIGURED` informa, no habilita.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques nada bajo `~`.** En particular **no corras `install.sh` ni `install.py` apuntando al
  `HOME` real**: usá `--home` de fixture. El `~/.codex/config.toml` de Federico tiene su modelo y
  su effort, y el `~/.local/state/set-agentes/subscriptions.local.toml` su config de C2.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1113 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041). Tres agentes ya lo violaron esta noche y tuvieron que repetir.

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C3-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **`install.sh --yes` terminando**, con la prueba de
que antes colgaba (timeout acotado, no esperes al infinito); `ROUTING_UNCONFIGURED` apareciendo
cuando todo fue `PROVIDER_UNAUTHENTICATED` **y no apareciendo** cuando la exclusión fue de catálogo;
el diff que el install ahora muestra antes de tocar un global; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** Ya van
cinco guardas huecas en este proyecto. No escribas la sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

`LICENSE` y la matriz de soporte (C4) · el sort key · `models.toml` y el overlay (C2, ya aceptada) ·
`ai/state` (C1, ya aceptada) · el aislamiento roto de los módulos de test y los otros defectos
latentes registrados · features 025 y 026.
