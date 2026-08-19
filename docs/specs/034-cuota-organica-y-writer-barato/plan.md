# 034 — plan de implementación (pre-aprobación)

Cuatro paquetes en un solo feature. Loop completo por paquete
(implementar → gates → review independiente → repair consolidado →
delta → aceptar). `--mode feature` porque Federico pidió SDD
(`user-asked-full-pipeline`). 033 no se reabre.

## Secuencia

```
PKG-A orgánico ──▶ PKG-B escritor barato ──┬──▶ PKG-C techo + métrica
                                           └──▶ PKG-D pins Cursor
```

- **A primero:** corta la ceremonia el día que aterriza; no depende del
  catálogo de modelos.
- **B antes de C y D:** C cuenta "barato" y "salvage"; D pinnea lo que B
  eligió. C y D **pueden ir en paralelo** después de B aceptado.
- No hay PKG-E. Engram, RDD, installer, bench y 16 runtimes no entran.

## Dependencias

| paquete | depende de | por qué |
|---|---|---|
| A | nada de 034; sí de `log-quickfix` y modos ya existentes | 029 ya exime ejes en `log-quickfix` |
| B | nada de A (ortogonal); sí de `billing_rank` (ADR-0035) y del test `:733-766` | reescribe, no borra |
| C | B aceptado | sin default barato / salvage no hay qué contar |
| D | B aceptado | el pin `code-rw` es el barato de B |
| C ∥ D | — | sin dependencia cruzada |

033 AC-6.1 (context pack) es dependencia **negativa** de A: A declara
que no aplica al quick-fix (AC-A.5).

032 shippeado es dependencia de D: D supersede AC-06; no reedita el
archivo 032.

## Qué dispara decisión humana

Solo lo que la Question policy autoriza. Este contrato **ya resolvió**
salvage, promoción a 2 consecutivos, roles baratos vs frontier,
product-analyst, techos 4/16, pins Cursor, no-goals. No se repreguntan.

Sí para el orquestador **después** de retry budget, o:

1. El modelo más barato que cumple tools **no existe** en el inventario
   vivo (nadie con tools y `billing_rank==0`). Entonces
   `HUMAN_DECISION_REQUIRED` con el inventario medido — no inventar un
   id.
2. Cursor no acepta ningún slug que architecture midió (fail-closed).
   No volver a `inherit` universal en silencio: eso revierte DEC-CURSOR-PIN.
3. Cursor no ofrece override de invocación para salvage o promoción
   (no hay `@tier` en Cursor, `generate.py:581-585`). Entonces humano —
   no pinnear `repair-agent` pesado ni copiar `writer_tier="fast"` al
   paquete 1.
4. Un finding de review que cambie el comportamiento aprobado (p.ej.
   "el techo no debe contar jueces"). Eso es cambio de contrato, no
   repair.

No es pregunta: fallas de test, re-corrida de gates, repair pedido por
el panel, continuar el slice aprobado, instalar un CLI del catálogo.

## Riesgos de secuencia

| riesgo | si se ignora | mitigación |
|---|---|---|
| D antes de B | pins Cursor a ciegas, después hay que regenerar | D espera B |
| C antes de B | la métrica no sabe qué es "barato" | C espera B |
| A y B en paralelo | conflicto bajo en `orchestrator.md` | A primero; B toca repair/salvage en el mismo archivo **después** |
| Subir scoped=8 cuando C ahoga | viola el invariante | AC-C.3; owned_paths de C no incluyen ese literal salvo aserción de igualdad |
| Reescribir `-fast` sin mordida | test verde por inercia | T-B02 RED→GREEN obligatorio |
| Copiar Engram porque un spawn no leyó el vault | viola no-goal 6 | T-X02; el arreglo es 005/025 |

## Presupuesto de despachos (no confundir con frontier)

Este feature corre en Cursor, `--mode feature` → 12 despachos/paquete
(`MODE_BUDGETS`). El techo frontier de 034 (4/16) **también aplica a
034 misma** en cuanto C aterrice. Hasta que C exista, no hay contador:
A y B no lo implementan. Architecture no "adelanta" el techo subiendo
`max_spawns`.

## Gates por paquete

`./build.sh --check` verde, `ai/scripts/verify.sh` verde,
`git diff --check` limpio, `check-owned-paths` contra el baseline del
paquete, mordida ejecutada en cada test nuevo. Aserciones netas no
bajan. Independencia writer/reviewer no se relaja.

## Criterio de cierre del feature

Los cuatro paquetes aceptados con review independiente, métrica
green-on-first-attempt visible en un `cost-report.py` de un paquete
real (puede ser 034 misma), pins Cursor distintos en implementer vs
reviewer (o degradación ruidosa registrada), y un arreglo 1–3 archivos
de prueba que **no** haya creado feature `scoped`. 033 sigue cerrado
en `8fd15fe`.
