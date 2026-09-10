# Propuesta ejecutiva — identidad honesta de modelos

## Problema y caso de negocio

Una pantalla puede mezclar una respuesta ya enviada, una preferencia para la próxima sesión, lo instalado y una política automática. Confundirlos lleva a corregir la configuración equivocada y erosiona confianza.

## Solución propuesta

SET mostrará un estado único para runtime principal y orquestador: último envío observado, default futuro de SET, instalación y routing. Cada dato conserva su fuente. El último envío sólo se observará en OpenCode y sólo desde la sesión raíz canónica más reciente del proyecto; si no se puede probar con seguridad, se informará “sin observar”.

## Alcance

- Estado CLI/consola de cuatro evidencias, sin llamar “actual” a ninguna.
- Aplicación local serializada: una sola modificación por vez, con relectura antes de confirmar éxito.
- Home inmediato, actualización explícita y acceso directo a Modo experto.
- Separación de `/model`, router automático y restore de defaults.
- Advertencias de plugin estrictamente informativas.

## Fuera de alcance

- Cambiar sesiones abiertas, leer SQLite privada o conservar conversación.
- Exponer IDs de sesión o modificar/respaldar/deshabilitar plugins.
- Alterar artefactos globales, lanes o trabajo existente de 045–048.

## Supuestos

Sólo se usan interfaces públicas de OpenCode. La observación tiene 5 s, 20 raíces candidatas y 1 MiB total de stdout. Los identificadores de modelos se tratan como texto opaco nullable. La compatibilidad de campos de export de OpenCode 1.18.14 se verifica antes de afirmar una observación.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Sesión ambigua o ajena | raíz/proyecto canónicos, orden determinista y degradación segura |
| Contenido sensible | child transitorio, límites y cero retención/exposición de ID |
| Aplicaciones simultáneas/fallidas | lock exclusivo hasta readback; conservar intención pendiente |
| Rótulo engañoso | warning read-only sin backup ni modificación |
| Pantalla lenta | primer frame cache-only; refresh explícito |

## Fases de entrega

| Fase | Esfuerzo relativo | Resultado |
|---|---:|---|
| Proyección local | M | instalación/drift efectivos sin cambiar fábrica |
| Estado honesto | M | estado privado, singular y acotado |
| Consola y modelos | M | home inmediato, experto directo y recuperación |
| Integración | S | regresiones, TTY y huella reproducible |

## Éxito medible

Una sesión hija o de otro proyecto nunca gana el último envío; `/model` no cambia SET; el segundo writer no muta; Automático limpia sólo pins y Restore conserva hosts/subscriptions byte-idénticos. El primer frame no inicia subprocesses y tarda menos de 300 ms en prueba hermética.
