# Reglas del Proyecto — <NOMBRE DEL PROYECTO>

> Esqueleto. Reemplazá los placeholders <...> y borrá lo que no aplique. Este archivo manda sobre las
> reglas globales del harness cuando hay conflicto, SOLO para este repo.

## Dominio del producto
<Una o dos frases: qué resuelve el sistema y para quién.>
Ejemplo: control de cobros futuros, pagos pendientes, comprobantes, detección de duplicados y conciliación manual.

## Fuente de verdad
- Specs: `docs/specs/**`  · ADRs: `docs/adr/**`  · Estado IA: `ai/state/features/*.json`
  · Logs IA: `ai/state/**`  · Memoria IA: `docs/ai/memory-log.md`

## Invariantes de dominio (ejemplos — ajustar)
- La plata NUNCA se calcula con punto flotante binario (usar enteros en unidades mínimas o decimal exacto).
- Toda acción de cobro/pago/comprobante/conciliación es auditable (actor, timestamp, antes/después).
- Operaciones que deben pasar juntas van en UNA transacción (atómicas).
- La detección de duplicados NO fusiona automáticamente: propone candidatos para revisión humana.
- Estados (pendiente/futuro/vencido) se derivan de status explícito + fechas, no de lógica oculta de UI.

## Verificación
Correr validaciones locales por tarea dentro del paquete y `./ai/scripts/verify.sh` antes de la revisión profunda
del paquete. Después de paquetes aceptados e integración final, `adversarial-judge` debe devolver `JUDGE_PASS`.

## Alcance de implementación
Implementar SOLO el paquete/work packet aprobado en `ai/state/features/<feature_id>.json` y sus ownership paths.
No agregar integraciones, sync bancario, exportes contables, OCR ni pasarelas de pago si no están pedidos.

## Gates de revisión (cuándo son obligatorios)
- Revisión profunda normal: una vez por paquete integrado, no después de cada tarea individual.
- **DB**: el `package-reviewer` carga `db-integrity` cuando toca schema, migraciones, plata, duplicados, conciliación, concurrencia o audit trail.
- **Seguridad**: el `package-reviewer` carga `security-review` y, si hay checkpoint de riesgo explícito, documenta la razón en el estado.
- **Performance**: el `package-reviewer` carga `performance-scalability` para listados, queries, loops sobre datos, paginación, colas o caché.
- **Diseño** (`@architect`): nuevos módulos, cambios de modelo de datos, máquinas de estado.
- **UI/UX** (`@ux-ui-designer`): cualquier cambio de interfaz o manejo de errores en el cliente.

## Stack y comandos
- Stack: <node | .NET | go | python | ...>
- Test: `<comando de test>`  · Lint: `<...>`  · Build: `<...>` (reflejarlos en verify.sh).

## Separación de deberes
El orquestador sólo inspecciona y delega. `gate-runner` ejecuta la verificación. `package-reviewer`,
`delta-reviewer`, `security-auditor` y `finding-verifier` son read-only. Ningún agente que modifica código
audita o juzga ese mismo cambio — y ninguno refuta un hallazgo contra su propio diff: retirar un hallazgo sin
tocar código es un verbo de autorización, así que sólo el `finding-verifier` puede hacerlo, nunca sobre un
hallazgo que él mismo levantó.

## MCP
- Context7 para docs actuales del framework/ORM/librerías de test cuando haya incertidumbre de versión.
- Engram solo para decisiones de alto valor y lecciones verificadas del proyecto.
- Runtime QA/E2E puede encender `playwright` o `brave-cdp` mediante `ai/scripts/mcp.sh` o `ai/scripts/e2e.sh`,
  usarlo sólo para la prueba observable y apagarlo al salir. No pedir al usuario que manipule toggles cuando el
  script puede hacerlo; pedir sólo login/credenciales si el servicio remoto lo exige.
