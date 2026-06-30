# PROYECTO — esqueleto para instanciar el harness en un repo

Copiá lo que necesites de esta carpeta a la raíz de tu repo. Mínimo recomendado:

```
AGENTS.md                      # reglas del proyecto (editá los placeholders)
docs/specs/<id>/{spec,plan,tasks,acceptance}.md
docs/adr/0001-*.md
docs/ai/memory-log.md
ai/scripts/{verify.sh,audit-readonly.sh,loop.sh}   # chmod +x
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
4. En OpenCode: `/sdd-start <idea>` → `/next-task T-001` → `@auditor` / `@db-auditor` según el gate.
5. O loop automático: `./ai/scripts/loop.sh T-001 4`.
6. **Agente en el loop**: pegá `prompt.md` como primer mensaje y la IA orquesta el loop sola
   (para solo en cortes duros o para pedirte encender un MCP).

> Regla de oro: lo que implementa NO aprueba. Modelos baratos implementan; modelos capaces diseñan y auditan.
> El estado vive en archivos, no en el chat.
