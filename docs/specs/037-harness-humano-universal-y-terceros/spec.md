# 037 — Harness humano, universal y listo para terceros

- **Estado:** Shipped (2026-08-24).
- **Modo:** feature · señal `public-contract`.
- **ADRs:** 0068 (nuevo); enmienda parcial 0027; refuerzo 0033.

## Problema

Los bloques `Cliente:` / `Ingeniería:` en el chat suenan a plantilla de harness (ADR-0027). El vocabulario
asume desarrollo de software (`feature`, `package`, `spec`) y no escala a otros encargos sin hardcodear
dominios. La narración duplicada (chat + vault) gasta tokens.

## Alcance

1. **Chat informativo** (ADR-0068): prosa natural en hitos; sin prefijos `Cliente:`/`Ingeniería:` en chat.
2. **Vault intacto:** `record-spawn` / `log-narrative` con `--client`/`--tech`; bitácora y digest siguen.
3. **Metamodelo neutral:** encargo, tanda de trabajo, consulta, arreglo acotado — sin enums de actividad.
4. **Tokens:** tope ~8 líneas por hito en chat; leer notas/digest antes de specs completos.
5. **Terceros:** TIPS + COMO-FUNCIONA describen chat vs vault.

## Fuera de alcance

- Renombrar CLI `--client`/`--tech`.
- Hardcodear tipos de actividad (escolar, Proteus, …).
- `/explicar` conserva salida dual como comando, no como plantilla de orquestación.

## Criterios de aceptación

- **AC-01:** Plantillas canónicas de chat sin `Cliente:`/`Ingeniería:` obligatorios.
- **AC-02:** Persistencia dual en CLI + bitácora regenerada.
- **AC-03:** ADR-0068 Accepted + enmienda 0027 documentada.
- **AC-04:** Tests narración/harness verdes.
- **AC-05:** `request-triage` vocabulary domain-neutral; cero enums de actividad.
- **AC-06:** `./build.sh --check` verde.
- **AC-07:** TIPS + COMO-FUNCIONA sección chat vs vault.
- **AC-08:** ADR-0068 cita recorte medido de líneas de plantilla (antes/después).

## Paquetes

- **P1:** Doctrina + ADR-0068
- **P2:** Tests + lint compat 028
- **P3–P5:** Triage neutral, tokens, terceros
