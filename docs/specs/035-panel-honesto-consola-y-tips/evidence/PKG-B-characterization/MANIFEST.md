# PKG-B characterization MANIFEST

**Sealed:** 2026-08-20
**git HEAD:** `788eb6207e5ccaca7c7a73642eb7f17f58e275bd`
**CLI entry:** `python3 ai/scripts/set_agents_app.py`

| case-id | group | argv | isolation | dry-run |
|---|---|---|---|---|
| `global-help` | global | `--help` | plain | False |
| `global-no-args` | global | `(no args)` | plain | False |
| `estado-valid` | estado | `--status` | plain | False |
| `estado-missing-arg` | estado | `--model-pin-set role` | plain | False |
| `estado-invalid` | estado | `--harness invalid` | plain | False |
| `routing-valid` | routing | `--routing-report --json` | disposable | False |
| `routing-missing-arg` | routing | `--route-explain` | plain | False |
| `routing-invalid` | routing | `--route-terminal run1_bad not-an-outcome` | disposable | False |
| `routing-route-decide` | routing | `--route-decide -` | declared-uncharacterizable | False |
| `routing-route-dispatched` | routing | `--route-dispatched run1_test` | disposable | False |
| `routing-route-terminal` | routing | `--route-terminal run1_test success` | disposable | False |
| `routing-route-quota-exhausted` | routing | `--route-quota-exhausted run1_test --quota-error {} --latency-ms 1` | disposable | False |
| `routing-fresh-probes` | routing | `--fresh-probes` | declared-uncharacterizable | False |
| `vault-valid` | vault | `--vault-doctor --dry-run` | disposable | True |
| `vault-missing-arg` | vault | `--vault-link` | plain | False |
| `vault-invalid` | vault | `--vault-doctor --repair` | disposable | False |
| `instalacion-valid` | instalacion | `--check-update` | disposable | False |
| `instalacion-missing-arg` | instalacion | `--auto-update` | plain | False |
| `instalacion-invalid` | instalacion | `--auto-update maybe` | plain | False |
| `herramientas-valid` | herramientas | `--tools` | disposable | False |
| `herramientas-missing-arg` | herramientas | `--tools-install` | plain | False |
| `herramientas-invalid` | herramientas | `--mcp-add` | plain | False |
| `proveedores-valid` | proveedores | `--provider-list` | disposable | False |
| `proveedores-missing-arg` | proveedores | `--provider-add` | plain | False |
| `proveedores-invalid` | proveedores | `--provider-add badid` | plain | False |
| `posturas-valid` | posturas | `--posturas` | disposable | False |
| `posturas-missing-arg` | posturas | `--model-preference-role-override role` | plain | False |
| `posturas-invalid` | posturas | `--postura invalid` | plain | False |
| `mutant-vault-init` | vault | `--vault-init company` | disposable | False |
| `mutant-vault-link` | vault | `--vault-link proj --vault vault/obsidian` | disposable | False |
| `mutant-scaffold` | instalacion | `--scaffold` | disposable | False |
| `mutant-update-dry-run` | instalacion | `--update --dry-run` | disposable | True |
| `mutant-tools-install` | herramientas | `--tools-install nonexistent-tool-xyz --dry-run` | disposable | True |
| `mutant-mcp-add` | herramientas | `--mcp-add brave-search --harness cursor` | disposable | False |
| `mutant-mcp-remove` | herramientas | `--mcp-remove brave-search --harness cursor` | disposable | False |
| `mutant-provider-add` | proveedores | `--provider-add testprov --base-url https://example.invalid/v1 --dry-run` | disposable | True |
| `mutant-provider-remove` | proveedores | `--provider-remove nonexistent-id` | disposable | False |
| `mutant-plugin-on` | herramientas | `--plugin-on frontend-design` | disposable | False |
| `mutant-plugin-off` | herramientas | `--plugin-off frontend-design` | disposable | False |
| `mutant-model-pin-set` | posturas | `--model-pin-set implementer cursor/composer-2.5` | disposable | False |
| `mutant-model-pin-clear` | posturas | `--model-pin-clear implementer` | disposable | False |
| `mutant-routing-migrate` | routing | `--routing-migrate` | disposable | False |
| `mutant-prune-dead` | proveedores | `--provider-verify --prune-dead` | disposable | False |
| `mutant-provider-verify` | proveedores | `--provider-verify` | disposable | False |
| `mutant-quota-failover-e2e` | routing | `--quota-failover-e2e` | disposable | False |
