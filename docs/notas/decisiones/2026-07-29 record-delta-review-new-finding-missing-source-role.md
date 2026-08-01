# record-delta-review no estampa source_role en --new-finding, a diferencia de record-subreview y record-late-review

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P3-correct-record|P3-correct-record]]

## Contexto

Reproducido en vivo por el segundo delta-reviewer de 007-P3: N-01/N-02/N-03 (los tres hallazgos que un delta-reviewer presento via --new-finding en record-delta-review) son los unicos hallazgos de todo el paquete P3-correct-record sin source_role en ai/state/features/007-quota-visibility.json. cmd_record_subreview (feature-state.py ~1698-1699) y el camino de record-late-review (~1888-1890) hacen finding.setdefault('source_role', role) al mergear un hallazgo nuevo, con un comentario explicito sobre por que: sin eso, cmd_record_verification no tiene con que comparar y quien presenta un hallazgo tardio podria despues refutar el suyo propio. cmd_record_delta_review (~2238-2242) llama merge_finding(package, finding) sobre --new-finding sin ese mismo setdefault.

## Decisión

No se repara en 007-P3: el paquete no posee codigo de ai/scripts/feature-state.py (fuera de owned_paths y de la excepcion aprobada, que es solo docs/specs/007-quota-visibility/**), y arreglarlo desde una reparacion de documentacion seria alcance no aprobado. Se registra como deuda, con reproduccion concreta en vez de solo la mencion generica que ya existia (el gap de 009-P3 sobre source_role en general). El guard anti-auto-refutacion de record-verification (linea ~2119, compara finding.source_role contra el actor) queda inerte para todo hallazgo nacido en un DELTA_REVIEW: nada impide hoy que el mismo rol que presento un --new-finding en record-delta-review lo refute despues en un record-verification posterior.

## Consecuencias

Candidato de una linea (finding.setdefault('source_role', args.role) o equivalente, mismo patron que los otros dos sitios) para el proximo paquete que toque feature-state.py -- candidato natural: 007-P3 (Pi cost fixes) NO, sino una futura 009 o el propio corte 1.3.0->1.4.0 de 007 si se abre un paquete de mantenimiento del arnes. Mientras tanto: ningun hallazgo de DELTA_REVIEW de este repo se auto-refuta hoy porque nadie lo intento, no porque el guard lo impida.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
