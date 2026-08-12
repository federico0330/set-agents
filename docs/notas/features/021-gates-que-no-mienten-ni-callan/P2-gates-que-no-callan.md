# 021-gates-que-no-mienten-ni-callan · P2-gates-que-no-callan

<!-- notas:auto -->
## Motivo

- objetivo: Que correr los gates no deje al que los corre mudo mas de 60s, y que la doctrina deje de recomendar el patron que lo causa
- complejidad: small
- paths: `ai/scripts/verify.sh`, `Global/_canonical/agents`, `Global/_canonical/skills/spawn-prompt`, `tests/test_harness.py`
- depende de: P1-check-que-verifica

## Tareas

- [ ] Modo de gates con latido: ningun intervalo sin emitir supera el umbral (AC-06) (planned)
- [ ] La doctrina deja de recomendar comando-largo-pipe-tail; frase exacta y testeable (AC-07) (planned)
- [ ] Dejar escrito que el watchdog es del runtime del agente, no del repo (AC-08) (planned)
- [ ] Test que prueba que el patron prohibido no aparece en briefs ni plantillas (AC-09) (planned)

↩ [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
