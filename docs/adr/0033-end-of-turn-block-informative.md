# ADR-0033 — End-of-turn block: informative, not telegraphic

- Estado: Accepted (2026-08-06). Quick-fix requested directly by the user.
- Amends the TEMPLATE of the end-of-turn block in `Global/_canonical/agents/orchestrator.md`
  (Narración, point c) and `Global/_shared/AGENTS.pi.md`. Does NOT amend ADR-0011's turn-continuity
  semantics (the `Necesito de vos:` sentinel and the three reasons a turn may end are untouched) nor
  ADR-0027's milestone rule (the five narrated moments stay the same).

## Contexto

The user reported the old four-line block was unreadable in practice:

> "no se entienden nada (porque no se sabe qué trata el paquete, o uno se puede olvidar) [...] quiero que
> lo que busque el mensaje sea informar en qué se está trabajando, dar detalles de lo importante y qué
> conviene hacer luego (a nivel estudiante de ingeniería en informática), no rebuscándosela con las
> palabras, con intención informativa/educativa/divulgativa."

The old template (`Estado: ... | Paquete: ... | Presupuestos: ...` / `Hice:` / `Sigue:` / `Necesito de
vos:`) compressed ids and counters into one line and never re-explained what the feature or package was
about, so a reader returning to the session had no thread to pick up. ADR-0011 D1 said the block was
"kept verbatim", but what D1 actually protects is the STOPPING RULE (the sentinel line and its "nada"
test), not the wording of the report above it.

## Decisión

The end-of-turn block becomes this template, max ~8 lines, plain user language:

```
En qué estamos: <feature_id — qué se está construyendo y para qué, en una frase>  (o "consulta suelta" | "quick-fix: <tema>")
Paquete: <id — qué resuelve este paquete, y "n de m"> | spawns x/y · reviews x/y  (o "-")
Hice: <qué pasó este turno y por qué importa, 1-2 líneas>
Conviene ahora: <próximo paso concreto Y por qué es el siguiente>
Necesito de vos: <decisión concreta pendiente, o "nada">
```

Tone rules attached to the template:

1. **Re-explain, don't assume.** The `En qué estamos` line always says what is being built and for what,
   in one sentence — never a bare feature id. Same for `Paquete`: what this package solves, not just its id.
2. **Informative/educational intent.** Written for a computer-engineering student: plain sentences,
   technical terms allowed and briefly explained when load-bearing, no clever wording, no filler.
3. **`Conviene ahora` carries the why.** The next step names the reason it is the next step (which gate,
   invariant or phase makes it so), because that is what teaches the reader how the pipeline works.

Invariants preserved:

- The literal line `Necesito de vos: <decisión concreta pendiente, o "nada">` stays the last line and
  keeps ADR-0011 D1's operational test: if it would read `nada`, the turn is not over.
- Budgets stay visible (`spawns x/y · reviews x/y`) — moved into the `Paquete` line, not dropped.
- ADR-0027: the block still fires at the end of EVERY turn and the milestone list is unchanged.

`tests/test_harness.py` now asserts the new labels (`En qué estamos:`, `Conviene ahora:`) alongside
`Necesito de vos:` on all four runtimes — the pi lane (`Global/pi/agents/orchestrator.md`,
`Global/pi/AGENTS.md`) is included, closing a coverage gap where only opencode/claude-code/codex were
asserted.

Rejected: *free prose paragraph*. Considered (it reads well) but the fixed labels are what lets the user
scan for the one line they care about and what the tests can pin without pinning prose.
