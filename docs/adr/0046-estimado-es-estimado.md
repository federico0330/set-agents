# ADR-0046 — Estimado es estimado: cuota restante siempre etiquetada, nunca sin presupuesto

- Estado: Accepted (2026-08-14). Feature 023-senales-de-consumo, PKG-B4
  (`B4-estimado-nunca-dato-del-proveedor`, AC-08/AC-09/AC-10). Depende de B3 (schema 9,
  `usage_rollups` con el par suma/`reported_count`, ya aceptado). No supersede nada.

## Contexto

Ningún proveedor expone cuota restante. Medido a lo largo de 023 (B1-B3): los comandos
permitidos (`opencode auth list --pure`, `codex login status`, etc.) responden autenticado
sí/no y qué modelos listan — nada sobre cuánto queda de una cuota. Lo único que este harness
puede medir es su **propio consumo**, ya agregado por B3 en `usage_rollups` (schema 9) por
ventana UTC-día e identidad, con el par `run_count`/`usage_<field>_sum`/
`usage_<field>_reported_count` que hace visible la **cobertura**: cuántos de los runs de la
ventana efectivamente reportaron ese campo.

La trampa que este paquete existe para cerrar: una cobertura de 12/40 presentada como
promedio sobre 40 (o como si los 28 runs restantes hubieran reportado cero) produce un número
con forma de dato que es, en realidad, una adivinanza. Es precisamente el tipo de defecto que
"suena razonable" — y por eso necesita una regla escrita, no una buena intención.

## Decisión

### 1. Un solo call site puede escribir "restante" — `format_metric_estimate`, `cost-report.py`

`ai/scripts/cost-report.py` gana una Section 3 ("ESTIMADO"), que lee `usage_rollups` para la
ventana UTC-día vigente (o la que `--window-start` fije, uso interno de tests) y, por cada uno
de los cinco campos de token (`FIELDS` — tokens únicamente, misma doctrina "what matters is
quota" que el propio docstring del módulo ya declaraba para las Secciones 1/2; `cost_micros`
queda fuera de esta superficie), imprime SIEMPRE:

- lo consumido, medido, sin proyectar (`usage_<field>_sum`, la suma cruda);
- su cobertura, como el par exacto que el schema ya carga: `reported_count`/`run_count`
  (nunca un promedio que trate los runs sin reportar como si hubieran reportado cero);
- la ventana **nombrada por su definición**: el rango ISO exacto que
  `usage_rollups.window_start` bucketiza, nunca una frase relativa ("última semana").

Un "restante" solo aparece para un campo que el caller declaró explícitamente con
`--budget FIELD=N` (AC-10) — y cuando aparece, lleva en la MISMA línea:
`ESTIMADO`, `provider_reported: false`, su `basis` (presupuesto declarado menos lo consumido
medido) y la cobertura. Las cuatro piezas viven en un único f-string, dentro de
`format_metric_estimate` — no hay una segunda función ni un segundo `print` que pueda emitir
la palabra "restante" sin arrastrarlas.

### 2. El guardián es estructural, no una convención

`test_cost_report_restante_has_exactly_one_render_site` (`tests/test_harness.py`, precedente
`test_canonical_ddl_is_pinned_to_schema`, `tests/test_routing.py:1424`) cuenta las ocurrencias
del marcador literal que arma la línea de "restante" en el código fuente y exige que sea
exactamente una. Un futuro call site que imprima su propio "restante" ad hoc — sin las cuatro
piezas — mueve ese conteo y el gate falla ahí mismo, no la próxima vez que alguien lo note en
una superficie real. Complementado por dos pruebas de comportamiento que muerden en las dos
direcciones: con `--budget` declarado, la línea aparece con sus cuatro piezas; sin él, el
marcador de valor (`"restante estimado:"`) no aparece en absoluto, en ningún campo — sólo
"consumido en la ventana".

### 3. Sin presupuesto declarado no hay denominador — y no se inventa uno

`--budget` es la única fuente de un presupuesto: no hay horario de reset ni cuota inferidos
desde ningún archivo o API. Un campo sin `--budget` nunca produce un "restante" — la única
salida es la medición cruda más su cobertura, que es información honesta aunque incompleta,
nunca una cifra con forma de dato inventado.

### 4. Nunca en el sort key, nunca en `reason_codes`

Sin cambios sobre `service.py` ni `reason_codes` en este paquete — el consumo es información
para el humano, decisión ya tomada y no re-litigable desde el arranque de 023.

## Alternativas rechazadas

- **Proyectar el consumo sobre `run_count` completo cuando la cobertura es parcial** (p. ej.
  `sum / reported_count * run_count`): rechazado — es exactamente la trampa que el context
  pack de este paquete nombra por nombre; un promedio sobre una cobertura de 12/40 presentado
  como "consumo diario" es falso aunque suene razonable.
- **Un horario de reset inferido (medianoche del proveedor, ciclo de facturación asumido)**:
  rechazado — ningún proveedor lo expone por los comandos permitidos, y asumirlo sería
  inventar un denominador que el harness no puede verificar.
- **Presupuesto persistido en `config.toml`/`models.toml` en vez de un flag por invocación**:
  considerado y diferido — el paquete no necesita más superficie que la que
  `--budget FIELD=N` ya cubre para cumplir AC-08/AC-09/AC-10; persistirlo es una extensión
  futura, no bloqueante.

## Consecuencias

- `cost-report.py --budget input=N` es la única forma de ver un "restante", y siempre
  etiquetado como estimado, nunca como dato del proveedor.
- Toda la información de consumo medido (Sections 1-3) sigue sin sumarse entre fuentes
  distintas (B2, AC-04/AC-05) ni entrar al ruteo (no-goal de la spec, sin cambios).
- Un futuro paquete que quiera agregar otra superficie de "restante" (p. ej. un panel en
  `set_agents_app.py`) hereda la misma obligación de las cuatro piezas — este ADR es la
  referencia, y el guardián estructural de `cost-report.py` es el precedente a replicar, no a
  reinventar desde cero.

## Evidencia

`docs/specs/023-senales-de-consumo/evidence/B4-implementer.md`.
