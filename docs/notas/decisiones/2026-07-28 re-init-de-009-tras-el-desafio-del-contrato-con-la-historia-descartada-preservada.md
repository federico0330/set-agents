# Re-init de 009 tras el desafio del contrato, con la historia descartada preservada

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]]

## Contexto

El spec-challenger devolvio revision_required con 11 hallazgos y el usuario aprobo dos criterios nuevos (AC-12 en P1, AC-13 en P2). El contrato paso de 1.0.0 a 1.1.0 y su hash de 70954fe7 a ec14f43b. feature-state.py no tiene comando para extender acceptance_criteria (cmd_init:1197 es el unico escritor) ni para corregir owned_paths (cmd_update_package:1299 es una lista blanca que los excluye), asi que un contrato revisado no se puede reflejar en el estado sin re-init. Es el segundo dia consecutivo que este limite bloquea, ya registrado como estado-no-sabe-amendar-un-contrato-revisado.

## Decisión

init --force sobre 009 con los trece criterios, y recrear los tres paquetes. A diferencia de 008, aca no se pierde trabajo entregado: los tres paquetes estaban planned con spawns 0 y attempts en cero, asi que lo descartado son cuatro eventos de historia sin contenido. El JSON viejo queda integro en docs/specs/009-self-application/evidence/state-before-reinit.json, verificado byte a byte. El re-init ademas repara dos defectos de planificacion que el desafio encontro y que ningun comando podia arreglar en caliente: F-03, P1 declaraba el patron literal knowledge, y fnmatch(knowledge/security.md, knowledge) es False, con lo cual P1 no podia tocar legalmente ninguno de sus propios archivos; y F-02, P3 no declaraba docs/specs/003-trusted-routing-pi-runtime/design.md, el archivo que AC-11 le exige editar.

## Consecuencias

El registro de 009 empieza en el desafio, no antes. Queda anotado que init acepta cualquier hash sin verificarlo contra el archivo, que es la otra mitad del mismo agujero y ahora tiene AC propio: AC-13. La preferencia por re-init sobre parche vale porque los paquetes estaban vacios; con trabajo entregado la respuesta habria sido la contraria.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
