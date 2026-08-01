# AC-10 de 005 nombra docs/adr/0009-mandatory-vault.md pero ese numero ya lo uso 006-P2

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/005-portable-harness|005-portable-harness]] · [[features/005-portable-harness/P2-vault-mandatory|P2-vault-mandatory]]

## Contexto

spec.md AC-10 (contrato 1.1.0, escrito 2026-07-27) dice textual 'docs/adr/0009-mandatory-vault.md'. Para cuando P2 abrio en la implementacion (2026-07-29), 006-P2-finding-verification ya habia tomado ese numero (docs/adr/0009-finding-verification.md, aceptado 2026-07-27, en paralelo). Mismo patron de deriva de numeracion que esta sesion ya registro para 007/009 (el hueco reservado del 0010, citas file:line que se pudren).

## Decisión

El ADR de P2 se escribio como docs/adr/0012-mandatory-vault.md (el proximo numero libre; 0002..0011 ya existen), con la correccion de cita documentada en el propio archivo. No se edita spec.md ni acceptance.md -- misma razon que ac-19-rationale-drifted-mid-package-routing-db-recreated: el hash del contrato aprobado no se re-verifica salvo init --force, y el implementador no deberia enmendar el contrato que lo esta juzgando.

## Consecuencias

Quien lea AC-10 despues de este paquete tiene que saber que el ADR real es 0012, no 0009. Convendria, en una futura enmienda formal de 005 (o en un paquete de mantenimiento del harness), migrar la convencion de ACs que citan numero de ADR a citar por slug (mandatory-vault) en vez de numero, mismo argumento que ya assumio 007-P1 para citas file:linea -> file:simbolo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
