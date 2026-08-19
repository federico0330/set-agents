# 034 slice: cuota + ruteo orgánico; Engram no entra

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]]

## Contexto

Comparativa SET vs Gentle-AI (canvas 2026-08-19). Federico pidió SDD de lo que Gentle gana y de los huecos. Elegió slice cuota-plus-organic y Cursor pins. Avisó que usa Obsidian para contexto.

## Decisión

En alcance: (1) escritor barato + un salvage caro + techo frontier + % green-on-first-attempt; (2) ruteo orgánico real: quick-fix 1-3 archivos como default operativo, no solo doctrina ADR-0020; (3) Cursor pinnea modelo por rol, enmendar 032 AC-06. Fuera: 16 runtimes, RDD nativo, installer Go, bench Gentle, perfiles OpenCode Tab, Engram. Engram no se implementa: el vault Obsidian (ADR-0012) ya es la memoria durable y Federico lo usa como contexto.

## Consecuencias

El spec 034 declara Engram no-goal con esa razón. Si el vault no se lee al arrancar un spawn, eso es un defecto de 005/025 (ADR-0056), no un motivo para copiar Engram.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
