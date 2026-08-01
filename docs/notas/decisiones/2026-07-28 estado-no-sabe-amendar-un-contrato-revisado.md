# La maquina de estados no sabe amendar un contrato revisado ni retirar un paquete superado

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]]

## Contexto

Descubierto el 2026-07-28 mientras se abria 008-P1. Cuando un SPEC_CHALLENGE hace que el contrato cambie despues del init -- que es exactamente para lo que existe el SPEC_CHALLENGE -- el archivo de estado no puede seguirlo. Tres huecos verificados en ai/scripts/feature-state.py: (1) acceptance_criteria se escribe solo en cmd_init:1197 y ningun comando lo extiende; (2) cmd_update_package:1299 es una lista blanca que excluye owned_paths, tasks, acceptance_criteria y objective, asi que un paquete es inmutable desde create-package; (3) no existe ningun status deferred/superseded y done_ready():457 exige que todo paquete este accepted, asi que un paquete superado bloquea el cierre de la feature para siempre. Ademas approved_spec.hash se guarda como argumento opaco y no lo verifica nada: el de 008 ya habia derivado (estado cecd909c, archivo 0f2965ec) sin que ningun comando fallara ni avisara.

## Decisión

Se registra como hallazgo dentro del alcance de 009-P2 state-machine-required, no de 008. La unica salida disponible hoy es init --force, que destruye historia, y eso ya se pago una vez (ver 008-state-reinit-con-perdida-de-historia). El defecto es de la misma clase que los otros cuatro de la feature 009: el arnes declara un flujo -- REQUIREMENTS -> SPEC_DRAFT -> SPEC_CHALLENGE -> USER_APPROVAL -- y su propia herramienta de estado no soporta el resultado normal de ese flujo, que es un contrato revisado.

## Consecuencias

009-P2 crece: ademas de exigir que exista el archivo de estado, tiene que dar un camino sancionado para amendar el contrato aprobado (extender AC, retirar o superar un paquete) y para detectar que el spec cambio despues de la aprobacion. Hasta entonces, toda revision de contrato posterior al init cuesta una perdida de historia o una deuda permanente.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
