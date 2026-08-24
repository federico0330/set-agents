# PKG-1 — Tokens, literacy, project label

**Objective.** Cap always-on doctrine, add code-literacy protocol, `project_label` hub title, and cost-report sessions per encargo without inventing spawn tokens.

**Mother functions (read, not invented):**

- `write_app_config` (`ai/scripts/set_agents_app.py`) — persist `project_label`
- `render_notes` / `merge_note` (`feature-state.py`, `feature_state_lib/render_notes.py`) — hub title
- `collect_engagements` / `render_engagements` (`ai/scripts/cost-report.py`) — sessions per encargo
- Always-on AGENTS.md + `orchestrator.md` Code literacy — planning/reporting

**Flow (project_label):**

```
CLI --project-label TEXT
  -> sanitize_project_label (collapse ws, max 80)
  -> write_app_config
  -> sync-notes / render_notes
       -> _config_project_label reads config.toml
       -> merge_note rewrites `# … — notas`
```

**Owned paths:** doctrine shared files, orchestrator/architect, set_agents_app, feature-state + render_notes (both trees), cost-report, tests, ADR-0069, spec 038, TIPS, COMO-FUNCIONA.
