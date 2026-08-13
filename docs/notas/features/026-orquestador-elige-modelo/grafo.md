# 026-orquestador-elige-modelo · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_026_orquestador_elige_modelo["026-orquestador-elige-modelo"]
  feature_026_orquestador_elige_modelo_1["feature: 026-orquestador-elige-modelo"]
  subgraph sg_026_orquestador_elige_modelo_p1_latencia_por_modelo_no_por_sufijo["P1-latencia-por-modelo-no-por-sufijo"]
    package_026_orquestador_elige_modelo_p1_latencia_por_modelo_no_por_sufijo_1["package: P1-latencia-por-modelo-no-por-sufijo"]
    spawn_026_orquestador_elige_modelo_p1_latencia_por_modelo_no_por_sufijo_1["SPAWN-001 implementer Sacar la obligacion del sufijo -fast al orquestador y ponerlo en un modelo no-GPT de suscripcion …"]
  end
  subgraph sg_026_orquestador_elige_modelo_p2_modelo_por_instancia["P2-modelo-por-instancia"]
    package_026_orquestador_elige_modelo_p2_modelo_por_instancia_1["package: P2-modelo-por-instancia"]
    spawn_026_orquestador_elige_modelo_p2_modelo_por_instancia_1["SPAWN-001 implementer Preferencia de modelo por instancia en el descriptor de ruteo, sin saltear ninguna barrera #91;opus#93;"]
  end
end
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
