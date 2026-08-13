# 022-disponibilidad-real · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_022_disponibilidad_real["022-disponibilidad-real"]
  feature_022_disponibilidad_real_1["feature: 022-disponibilidad-real"]
  subgraph sg_022_disponibilidad_real_p1_registro_de_proveedores["P1-registro-de-proveedores"]
    package_022_disponibilidad_real_p1_registro_de_proveedores_1["package: P1-registro-de-proveedores"]
    finding_022_disponibilidad_real_p1_registro_de_proveedores_1["P1-F01 #40;critical#41; verified_by=orchestrator"]
    finding_022_disponibilidad_real_p1_registro_de_proveedores_2["P1-F02 #40;high#41; verified_by=orchestrator"]
    review_022_disponibilidad_real_p1_registro_de_proveedores_1["repair_required #40;orchestrator#41;"]
    verification_022_disponibilidad_real_p1_registro_de_proveedores_1["verified_by=orchestrator"]
    repair_022_disponibilidad_real_p1_registro_de_proveedores_1["1 changed files"]
    spawn_022_disponibilidad_real_p1_registro_de_proveedores_1["SPAWN-001 implementer Implementar ADR-0042: un unico registro PROVIDERS del que se derivan las tablas de proveedores #91;o…"]
    spawn_022_disponibilidad_real_p1_registro_de_proveedores_2["SPAWN-002 package-reviewer Review independiente de P1: derivacion real, contrato de orden, honestidad del ADR y mordida…"]
    spawn_022_disponibilidad_real_p1_registro_de_proveedores_3["SPAWN-003 repair-agent Reparacion consolidada de P1-F01 y P1-F02: dos guardas que pasan en verde con el registro roto #91;…"]
    spawn_022_disponibilidad_real_p1_registro_de_proveedores_4["SPAWN-004 delta-reviewer Delta review de la reparacion de P1-F01 y P1-F02 #91;gpt-5.6-terra#93;"]
  end
  subgraph sg_022_disponibilidad_real_p2_techo_catalogo_tri_estado["P2-techo-catalogo-tri-estado"]
    package_022_disponibilidad_real_p2_techo_catalogo_tri_estado_1["package: P2-techo-catalogo-tri-estado"]
    spawn_022_disponibilidad_real_p2_techo_catalogo_tri_estado_1["SPAWN-001 implementer Implementar el techo #91;catalog#93; tri-estado: lista = techo curado, #91;#93; = veto, ausente = auto #91;opus#93;"]
    spawn_022_disponibilidad_real_p2_techo_catalogo_tri_estado_2["SPAWN-002 package-reviewer Review independiente de P2: tri-estado real, las cuatro capas, el error nombrado y el cache …"]
  end
  subgraph sg_022_disponibilidad_real_p3_liveness_real["P3-liveness-real"]
    package_022_disponibilidad_real_p3_liveness_real_1["package: P3-liveness-real"]
    finding_022_disponibilidad_real_p3_liveness_real_1["P3-F01 #40;critical#41; verified_by=orchestrator"]
    finding_022_disponibilidad_real_p3_liveness_real_2["P3-F02 #40;high#41; verified_by=orchestrator"]
    finding_022_disponibilidad_real_p3_liveness_real_3["P3-F03 #40;critical#41; verified_by=orchestrator"]
    review_022_disponibilidad_real_p3_liveness_real_1["delta: repair_required"]
    review_022_disponibilidad_real_p3_liveness_real_2["repair_required #40;package-reviewer#41;"]
    verification_022_disponibilidad_real_p3_liveness_real_1["verified_by=orchestrator"]
    verification_022_disponibilidad_real_p3_liveness_real_2["verified_by=orchestrator"]
    repair_022_disponibilidad_real_p3_liveness_real_1["2 changed files"]
    repair_022_disponibilidad_real_p3_liveness_real_2["2 changed files"]
    spawn_022_disponibilidad_real_p3_liveness_real_1["SPAWN-001 implementer Implementar liveness real: firma de credencial por runtime en la clave de cache, y una sola cache…"]
    spawn_022_disponibilidad_real_p3_liveness_real_2["SPAWN-002 package-reviewer Review independiente de P3, clase security: filtracion, la trampa del mcpOAuth, las dos prop…"]
    spawn_022_disponibilidad_real_p3_liveness_real_3["SPAWN-003 repair-agent Reparacion consolidada de P3-F01 #40;critical#41; y P3-F02 #40;high#41;: fail-open en las firmas de credenci…"]
    spawn_022_disponibilidad_real_p3_liveness_real_4["SPAWN-004 delta-reviewer Delta review de la reparacion de P3-F01 y P3-F02 #91;gpt-5.6-terra#93;"]
    spawn_022_disponibilidad_real_p3_liveness_real_5["SPAWN-005 repair-agent Segunda reparacion de P3: P3-F03, la cuarta guarda falsa-verde de la feature #91;opus#93;"]
    spawn_022_disponibilidad_real_p3_liveness_real_6["SPAWN-006 delta-reviewer Delta review final de P3: cierre de P3-F03, ultimo ciclo disponible #91;gpt-5.6-terra#93;"]
  end
  subgraph sg_022_disponibilidad_real_p4_proveedores_del_usuario["P4-proveedores-del-usuario"]
    package_022_disponibilidad_real_p4_proveedores_del_usuario_1["package: P4-proveedores-del-usuario"]
    spawn_022_disponibilidad_real_p4_proveedores_del_usuario_1["SPAWN-001 implementer Administrar proveedores propios desde set-agents, sin editar JSON, y que quitar funcione de verda…"]
    spawn_022_disponibilidad_real_p4_proveedores_del_usuario_2["SPAWN-002 package-reviewer Review independiente de P4: que quitar funcione, que la poda no borre lo ajeno, y el desvio …"]
  end
  subgraph sg_022_disponibilidad_real_p5_altas_y_bajas_automaticas["P5-altas-y-bajas-automaticas"]
    package_022_disponibilidad_real_p5_altas_y_bajas_automaticas_1["package: P5-altas-y-bajas-automaticas"]
    spawn_022_disponibilidad_real_p5_altas_y_bajas_automaticas_1["SPAWN-001 implementer Altas y bajas automaticas: verificacion empirica del CLI id, baja simetrica, --provider-verify y …"]
    spawn_022_disponibilidad_real_p5_altas_y_bajas_automaticas_2["SPAWN-002 package-reviewer Review independiente de P5: verificacion empirica fail-closed, liveness honesta y las tres s…"]
  end
