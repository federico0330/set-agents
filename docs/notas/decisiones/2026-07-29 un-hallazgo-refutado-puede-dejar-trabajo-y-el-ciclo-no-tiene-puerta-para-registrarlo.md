# Cuando el unico hallazgo se refuta, el paquete salta a PACKAGE_TESTING y el trabajo que la refutacion revelo se queda sin canal

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P1-schema-normalize|P1-schema-normalize]]

## Contexto

Medido en vivo hoy sobre 007-P1. F-01 fue el unico hallazgo del panel y se refuto. cmd_record_verification mueve la fase de PACKAGE_REPAIR a PACKAGE_TESTING en cuanto no queda nada abierto por encima de low, asi que record-repair pasa a ser inalcanzable y contesta 'cannot record repair from phase PACKAGE_TESTING' con exit 2 -- correctamente, no es un bug del comando. Pero la refutacion en si misma produjo trabajo real: al probar que la frase del ADR era cierta, el verificador expuso que NINGUN test de regresion fijaba el rechazo por PRAGMA integrity_check en el camino rw, que es exactamente lo que esa frase nombra como la razon de que la validacion se quede. Ese test se embarco y no tiene entrada propia en el expediente: entra por la evidencia de record-testing, que es un lugar donde nadie lo va a buscar.

## Decisión

Se registra y no se repara. Arreglarlo es tocar el ciclo de review, que es alcance de la 009 y no de la 007, y ademas requiere decidir la forma: o record-repair acepta un lote sin hallazgos abiertos cuando la fase es PACKAGE_TESTING, o hay un verbo nuevo para 'trabajo derivado de una refutacion'. Ninguna de las dos es una linea.

## Consecuencias

Es la misma clase que start-review-panel-silent-noop y p0-architect-findings-outside-package-record: trabajo verificado que termina en un lugar donde quien mira el paquete no lo encuentra. La diferencia es que aca el trabajo SI se embarco y esta en los tests; lo que falta es su registro. Nota util para quien lo repare: la refutacion adversarial no es solo un filtro que descarta hallazgos, tambien PRODUCE hallazgos, y el ciclo hoy modela nada mas la primera mitad.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
