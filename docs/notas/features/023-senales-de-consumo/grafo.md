# 023-senales-de-consumo · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_023_senales_de_consumo["023-senales-de-consumo"]
  feature_023_senales_de_consumo_1["feature: 023-senales-de-consumo"]
  subgraph sg_023_senales_de_consumo_b1_registro_que_no_miente["B1-registro-que-no-miente"]
    package_023_senales_de_consumo_b1_registro_que_no_miente_1["package: B1-registro-que-no-miente"]
    spawn_023_senales_de_consumo_b1_registro_que_no_miente_1["SPAWN-001 implementer Que el consumo de cada spawn efectivamente llegue a la base, y que el normalizador no invente ni …"]
  end
  subgraph sg_023_senales_de_consumo_b2_el_reporte_dice_de_donde_sale["B2-el-reporte-dice-de-donde-sale"]
    package_023_senales_de_consumo_b2_el_reporte_dice_de_donde_sale_1["package: B2-el-reporte-dice-de-donde-sale"]
    spawn_023_senales_de_consumo_b2_el_reporte_dice_de_donde_sale_1["SPAWN-001 implementer Traducir las formas que los lanes ya mandan, y que el reporte no sume dos mediciones del mismo ga…"]
  end
  subgraph sg_023_senales_de_consumo_b3_ventana_y_rollup["B3-ventana-y-rollup"]
    package_023_senales_de_consumo_b3_ventana_y_rollup_1["package: B3-ventana-y-rollup"]
    finding_023_senales_de_consumo_b3_ventana_y_rollup_1["B3-F01 #40;critical#41; verified_by=orchestrator"]
    finding_023_senales_de_consumo_b3_ventana_y_rollup_2["B3-F02 #40;critical#41; verified_by=orchestrator"]
    finding_023_senales_de_consumo_b3_ventana_y_rollup_3["B3-F03 #40;high#41; verified_by=orchestrator"]
    finding_023_senales_de_consumo_b3_ventana_y_rollup_4["B3-F04 #40;medium#41; verified_by=orchestrator"]
    finding_023_senales_de_consumo_b3_ventana_y_rollup_5["B3-F05 #40;medium#41; verified_by=orchestrator"]
    finding_023_senales_de_consumo_b3_ventana_y_rollup_6["B3-F06 #40;low#41; verified_by=orchestrator"]
    review_023_senales_de_consumo_b3_ventana_y_rollup_1["repair_required #40;package-reviewer#41;"]
    verification_023_senales_de_consumo_b3_ventana_y_rollup_1["verified_by=orchestrator"]
    repair_023_senales_de_consumo_b3_ventana_y_rollup_1["2 changed files"]
    spawn_023_senales_de_consumo_b3_ventana_y_rollup_1["SPAWN-001 implementer Schema 8 con usage_rollups en la misma transaccion que close_run, y retencion de dispatches que n…"]
    spawn_023_senales_de_consumo_b3_ventana_y_rollup_2["SPAWN-002 implementer Schema 8 con usage_rollups y retencion de dispatches -- relanzado en codex tras limite de sesion …"]
    spawn_023_senales_de_consumo_b3_ventana_y_rollup_3["SPAWN-003 package-reviewer Review independiente de B3: la migracion no pierde datos y la retencion no borra evidencia #91;…"]
    spawn_023_senales_de_consumo_b3_ventana_y_rollup_4["SPAWN-004 repair-agent Reparacion consolidada de los seis hallazgos de B3, dos criticos de perdida de evidencia #91;opus#93;"]
    spawn_023_senales_de_consumo_b3_ventana_y_rollup_5["SPAWN-005 delta-reviewer Delta review de la reparacion de los seis hallazgos de B3, dos criticos de perdida de evidenci…"]
  end
  subgraph sg_023_senales_de_consumo_b4_estimado_nunca_dato_del_proveedor["B4-estimado-nunca-dato-del-proveedor"]
    package_023_senales_de_consumo_b4_estimado_nunca_dato_del_proveedor_1["package: B4-estimado-nunca-dato-del-proveedor"]
    spawn_023_senales_de_consumo_b4_estimado_nunca_dato_del_proveedor_1["SPAWN-001 implementer Que ningun numero estimado viaje sin su base, su ventana y su cobertura, y que sin presupuesto no…"]
  end
end
review_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|produjo| finding_023_senales_de_consumo_b3_ventana_y_rollup_1
review_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|produjo| finding_023_senales_de_consumo_b3_ventana_y_rollup_2
review_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|produjo| finding_023_senales_de_consumo_b3_ventana_y_rollup_3
review_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|produjo| finding_023_senales_de_consumo_b3_ventana_y_rollup_4
review_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|produjo| finding_023_senales_de_consumo_b3_ventana_y_rollup_5
review_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|produjo| finding_023_senales_de_consumo_b3_ventana_y_rollup_6
verification_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|verificó| finding_023_senales_de_consumo_b3_ventana_y_rollup_1
verification_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|verificó| finding_023_senales_de_consumo_b3_ventana_y_rollup_2
verification_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|verificó| finding_023_senales_de_consumo_b3_ventana_y_rollup_3
verification_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|verificó| finding_023_senales_de_consumo_b3_ventana_y_rollup_4
verification_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|verificó| finding_023_senales_de_consumo_b3_ventana_y_rollup_5
verification_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|verificó| finding_023_senales_de_consumo_b3_ventana_y_rollup_6
repair_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|reparó| finding_023_senales_de_consumo_b3_ventana_y_rollup_1
repair_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|reparó| finding_023_senales_de_consumo_b3_ventana_y_rollup_2
repair_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|reparó| finding_023_senales_de_consumo_b3_ventana_y_rollup_3
repair_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|reparó| finding_023_senales_de_consumo_b3_ventana_y_rollup_4
repair_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|reparó| finding_023_senales_de_consumo_b3_ventana_y_rollup_5
repair_023_senales_de_consumo_b3_ventana_y_rollup_1 -->|reparó| finding_023_senales_de_consumo_b3_ventana_y_rollup_6
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
