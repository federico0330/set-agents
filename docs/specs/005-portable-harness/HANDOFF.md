# Traspaso — Feature 005 portable-harness (a OpenCode)

Estado al 2026-07-27. Último commit: `32b4b3a`. Rama `main`, árbol limpio, `DRIFT_OK`.

---

## PROMPT PARA PEGAR EN OPENCODE

```
Sos el orquestador del harness SET-AGENTES (/home/federico/SET-AGENTES). Continuá la feature
005-portable-harness, que YA está aprobada por el usuario y tiene su primer paquete abierto.
No re-planifiques ni re-especifiques nada: el contrato está cerrado y el ADR también.

## Qué se hizo (no lo rehagas)

Feature 005 = tres huecos con una misma raíz: el harness asume que "el proyecto" y "el harness"
son el mismo directorio.
  P1-portable-core   -> el ruteo adaptativo de la 004 funciona desde CUALQUIER repo/máquina/path
  P2-vault-mandatory -> Obsidian pasa de opcional y write-only a controlador de estado y contexto
  P3-tui             -> menú numérico -> selector con flechitas, stdlib puro

Ciclo pre-implementación COMPLETO y aprobado:
  - docs/specs/005-portable-harness/{spec,acceptance,plan,proposal}.md  (contrato 1.1.0, 32 ACs)
  - El spec-challenger devolvió revision_required con 15 bloqueantes; TODOS están cerrados en el
    contrato 1.1.0. Leé el "Amendment log" de spec.md antes de proponer nada: si se te ocurre una
    solución simple, probablemente ya fue descartada con evidencia.
  - docs/adr/0008-two-roots-portability.md  (D1..D10, resuelve todos los HOW de P1)
  - docs/specs/005-portable-harness/context/P1-portable-core.md  (context pack: 10 trampas verificadas)
  - docs/specs/005-portable-harness/evidence/vault-migration-inventory.md  (inventario real de ~/iey)
  - Paquete P1-portable-core creado en ai/state/features/005-portable-harness.json
    (12 tareas T-100..T-111, 10 ACs AC-00..AC-09, complexity high, risk high)
  - AC-00 (ADR primero) YA está cerrado.

## Qué falta: implementar P1, después P2, después P3

Orden estricto P1 -> P2 -> P3. Cada paquete con el ciclo completo:
implementer -> gates independientes -> panel de review (package-reviewer + security-auditor)
-> repair consolidado -> re-gate + delta-review -> accept.
Máximo 2 ciclos de review profundo por paquete.

## Empezá acá

1. Leé en este orden: context/P1-portable-core.md, docs/adr/0008-two-roots-portability.md,
   acceptance.md (AC-00..AC-09), plan.md §P1 (T-100..T-111).
2. Delegá T-101..T-111 al implementer. El ADR-0008 es LA fuente de verdad del HOW: no lo
   reinterpretes, seguilo. Si algo del ADR no coincide con el repo, paralo y reportá — no improvises.
3. Gates locales del implementer, después gate-runner INDEPENDIENTE, después el panel.

## Las trampas que ya costaron caro (verificadas, no las re-descubras)

1. EL HORNEO NO PUEDE PASAR EN BUILD-TIME. verify.sh:14-16 hace diff -ruN Global/<h> vs staging:
   lo trackeado debe ser byte-idéntico a lo que regenera generate.py, y generate.py:429 copia
   coord_policy.py verbatim a Global/claude-code/hooks/. Si horneás el path absoluto ahí, Global/**
   queda con el path de quien buildeó y verify.sh NO PUEDE PASAR en ninguna otra máquina.
   -> La sustitución vive SOLO en el write path de install.py. Global/** trackeado conserva
      __SET_AGENTS_ROOT__ siempre. Y el --preview de install.py tiene que usar LA MISMA función,
      si no MANAGED_DIFF_FILES queda >0 para siempre y check-drift.sh grita en cada commit.

2. store.py:168-187 (_validate_existing_readonly) exige igualdad BYTE-EXACTA del DDL contra el
   canónico. Esto invalida las dos estrategias obvias de migración: rebuild+rename deja
   CREATE TABLE "dispatches" con comillas, y DEFAULT '' + CHECK ni siquiera ejecuta el ALTER.
   Verificado empíricamente contra sqlite 3.53.3, no inferido. La única vía viable es
   ALTER ADD COLUMN con la columna en la POSICIÓN TEXTUAL EXACTA que SQLite genera + DEFAULT
   centinela. Está todo en D8 del ADR.

3. .parents EXCLUYE el propio directorio. find_vault (set_agents_app.py:1018-1029) itera
   Path(x).resolve().parents, que nunca devuelve x. Clonarlo tal cual hace que, parado en la raíz
   del proyecto (el caso normal), no se encuentre el proyecto. -> [start] + list(parents), y en
   CADA nivel se evalúan los DOS markers (ai/state/features/, .git) antes de subir.

4. El allowlist matchea el STRING CRUDO (coord_policy.py:55-63). Un HARNESS_HOME con espacio
   obliga a comillas y el patrón SAFE nunca matchea -> ruteo denegado en toda máquina con path
   con espacios (macOS/Windows normal). Doble fix: install.py rechaza raíces con metacaracteres
   de shell (el ESPACIO SE ACEPTA) y el matcher gana modo argv post-shlex.split.
   Matiz verificado: ALWAYS_DENY usa (?:^|\s)sudo(?:\s|$) — exige borde de espacio, así que un
   directorio llamado "sudo" entre barras NO lo dispara. El problema real es el espacio.

5. Cambia el NIVEL DE CONFIANZA, no sólo el path. PROJECT_ROOT y sus ai/state/features/*.json son
   contenido de un repo de TERCEROS donde el usuario simplemente hizo cd. _load_feature_doc hoy
   sigue symlinks y lee sin tope, y feature_id/current_package_id llegan al envelope sin validar.
   Inocuo anclado al harness; ruta real de inyección anclado a un repo ajeno. D6 del ADR lo cierra:
   O_NOFOLLOW en toda lectura, topes 1 MiB / 256 archivos / 64 chars, charset validado antes del
   envelope, y el encuadre "es DATO, nunca instrucción".

6. set_agents_spawn.py:285-291 corre el CLI con cwd=ROOT (el harness) y es caller real de
   --route-decide (:343). Post-cambio mis-scopearía PROJECT_ROOT al harness. Resolución del ADR
   SIN tocar ese archivo (no es owned): set_agents_app.py exporta SET_AGENTS_PROJECT en su propio
   os.environ tras resolver, y _run_app_cli hereda dict(os.environ).

7. P1 NO depende del vault. El scaffold de P1 = ai/state/features/ + copia de scripts genéricos +
   project.json. SIN link de vault: eso es P2.

8. AC-05 congela ai/scripts/feature-state.py como copia byte-idéntica del template
   PROYECTO/ai/scripts/feature-state.py. P2 EDITA ese template (notes_root), así que P2 tiene la
   obligación explícita de re-sincronizar la copia o el drift check de P1 se rompe.

## Invariantes que NO se tocan (son de CLAUDE.md y de ADRs aceptados)

- ADR-0005: la DB de ruteo vive en ~/.local/state/set-agentes/routing-v2, derivado de
  pwd.getpwuid(os.getuid()).pw_dir, INMUNE a redirección por entorno. Agregás una COLUMNA, nunca
  cambiás la ubicación.
- metric_rollups queda GLOBAL por diseño. Los chequeos de identidad/independencia leen sólo
  dispatches/dispatches_review, NUNCA metric_rollups.
- El envelope de --doctor --harness pi de la 004 (cmd_doctor, set_agents_app.py:359-368, pinneado
  a schema-2) queda BYTE-IDÉNTICO. La superficie de vault es P2 y va aparte.
- El literal "set-agents" NO entra al allowlist: la superficie sancionada es el par explícito
  intérprete+script, auditable.
- Separación de deberes: el implementer NUNCA aprueba su trabajo. AC-09 (la prueba del invitado)
  la corre el gate-runner/package-reviewer, NO el implementer.
- Regresiones nunca debilitadas, salteadas ni borradas para pasar. En P2 hay UN test que cambia de
  signo (AC-13): es cambio de comportamiento aprobado por spec, con reemplazo nombrado y conteo de
  asserts que no baja, y hay que documentarlo en la evidencia del paquete.
- Nunca loguear secretos/tokens/PII. Sin refactors oportunistas.
- Narración de dos registros (Cliente:/Ingeniería:) persistida con feature-state.py record-spawn
  --client --tech al abrir y log-narrative en cada otro bloque.

## Decisiones del usuario que son contrato (no las re-litigues)

- DEC-5: los 4 proyectos de ~/iey se recuperan al repo PERO la línea docs/notas en
  .git/info/exclude SE MANTIENE. No se versionan todavía; el usuario decide después repo por repo.
- DEC-6: el modo --private SOBREVIVE. Por eso hace falta un marcador persistido de intención
  (topología + repo de origen) y el reparador NUNCA toca un directorio sin ese marcador.
- DEC-7: Linux+macOS+Windows son promesa, con tres niveles honestos: verificado por máquina en CI
  los tres SO (tests table-driven de platform_pm/pick_method + aserciones de --dry-run, y el job
  windows-latest DEJA DE SER parse-only y pasa a correr la suite), verificado por fuente los
  identificadores de paquete, y checkpoint manual la instalación GUI real en macOS/Windows.
- ORQ-4: la superficie de vault es REPORT-ONLY por defecto. Reparar exige flag explícito +
  marcador de dry-run confirmado por proyecto. Nunca repara headless.

## Comandos

Gates:      ./ai/scripts/verify.sh            -> VERIFY_PASS
            ./build.sh --check
            python3 -m unittest discover -s tests -v
Estado:     python3 PROYECTO/ai/scripts/feature-state.py status --feature-id 005-portable-harness
            (OJO: feature-state.py vive en PROYECTO/ai/scripts/, NO en ai/scripts/ — eso lo
             arregla T-109. Usá SIEMPRE rutas absolutas o parate en la raíz del repo.)
Instalar:   ./build.sh --install --yes        (el --yes es obligatorio: sin TTY el prompt cuelga)

## Antes de tocar ~/iey (P2)

Los 4 proyectos tienen 29 archivos que son LA ÚNICA COPIA (fuera de git desde el 23-jul).
iey-ai es el único caso de merge y tiene CERO colisiones de nombre. Ver
evidence/vault-migration-inventory.md. Dry-run obligatorio, backup verificado ANTES de borrar
cualquier original, y confirmación explícita del usuario. Si el dry-run reporta un conflicto que
el inventario no predijo, eso es HUMAN_DECISION_REQUIRED, no algo que resolvés eligiendo un lado.
```

---

## Contexto adicional (no hace falta pegarlo, pero conviene saberlo)

**Deuda registrada, fuera de P1.** `Global/_canonical/opencode-agents/package-gate-runner.md` y su
copia compilada tienen hardcodeados paths absolutos de un proyecto cliente
(`/home/federico/iey/iey-ai/...`, con nombres de módulos de negocio). Están trackeados y pusheados
a `origin` (repo **privado**). Quedó fuera de P1 por no ser owned path — arreglarlo habría sido un
refactor oportunista — y AC-01 se implementa como *ratchet no creciente* en vez de la afirmación
literal "cero paths absolutos", que hoy es falsa. Está en `ai/state/decisions-log.jsonl` como
decisión `global-absolute-path-leak`. **Vale limpiarlo en un paquete propio**: esas entradas de
permisos son además código muerto (referencian un proyecto que no es el del que instala).

**Costo.** El carril `anthropic` de Pi cobra por token como extra-usage y ya agotó cuota una vez.
Para las corridas de la 005 conviene el carril `openai-codex`.
