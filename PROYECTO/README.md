# PROYECTO — esqueleto para instanciar el harness en un repo

Copiá lo que necesites de esta carpeta a la raíz de tu repo. Mínimo recomendado:

```
AGENTS.md                      # reglas del proyecto (editá los placeholders)
docs/specs/<id>/{spec,plan,tasks,acceptance}.md
docs/adr/0001-*.md
docs/ai/memory-log.md
ai/scripts/{verify.sh,audit-readonly.sh,loop.sh}   # deterministic gates and optional worker loop
ai/scripts/{feature-state.py,check-owned-paths.py} # package workflow state and ownership gates
```

## Overrides locales (opcional)
- `.opencode/agents/<nombre>.md` — agente de dominio específico del repo (mismo formato que los globales).
- `.opencode/skills/<nombre>/SKILL.md` — skill de dominio (reglas de negocio del cliente).
- `.claude/agents/…` y `.codex/…` — equivalentes por harness.
Los globales siguen disponibles; lo local tiene más precedencia dentro del repo.

## Uso rápido
1. Editá `AGENTS.md` (dominio, invariantes, stack, comandos de test/lint/build).
2. Reflejá tu stack en `ai/scripts/verify.sh`.
3. `chmod +x ai/scripts/*.sh`.
4. En OpenCode: `/feature-batch <idea>`.
5. Cerrá y aprobá la spec; después el orquestador registra paquetes en `ai/state/features/<feature_id>.json`.
6. Cada tarea del paquete corre validaciones locales. La auditoría profunda se ejecuta una vez sobre el paquete
   integrado mediante un panel liderado por `package-reviewer`; el orquestador convoca los especialistas que
   correspondan y registra todo como una sola iteración.
7. Después de la reparación consolidada y `delta-reviewer`, se corren regression/integration tests y QA runtime
   con app levantada/navegador cuando aplique.
8. **Agente en el loop**: pegá `prompt.md` como primer mensaje si no usás comandos. La IA orquesta el package
   workflow y sólo para en cortes duros.

Comandos útiles:

```bash
python3 ai/scripts/feature-state.py status <feature_id>
python3 ai/scripts/feature-state.py next <feature_id>
python3 ai/scripts/feature-state.py dry-run smoke-package-flow
python3 ai/scripts/check-owned-paths.py --state-file ai/state/features/<feature_id>.json --package-id PKG-01 --baseline HEAD
```

> Regla de oro: lo que implementa NO aprueba. Modelos baratos implementan; modelos capaces diseñan y auditan.
> El estado vive en archivos, no en el chat.
