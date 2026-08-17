# Correccion: los paquetes de 028 tampoco se pueden replantear -- el motor no tiene salida

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/028-narracion-que-ensena|028-narracion-que-ensena]]

## Contexto

Se intento el replanteo decidido en 'replanteo-028-paquetes-sin-work-items'. No es ejecutable: create-package exige PACKAGE_PLANNING o PACKAGE_ACCEPTED (cli_lifecycle.py:305-306), y LEGAL_TRANSITIONS (model.py:36-49) solo llega a PACKAGE_PLANNING desde PACKAGE_ACCEPTED. Para aceptar hacen falta los work items que no se pueden crear. Es circular. supersede-package por si solo retira los registros sin poder reemplazarlos.

## Decisión

No se fuerza. 028 queda en PACKAGE_GATES con su gate verde registrado; la revision independiente y las cinco reparaciones viven en docs/specs/028-narracion-que-ensena/evidence/N-package-review.md y en el codigo con sus mordidas probadas. Se registra blocker HUMAN_DECISION_REQUIRED.

## Consecuencias

Segunda instancia de la misma clase de hueco que D5 (ver d5-revision-correctiva-sin-camino-de-estado): un registro que resulta defectuoso no tiene camino de correccion. Alli era una feature cerrada; aca es un paquete creado sin work items. Las dos piden lo mismo: un verbo de correccion de registro. Candidato a feature propia.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
