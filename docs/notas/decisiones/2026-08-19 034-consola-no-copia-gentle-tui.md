# No copiar la TUI de Gentle; SET ya cubre install/update/sync

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator

## Contexto

Comparación de consolas pedida antes de commit+install. Gentle v2.3.0 WelcomeOptions (welcome.go:43-71) y help.go COMMANDS vs SET MENU_ITEMS y cmd_update. Federico usa Obsidian; Engram no-goal.

## Decisión

No se copia Upgrade/Sync separado, agent builder, SDD Profiles, marketplace, brew/curl, cadena de 8 pantallas, ni Engram. SET cmd_update ya es pull+install. Diferidos (no este commit): menú Desinstalar sobre install.py --uninstall, menú --scaffold. Sí se corrige README/INSTALACION que aún decían inherit universal en Cursor.

## Consecuencias

Este commit es 034 + docs humanas alineadas. Uninstall/scaffold de menú quedan para un pedido aparte. install-targets.json tiene los cinco harnesses; no hay otros project.json scaffolded en $HOME.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
