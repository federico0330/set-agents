# El chequeo de ownership es ciego a los archivos sin trackear

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P1-knowledge-home|P1-knowledge-home]]

## Contexto

check-owned-paths.py:40-49 obtiene la lista de cambios con git diff --name-only <baseline>, y git diff no ve archivos untracked. Sobre un arbol sin commitear eso falla en las dos direcciones. Hacia abajo: los archivos nuevos que crea un paquete no aparecen en el diff, asi que el gate los aprueba sin mirarlos; 009-P1 creo diez archivos en docs/ai/knowledge y ninguno habria sido chequeado. Hacia arriba: si se suplen a mano con --changed-file usando git ls-files --others, entran tambien los untracked que ya existian antes del paquete, y el gate marca out_of_scope trabajo ajeno; aca fueron ocho artefactos de las features 007 y 008.

## Decisión

Para este paquete se compuso la lista a mano (git diff vs baseline mas git ls-files --others) y se excluyeron los ocho ajenos probando que ninguno fue tocado: sus mtimes van de 09:41 a 11:49 contra un baseline tomado 13:27. El resultado es OWNERSHIP_PASS sobre los 50 archivos reales del paquete, y la exclusion quedo escrita en la evidencia del gate en vez de en el chat. No se toco check-owned-paths.py: esta fuera del alcance de P1 y arreglarlo de contrabando seria el refactor oportunista que las reglas prohiben.

## Consecuencias

El gate de ownership de todo paquete entregado sobre un arbol sucio vale lo que valga la lista que le pasaron a mano. La correccion natural es que el baseline incluya untracked (git stash create -u, o una lista de untracked capturada al abrir el paquete) y que el script sepa distinguir preexistente de nuevo. Es candidato a 009-P3 o a la deuda registrada, no a P1.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
