# Propuesta ejecutiva — Índice honesto de especificaciones

## Problema

El registro de features del harness no refleja qué contratos siguen vigentes. Un agente puede citar
requerimientos de features ya entregadas como si fueran mandato actual, y la tabla índice está incompleta.

## Solución

Documentar una regla clara de precedencia (código y ADRs primero; specs cerrados son histórico), completar
el índice de specs, marcar supersession parcial donde corresponde, y automatizar un test que impida que el
índice vuelva a quedar desactualizado.

## Alcance

- Doctrina en archivos que el agente ya lee al iniciar.
- Tabla índice completa y alineada al tablero de proyecto.
- Aviso en spec 032 sin alterar su contenido original.
- ADR formal + test de regresión.

## Fuera de alcance

Reescribir specs antiguos, nuevas herramientas CLI, ni reabrir features bloqueadas.

## Éxito medible

- Test verde que valida índice vs disco y features DONE.
- `./build.sh --check` verde.
- Orquestador con precedencia explícita en un solo lugar canónico.

## Esfuerzo

Pequeño (un paquete, documentación + un test).
