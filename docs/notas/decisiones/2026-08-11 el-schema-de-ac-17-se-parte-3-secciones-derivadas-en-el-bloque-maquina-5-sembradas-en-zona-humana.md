# El schema de AC-17 se parte: 3 secciones derivadas en el bloque maquina, 5 sembradas en zona humana

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P3-cognitive-module-docs|P3-cognitive-module-docs]]

## Contexto

AC-17 y el context pack de P3 ponen las 8 secciones del doc de modulo dentro del bloque ‹!--. El implementer puso solo Responsabilidad, Posee y Ultimos cambios estructurales adentro, y Puntos de entrada, Componentes, Flujo, Invariantes y Decisiones afuera, en la zona humana preservada. El motivo tecnico es real y el package-reviewer independiente lo endosa: merge_note regenera desde el body derivado TODO lo que esta entre los marcadores, y no existe ningun campo estructurado en el estado del que se puedan derivar Flujo, Invariantes o Componentes; meterlas adentro las condena a placeholder eterno o a destruccion de la prosa real que un humano escriba. El reviewer levanto F-07 pidiendo el registro formal de la desviacion, que es exactamente lo que corresponde.

## Decisión

Se acepta la desviacion. El schema de AC-17 queda reinterpretado asi: el bloque maquina cubre lo derivable del estado (Responsabilidad, Posee/Depende de, Ultimos cambios estructurales) y las cinco secciones restantes son PROSA SEMBRADA por quien conoce el modulo, preservada entre regeneraciones. La condicion de la aceptacion es que el doc no mienta sobre esa garantia: F-01 (overview.md afirma que todo se regenera solo) y F-04 (falta senal visible de staleness para el lector) se reparan antes de aceptar el paquete. Sin esas dos reparaciones la desviacion no queda aceptada, porque el paquete estaria reproduciendo el defecto que existe para arreglar.

## Consecuencias

Las cinco secciones sustantivas siguen siendo mantenidas a mano y pueden ponerse stale, igual que docs/architecture/overview.md. El mitigante de fondo es AC-28 (comando /explicar, paquete P4), que compara el doc contra el codigo y avisa si quedo desactualizado; hasta que P4 exista, el mitigante es la senal visible de F-04. Queda anotado como deuda conocida de la feature.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
