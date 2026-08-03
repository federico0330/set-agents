# Los gates de suite completa no se corren en paralelo: build.sh colisiona en staging compartido

<!-- notas:auto -->
- fecha: 2026-08-02 · actor: orchestrator

## Contexto

Durante la pasada 2026-08-02, un unittest discover (gate P2-hygiene) corrio en simultaneo con el verify.sh vivo del integrador de 013. Tres tests que invocan ./build.sh fallaron con exit 1 y FileNotFoundError sobre un orchestrator.md generado a medio regenerar. Reruns aislados: los 3 tests y la suite completa (573 OK) en verde.

## Decisión

Los gates que invocan build.sh (unittest discover completo, verify.sh) se ejecutan secuencialmente, nunca dos agentes a la vez. Un fallo de gate con build.sh exit 1 + FileNotFoundError en artefactos generados se trata primero como sospecha de carrera y se re-corre aislado antes de abrir reparacion.

## Consecuencias

El orquestador seria las corridas de gate pesadas. Deuda opcional futura: staging unico por proceso (mktemp) en build.sh para eliminar la clase de carrera.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
