# El desvio de alcance de P4 a provider_registry.py queda aprobado, medido

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P4-proveedores-del-usuario|P4-proveedores-del-usuario]]

## Contexto

El implementer de P4 flageo POR SU CUENTA que toco ai/scripts/provider_registry.py, fuera de la lista literal de alcance del context pack, agregando HARNESS_PROVIDER_SEED, seed_or_migrate, ProviderEntry y el serializador TOML. Argumento: ADR-0042 Decision 1 dice que PROVIDERS vive en ese modulo, y la alternativa era duplicar la siembra en set_agents_app.py e install.py, que es el patron de lockstep manual que 0042 existe para eliminar.

## Decisión

APROBADO. Verificado por el orquestador, no aceptado por argumento: el separador esta en provider_registry.py:76 ('===...=== 022 PKG-4 (AC-11..15)'); ProviderSpec (:33) y PROVIDERS (:56) quedan ANTES, y todo lo agregado por P4 va despues (:88-266). Los cuatro tests de caracterizacion de P1 y P2 -byte-identico, guarda AC-01b, lockstep ADR-0034 y tri-estado de resolve_ceiling- pasan en verde SIN editarlos. La ubicacion es coherente con ADR-0042 y evita el duplicado; no se pide reubicacion.

## Consecuencias

Se registro la approved_exception con la razon real (extension flageada), no con la razon generica de 'heredado del diff compartido' que el orquestador habia puesto por adelantado. Nota de proceso: el orquestador primero declaro que el separador no existia, por buscar la cadena literal corta en vez del separador real, mas largo. Corregido con la medicion; la afirmacion del implementer se sostiene.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