end
review_022_disponibilidad_real_p1_registro_de_proveedores_1 -->|produjo| finding_022_disponibilidad_real_p1_registro_de_proveedores_1
review_022_disponibilidad_real_p1_registro_de_proveedores_1 -->|produjo| finding_022_disponibilidad_real_p1_registro_de_proveedores_2
verification_022_disponibilidad_real_p1_registro_de_proveedores_1 -->|verificó| finding_022_disponibilidad_real_p1_registro_de_proveedores_1
verification_022_disponibilidad_real_p1_registro_de_proveedores_1 -->|verificó| finding_022_disponibilidad_real_p1_registro_de_proveedores_2
repair_022_disponibilidad_real_p1_registro_de_proveedores_1 -->|reparó| finding_022_disponibilidad_real_p1_registro_de_proveedores_1
repair_022_disponibilidad_real_p1_registro_de_proveedores_1 -->|reparó| finding_022_disponibilidad_real_p1_registro_de_proveedores_2
review_022_disponibilidad_real_p3_liveness_real_1 -->|produjo| finding_022_disponibilidad_real_p3_liveness_real_3
review_022_disponibilidad_real_p3_liveness_real_2 -->|produjo| finding_022_disponibilidad_real_p3_liveness_real_1
review_022_disponibilidad_real_p3_liveness_real_2 -->|produjo| finding_022_disponibilidad_real_p3_liveness_real_2
verification_022_disponibilidad_real_p3_liveness_real_1 -->|verificó| finding_022_disponibilidad_real_p3_liveness_real_1
verification_022_disponibilidad_real_p3_liveness_real_1 -->|verificó| finding_022_disponibilidad_real_p3_liveness_real_2
verification_022_disponibilidad_real_p3_liveness_real_2 -->|verificó| finding_022_disponibilidad_real_p3_liveness_real_3
repair_022_disponibilidad_real_p3_liveness_real_1 -->|reparó| finding_022_disponibilidad_real_p3_liveness_real_1
repair_022_disponibilidad_real_p3_liveness_real_1 -->|reparó| finding_022_disponibilidad_real_p3_liveness_real_2
repair_022_disponibilidad_real_p3_liveness_real_2 -->|reparó| finding_022_disponibilidad_real_p3_liveness_real_3
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
