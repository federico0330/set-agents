# Feature 004 — spec challenge (dos rondas)

## Ronda 1 (contract 1.0.0) — needs-rework

Spec-challenger independiente (read-only), 9 bloqueantes + 12 menores. Núcleo: la 004 relajaba dos
invariantes de la 003 sin registrarlo (origen de facts B1, frescura de probes B2), el valor prometido no
era testeable (B4), P2 podía romper la identidad durable (B5) y P3 apoyaba en incógnitas de Pi (B7).

Cuatro bloqueantes eran decisiones de producto; el usuario decidió el 2026-07-26 (persistido en
`decisions-log`, slugs `am1-hybrid-facts`, `am2-probe-cache-fresh-selected`,
`scope-cheap-tier-and-pi-spike`):

- **B1 → AM-1**: derivación híbrida; el descriptor aporta `task_class`; risk solo puede subir la base
  derivada.
- **B2 → AM-2**: cache de probes filtering-only (TTL 300s, clave uid+digest+par) + re-probe fresco del
  par seleccionado antes de autorizar writers; ADR-0006 antes de P1.
- **B5**: tier fast solo con proveedores auditados; `opencode/*` (Zen/Go) difiere a feature futura.
- **B7**: P3 condicionado al spike T-300 (evidencia binaria; cualquier NO ⇒ HUMAN_DECISION_REQUIRED).

## Ronda 2 (contract 1.1.0, delta) — approve-with-edits

B2/B7/B8/B9 y 11 de los 12 menores: resolved. Residuos mecánicos NEW-1..NEW-9 + m3, todos aplicados al
texto (misma fecha):

1. NEW-1: cierre `authorized → abandoned` como estado terminal nuevo, `SCHEMA` 3→4, doctrina de wipe del
   operador en Non-goals.
2. NEW-2: reviewers ruteados SOLO con `review_of_run_id` verificado; `--routing-recent-writers` como
   fuente del run_id terminal; decisión no ejecutable jamás selecciona variante.
3. NEW-3: gate de coherencia = proyección pura offline (full-inventory assumption); doctrine matchea por
   MODELO decidido; mismatch ⇒ abandono del run + modo degradado con agente base.
4. NEW-4: `runtimes` opcional allowlisted; fuera de la tupla canónica del ID; duplicados que solo
   difieren en `runtimes` siguen `CATALOG_INVALID`.
5. NEW-5: tier codificado como grupo de un elemento (contrato de ID de la 003 sin tercera enmienda).
6. NEW-6: descriptor con `feature_id`/`package_id` (default: feature/paquete activo) para derivar los
   context flags; sin paquete resoluble ⇒ flags false conservador.
7. NEW-7: latencia honesta de writers en proposal.md.
8. m3: `catalog_version` 1→2, validado y hasheado.
9. NEW-8/NEW-9: allowlists de reasons/data + set de modos extendido; variantes aditivas OpenCode-only con
   agente base intacto.

Estado: contract 1.1.0 listo para USER_APPROVAL.
