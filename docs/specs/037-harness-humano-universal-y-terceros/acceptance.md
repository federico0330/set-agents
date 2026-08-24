# 037 — Criterios de aceptación (BDD)

## AC-01 — Chat sin registros etiquetados

**Given** `Global/_canonical/agents/orchestrator.md` y twins generados  
**When** se buscan plantillas de hito en chat  
**Then** no hay líneas `Cliente:` ni `Ingeniería:` como prefijos obligatorios; sí `ADR-0068`.

## AC-02 — Vault persiste auditoría

**Given** un `log-narrative` con `--client` y `--tech`  
**When** se renderiza bitácora  
**Then** aparecen campos Cliente/Ingeniería en **archivo**, no exigidos en chat.

## AC-04 — Tests verdes

**Given** `tests/test_narracion_contrato.py` y `tests/test_harness.py`  
**When** corre la suite  
**Then** verde con nuevo contrato.

## AC-05 — Vocabulario neutral

**Given** `request-triage/SKILL.md`  
**When** se lee intake  
**Then** tabla encargo/tanda/consulta/arreglo; sin lista cerrada de dominios.

## AC-07 — Docs terceros

**Given** `TIPS-USO.md` y `docs/COMO-FUNCIONA.md`  
**When** usuario nuevo lee  
**Then** sección "Cómo te habla el harness" + puntero a Obsidian.
