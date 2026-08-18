# 024 — Opciones para el codename de cliente en repo público

**Fecha**: 2026-08-17. **Quien decide**: Federico.

## Contexto

El harness hardcodea la regla de ruteo de un cliente real en cuatro ubicaciones:

| Archivo | Línea | Texto |
|---------|-------|-------|
| `ai/scripts/generate.py` | 475 | inyecta la regla en el orchestrator de opencode |
| `Global/opencode/agents/orchestrator.md` | 1066 | artefacto generado (instala en la máquina) |
| `tests/test_harness.py` | 7563–7570 | test que EXIGE que esté: `assertIn("For 'replenishment-v2' package 'RPL-P0A' only", orchestrator)` |
| `TIPS-USO.md` | 114 | mención en documentación |

La regla de ruteo es real: *"For `replenishment-v2` package `RPL-P0A` only, route deterministic
package gates to `package-gate-runner`"*. Hoy alguien la usa.

El repo es **PÚBLICO** desde aproximadamente 2026-08-07. El codename viaja a la máquina de cada
tercero que instale el harness.

El historial de git tiene el codename desde commits anteriores. Eso es permanente a menos que se
haga `git filter-repo` + force push.

---

## Opción A — Borrar la regla del árbol actual (DIFF LISTO)

Elimina la regla hardcodeada de los cuatro archivos. El historial git sigue teniendo el codename
(sólo el árbol actual queda limpio). La feature `package-gate-runner` pierde su regla de ruteo del
producto base; quien la necesite tendrá que agregarla en su proyecto.

**Impacto**:
- `ai/scripts/generate.py`: eliminar el bloque `if row["role"] == "orchestrator": oc += ...`
- `Global/opencode/agents/orchestrator.md`: regenerado por `./build.sh`
- `tests/test_harness.py`: remover el `assertIn("For 'replenishment-v2'...")` y el `assertNotIn`
  en la lista de literales hardcodeados (ya están en la aserción `lowered`)
- `TIPS-USO.md`: remover la mención de la deuda

**Diff preparado** (aplicar con `git apply`):

```diff
--- a/ai/scripts/generate.py
+++ b/ai/scripts/generate.py
@@ -472,11 +472,6 @@ def generate_opencode(roles, yolo, models_config, out, variants):
         if row["role"] == "orchestrator":
-            oc += (
-                "\n\nFor `replenishment-v2` package `RPL-P0A` only, route deterministic package gates to "
-                "`package-gate-runner`. That agent is unavailable for every other feature, package, worktree, "
-                "and baseline."
-            )
-        oc = oc.replace("\n\npermission:", "\npermission:")
+        oc = oc.replace("\n\npermission:", "\npermission:")
```

```diff
--- a/tests/test_harness.py
+++ b/tests/test_harness.py
@@ (línea assertIn replenishment-v2)
-        self.assertIn("For `replenishment-v2` package `RPL-P0A` only", orchestrator)
```

*(Después de `./build.sh`, `Global/opencode/agents/orchestrator.md` se actualiza solo.)*

---

## Opción B — Hacer la regla genérica y configurable por proyecto

La regla de ruteo se parametriza: `generate.py` lee una config de proyecto (p.ej.
`.set-agents/routing-overrides.toml` o similar) y las inyecta en el orchestrator. El codename sale
del artefacto base; quien lo necesite lo declara en su propia config.

**Impacto**: requiere diseño y trabajo de implementación (un paquete de feature 024 o nuevo).
No bloquea que 024 cierre, pero lo amplía.

---

## Opción C — Dejar todo como está y aceptar que el codename es público

No cambiar nada. El historial ya es público. La regla de ruteo sigue llegando a terceros.
Documentar la decisión.

---

## Recomendación del orquestador

Opción A es la más conservadora y limpia hoy. El diff es quirúrgico (8 líneas). El historial sigue
existiendo pero el árbol instalado en nuevas máquinas queda sin el codename.

**La decisión es tuya. No aplico ninguna opción sin tu confirmación.**
