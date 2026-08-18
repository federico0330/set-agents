# 032 — Cursor como runtime del harness

## Problema

El harness genera artefactos nativos para cuatro runtimes (`opencode`, `claude-code`, `codex`, `pi`).
Cursor no está entre ellos: abrir un proyecto en Cursor deja al agente sin roles, sin skills y sin
la doctrina del harness. Federico pagó Cursor precisamente porque las cuotas de los otros tres se
agotaron, así que hoy el runtime disponible es el único que el harness no sabe configurar.

## Fuente (verificada 2026-08-18, docs oficiales de Cursor)

- Subagentes: archivos `.md` con frontmatter YAML en `.cursor/agents/` (proyecto) y `~/.cursor/agents/`
  (global). Campos: `name`, `description`, `model` (default `inherit`), `readonly`, `is_background`.
  <https://cursor.com/docs/subagents>
- Skills: `SKILL.md` dentro de `~/.cursor/skills/<nombre>/` (global) y `.cursor/skills/` (proyecto).
  <https://cursor.com/help/customization/skills>
- Reglas de proyecto: `.cursor/rules/*.mdc`, frontmatter `alwaysApply` / `description` / `globs`.
  `AGENTS.md` en la raíz del proyecto también se lee. <https://cursor.com/docs/context/rules>
- Slash commands: **solo a nivel proyecto**, `.cursor/commands/`. No hay soporte global hoy.
- Hooks: `~/.cursor/hooks.json` y `<proyecto>/.cursor/hooks.json`, contrato JSON por stdin/stdout.
  <https://cursor.com/docs/hooks>

## Alcance

Cursor entra como **runtime anfitrión**, no como lane de ruteo. No se le asigna modelo desde
`models.toml`: cada subagente hereda el modelo que el usuario eligió en Cursor. Esa es una decisión
explícita — inventar un catálogo de modelos de Cursor sin poder medirlo sería exactamente el defecto
que ADR-0026 prohíbe, y además es lo que quemó las cuotas en los otros runtimes.

## Criterios de aceptación

- **AC-01** `./build.sh` emite un target `cursor` con un agente por fila de `roles.tsv`, frontmatter
  Cursor válido (`name`, `description`, `model: inherit`) y `readonly: true` exactamente en las
  capabilities de solo lectura (`READ_ONLY` + `release`), nunca en las de escritura.
- **AC-02** Las skills canónicas se emiten como `cursor/skills/<nombre>/SKILL.md`, con el mismo
  contenido que reciben los otros runtimes.
- **AC-03** `install.py --target cursor` instala en `~/.cursor` y su desinstalación revierte, con el
  mismo mecanismo `managed-files.txt` que los otros cuatro targets.
- **AC-04** `./build.sh --check` cubre `cursor`: un drift entre `Global/cursor/` y lo que genera el
  build falla el chequeo, igual que para los otros targets.
- **AC-05** `bootstrap_project.py` deja en el proyecto `.cursor/rules/00-harness.mdc` con
  `alwaysApply: true` — la doctrina del harness entra en cada sesión de Cursor sin acción del
  usuario — y `.cursor/commands/*.md` con los comandos canónicos.
- **AC-06** Ningún id de modelo de Cursor queda escrito en el árbol: todo agente hereda la sesión.
  La pérdida de diversidad de modelo entre escritor y revisor (ADR-0011) queda registrada como
  degradación deliberada, apoyada en que la independencia es primariamente contexto limpio y un
  subagente de Cursor arranca con contexto limpio.
- **AC-07** README e INSTALACION dicen qué recibe Cursor y qué **no**: en esta versión no se instalan
  hooks de evento (`hooks.json`), así que la política de comandos del harness no se aplica en Cursor
  y la superficie que gobierna es la de permisos del propio Cursor.
