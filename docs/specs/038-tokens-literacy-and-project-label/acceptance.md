# 038 — Criterios de aceptación (BDD)

## AC-01 — project_label

**Given** `set-agents --project-label "Acme Labs"`  
**When** `feature-state.py sync-notes`  
**Then** el hub se titula `# Acme Labs — notas`; vacío restaura el nombre del directorio.

## AC-02 — doctrina por capas

**Given** AGENTS always-on (excepto pi)  
**When** se cuenta líneas y se busca ADR-0069  
**Then** techo 90/100 y puntero a `orchestrator.md`; Turn continuity sigue en AGENTS.md.

## AC-03 — alfabetismo de código

**Given** `orchestrator.md` y `architect.md`  
**When** se planifica o se cierra un hito  
**Then** hay función madre, flujo, pseudocódigo y `file:line`.

## AC-04 — sesiones por encargo

**Given** `cost-report.py --project DIR` con spawn records  
**When** se imprime el reporte  
**Then** tabla per encargo con conteo de sesiones y la frase de que los tokens no están en esos records.

## AC-05 — generate coherente

**Given** `./build.sh --check`  
**When** corre  
**Then** verde.
