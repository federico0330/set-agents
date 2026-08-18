# Cursor entra como runtime anfitrion, nunca como lane de ruteo

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/032-cursor-como-runtime|032-cursor-como-runtime]]

## Contexto

Federico pago Cursor porque las cuotas de opencode, codex y claude se agotaron. La tentacion era darle a Cursor una fila de modelos en models.toml como a los otros cuatro runtimes. Contra eso hay dos hechos: (a) no hay forma de medir el catalogo de modelos de Cursor desde el harness hoy, y ADR-0026 prohibe escribir en el arbol lo que no se pudo verificar; (b) el ruteo automatico es exactamente el mecanismo que vacio las otras tres cuotas.

## Decisión

Los 28 roles se emiten con 'model: inherit' y validate_cursor_target (ai/scripts/generate.py) mata el build si alguno pinea un id concreto. Cursor no entra en models_config.RUNTIMES ni en routing_core.domain.SELECTED_RUNTIMES: no es lane de despacho.

## Consecuencias

Ningun rol puede gastar una cuota que el usuario no eligio en el selector de Cursor. El costo es que escritor y revisor comparten modelo: la independencia de revision queda apoyada solo en el contexto limpio del subagente, degradacion que CLAUDE.md ya contempla y que debe registrarse en la evidencia de review de cada paquete hecho en Cursor.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
