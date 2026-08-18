# 033-menos-espera-menos-cuota · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_033_menos_espera_menos_cuota["033-menos-espera-menos-cuota"]
  feature_033_menos_espera_menos_cuota_1["feature: 033-menos-espera-menos-cuota"]
  subgraph sg_033_menos_espera_menos_cuota_pkg_1["PKG-1"]
    package_033_menos_espera_menos_cuota_pkg_1_1["package: PKG-1"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_2["PKG-2"]
    package_033_menos_espera_menos_cuota_pkg_2_1["package: PKG-2"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_3["PKG-3"]
    package_033_menos_espera_menos_cuota_pkg_3_1["package: PKG-3"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_4["PKG-4"]
    package_033_menos_espera_menos_cuota_pkg_4_1["package: PKG-4"]
    spawn_033_menos_espera_menos_cuota_pkg_4_1["SPAWN-001 package-planner escribir context packs de los 6 paquetes y persistir --context-pack#59; PKG-4 es el primero a im…"]
    spawn_033_menos_espera_menos_cuota_pkg_4_2["SPAWN-002 implementer implementar AC-4.1 a AC-4.4 en un solo paquete#59; AC-4.5 CI SHA queda para el cierre con jobs #91;inhe…"]
    spawn_033_menos_espera_menos_cuota_pkg_4_3["SPAWN-003 gate-runner gates de cierre PKG-4: check-owned-paths, build.sh --check, verify.sh, git diff --check #91;inherit#93;"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_5["PKG-5"]
    package_033_menos_espera_menos_cuota_pkg_5_1["package: PKG-5"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_6["PKG-6"]
    package_033_menos_espera_menos_cuota_pkg_6_1["package: PKG-6"]
  end
end
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
