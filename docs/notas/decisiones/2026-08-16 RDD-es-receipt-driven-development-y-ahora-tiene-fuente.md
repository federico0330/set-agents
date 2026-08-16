# RDD queda cerrado con fuente: Receipt-Driven Development, verificado contra el upstream

<!-- notas:auto -->
- fecha: 2026-08-16 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D3-posturas-de-autonomia|D3-posturas-de-autonomia]]

## Contexto

La spec de 025 (spec.md:69) definia RDD como 'Receipt Driven Development' SIN citar fuente, y ese texto quedo en la pantalla de metodologias que ve el usuario. Federico confirmo el 2026-08-16 que RDD era lo que gentle-ai habia implementado, pero la expansion de la sigla seguia sin respaldo: las dos skills instaladas solo dicen 'Ported from gentle-ai (Gentleman Programming) RDD strict-TDD module', sin expandirla, y los ADR 0020 a 0024 la usan como sigla suelta.

## Decisión

Verificado contra el upstream con gh api sobre el README de Gentleman-Programming/gentle-ai, cita textual: 'Receipt-Driven Development (RDD) is the supported stable path'. Y el mismo README data el origen: 'Receipt-Driven Development (RDD) started in gentle-ai v1.47.0 on 2026-07-10'. La expansion que la spec afirmaba es CORRECTA; lo que faltaba era la fuente. Se cita en el ADR-0054 y en la spec, con la URL del repo.

## Consecuencias

Nota de metodo, no de contenido: la spec afirmaba algo verdadero sin fuente, y el implementer lo copio de buena fe hasta el texto que ve el usuario. Salio bien por suerte, no por proceso. ADR-0026 exige fuente para afirmaciones sobre blancos moviles, y un vocabulario de un proyecto de terceros lo es. El chequeo que falta y que ya quedo anotado en el registro de RDD: nada valida coherencia de vocabulario entre una spec y las skills canonicas instaladas, ni exige fuente para un termino importado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
