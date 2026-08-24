# 038 — Tokens, alfabetismo de código y etiqueta de proyecto

- **Estado:** Shipped (pedido Federico 2026-08-24: filas 1/2/4/5 del punto 7 post-037 + lectura de código como compañero).
- **Modo:** scoped · señal `public-contract`.
- **ADRs:** 0069 (nuevo). Relaciona 0068 (chat), 0026 (evidencia), 0020 (lectura), 0011 (continuidad en AGENTS.md).

## Problema

El vibe coding pierde la noción de qué hace el software. El always-on (AGENTS.md / 00-harness) duplica prosa que ya vive en `orchestrator.md`. No hay etiqueta libre para el hub. `cost-report` no agrupa sesiones por encargo. Las plantillas pueden volver a inflarse.

## Alcance

1. **`project_label`** en `config.toml` (string libre, sin enum de dominio) para el título del hub.
2. **Doctrina por capas (ADR-0069):** always-on = invariantes + puntero; protocolo de coordinación (plantillas de hito, spawn economy, alfabetismo de código completo) en `orchestrator.md`. OpenCode/Claude/Codex **conservan** Turn continuity / Question policy / Human decision en AGENTS.md (ADR-0011: una sesión sin spawn de orchestrator igual las necesita). Pi sigue siendo el archivo gordo (orquestador por defecto).
3. **Test de techo** de líneas en AGENTS always-on (excepto `AGENTS.pi.md`).
4. **`cost-report` por encargo:** conteo de sesiones `record-spawn` por `feature_id`. Tokens en spawn records siguen ausentes — no inventarlos (023).
5. **Alfabetismo de código:** planificar con flujo + pseudocódigo de la **función madre**; devoluciones con `file:line`; no alucinar APIs (ADR-0026).

## Fuera de alcance

- Renombrar `--client`/`--tech`.
- Mover Turn continuity fuera de AGENTS.md de OpenCode/Claude/Codex.
- Inventar tokens por encargo desde spawn JSON.

## Criterios

- **AC-01** `--project-label` persiste; hub usa esa etiqueta; vacío = nombre de directorio.
- **AC-02** Always-on cita ADR-0069 y carga orchestrator para coordinación; techo de líneas en test.
- **AC-03** `orchestrator.md` + `architect.md` exigen función madre / flujo / pseudocódigo / `file:line`.
- **AC-04** `cost-report --project` imprime sesiones por encargo y la frase de que los tokens no están en spawn records.
- **AC-05** `./build.sh --check` verde.

## ## Supersedes

- none (doctrina aditiva; 0011/0068 intactos en su ámbito)
