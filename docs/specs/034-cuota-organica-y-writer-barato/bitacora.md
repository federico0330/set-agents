# Bitácora — 034-cuota-organica-y-writer-barato

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-19T18:30:21+00:00

[2026-08-19T14:56:09+00:00] orchestrator · done
Cliente: Aprobaste el contrato: el escritor arranca barato, un arreglo caro si falla, y un cambio chico no abre el proceso grande. El contexto sigue en Obsidian, no en Engram.
Ingeniería: USER_APPROVAL 034 hash 539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721. Mode feature. Challenge READY_FOR_USER_APPROVAL after F-034-01/02/03. ADRs 0060-0064 Proposed until this stamp.
Aprendimos: Engram no entra cuando el vault Obsidian ya es mandatory; el challenge bloqueo por HOW (grano de promotion, writer_tier=fast, pin repair pesado), no por recorte.
Conviene ahora: package-planner crea PKG-A..D con context packs; luego implementer PKG-A.
Por qué ahora: Sin plan de paquetes no hay implementacion legal; el context pack es obligatorio al entrar implementacion.
Alternativa: none

[2026-08-19T15:04:59+00:00] PKG-A · implementer · started · spawns 1/12
Cliente: Un arreglo chico ya no puede colarse al proceso grande sin decir por qué.
Ingeniería: PKG-A implementer inherit. strict_tdd true. ADR-0064. Bite with cp not git restore. No --route-decide.

[2026-08-19T15:22:02+00:00] PKG-A · local-gate-runner · started · spawns 2/12
Cliente: Chequeo rapido de que el lote no rompio archivos ajenos ni la sintaxis.
Ingeniería: P001 only. check-owned-paths PKG-A vs HEAD. py_compile feature-state.py. git diff --check.

[2026-08-19T15:25:15+00:00] PKG-A · local-gate-runner · started · spawns 3/12
Cliente: Segundo chequeo rapido ahora que las notas y el spec no cuentan como codigo ajeno.
Ingeniería: P001 retry. Same commands. Exceptions now cover living docs and 034 spec/ADR trees.

[2026-08-19T15:26:25+00:00] PKG-A · gate-runner · started · spawns 4/12
Cliente: Verificar que el ruteo organico no rompio lo que ya andaba.
Ingeniería: Context pack validation. unittest AC-A tests + log-quickfix + ./build.sh --check + git diff --check. Not P001.

[2026-08-19T15:28:38+00:00] PKG-A · package-reviewer · started · spawns 5/12
Cliente: Alguien que no escribio el cambio revisa si el corte de ceremonia realmente corta.
Ingeniería: Clean-context package-reviewer. Same-model inherit degradation: record in --evidence. strict_tdd true so re-run bite tests. Cursor host no --route-decide.

[2026-08-19T15:28:56+00:00] PKG-A · orchestrator · done
Cliente: El cambio chico ya no puede colarse a la ceremonia completa: si alguien arranca un trabajo mediano o grande sin decir por que es riesgoso, el sistema lo corta. Los chequeos automaticos de este lote dieron verde.
Ingeniería: The ownership checker compared the whole dirty working tree against the last commit, so living notes and leftover docs from the previous feature looked like out-of-scope code. After waiving those documentation trees, compile, ownership, eight focused harness tests, and the generated-tree check all passed. The bite is that a scoped init without a named risk token dies before writing state.
Aprendimos: The ownership gate does not know which files this package created versus which were already dirty, so generated vault notes and a previous feature leftover must be waived by directory rather than by widening product ownership.
Conviene ahora: An independent reviewer who did not write the change checks the six acceptance criteria, then we skip app runtime checks because this package has no user interface.
Por qué ahora: Gates exist to prove the bite before a reviewer spends a spawn. They passed, so the remaining cost is independence, not more local compile.
Alternativa: none

[2026-08-19T15:36:35+00:00] PKG-A · orchestrator · done
Cliente: El primer lote ya esta cerrado: un arreglo chico no puede colarse a la ceremonia grande sin decir el riesgo. Alguien que no escribio el cambio lo reviso y dio el visto bueno.
Ingeniería: Independent review found no defects. Eight harness tests were re-run green. Runtime QA was waived because this package has no app UI. Two module-impact notes landed on the state machine and on the generated agent trees. Remaining work is the cheap-writer default and one salvage per package.
Aprendimos: The CLI mode flag default staying scoped is what makes a naked init fail closed; the operational default for a tiny change is simply not calling init.
Conviene ahora: Implement the cheap writer default, rewrite the fast-suffix test without deleting it, and persist a single salvage plus the consecutive-failure promotion counter.
Por qué ahora: Without the cheap default the rest of the quota work has nothing to count as first-attempt green.
Alternativa: none

[2026-08-19T15:36:36+00:00] PKG-B · implementer · started · spawns 1/12
Cliente: El trabajo de aplicar codigo deberia ir primero a un modelo barato o gratis, y solo gastar uno caro si ese falla.
Ingeniería: PKG-B implementer inherit. strict_tdd false but bite the rewritten hot-path test with cp. V-B01 measure tools of -free before pin. Never put opencode/* into tiers.*. billing_rank read-only. No --route-decide. No Engram.

[2026-08-19T15:53:40+00:00] PKG-B · local-gate-runner · started · spawns 2/12
Cliente: Chequeo rapido de que el escritor barato no toco archivos ajenos.
Ingeniería: P001 only after directory waivers including cli_lifecycle.py and generated trees.

[2026-08-19T15:54:37+00:00] PKG-B · local-gate-runner · started · spawns 3/12
Cliente: Segundo chequeo rapido: el archivo que quedaba era del lote anterior.
Ingeniería: P001 retry. Extra exception is PKG-A dirty skill, not a B product path.

[2026-08-19T15:56:36+00:00] PKG-B · gate-runner · started · spawns 4/12
Cliente: Verificar que el escritor barato y el salvage unico no rompen independencia ni el build.
Ingeniería: Context pack plus PKG-A regression cluster. heartbeat-run for build.sh --check. Not P001.

[2026-08-19T15:57:54+00:00] PKG-B · package-reviewer · started · spawns 5/12
Cliente: Alguien que no eligio el modelo barato revisa si el default y el salvage unico son reales.
Ingeniería: Clean-context package-reviewer. Same-model inherit degradation in evidence. No --route-decide.

[2026-08-19T15:57:54+00:00] PKG-B · security-auditor · started · spawns 6/12
Cliente: Revisar si el salvamento o el ruteo barato se pueden abusar para gastar de mas o saltar controles.
Ingeniería: security-auditor read-only. Quota/routing/salvage surface. Same-model inherit degradation. No --route-decide.

[2026-08-19T15:57:54+00:00] PKG-B · orchestrator · done
Cliente: El escritor barato y el salvamento unico ya pasaron los chequeos automaticos: el modelo por defecto es gratis, y si falla solo hay un intento caro.
Ingeniería: Ownership passed after waiving the leftover triage skill from the previous package. Nine harness tests green including the rewritten cheap-pin test, salvage-once, and the organic-routing regression. Generated trees still match the build.
Aprendimos: A package gate against the last commit still sees files the previous accepted package dirtied, so those paths need a pinpoint waiver rather than a wider product ownership.
Conviene ahora: Two independent reviewers look at quota routing and at whether salvage can be abused, then we skip app runtime checks.
Por qué ahora: Quota defaults and a salvage override change who spends money; that is why the security pass sits with the package review instead of waiting for a later audit.
Alternativa: none

[2026-08-19T16:06:42+00:00] PKG-B · finding-verifier · started · spawns 7/12
Cliente: Antes de gastar un arreglo, alguien intenta tumbar los dos hallazgos.
Ingeniería: finding-verifier clean context. Batch F-B01 F-B02. When in doubt uphold. No --route-decide.

[2026-08-19T16:12:01+00:00] PKG-B · repair-agent · started · spawns 8/12
Cliente: Hay que arreglar dos cosas: el contador de fallos baratos se resetea demasiado pronto, y un salvamento sin modelo pesado gasta el unico intento.
Ingeniería: repair-agent inherit. Upheld F-B01 F-B02. Smallest fix. Do not weaken tests. No --route-decide. This is the one salvage-shaped repair of this cycle; keep repair-agent pin cheap.

[2026-08-19T16:20:17+00:00] PKG-B · delta-reviewer · started · spawns 9/12
Cliente: Revisar solo el arreglo: el contador ya no se resetea a mitad de paquete, y el salvamento vacio ya no gasta el intento.
Ingeniería: delta-reviewer inherit. Same-model degradation in evidence. Focused on repair delta. No --route-decide.

[2026-08-19T16:25:32+00:00] PKG-C · implementer · started · spawns 1/12
Cliente: Se tiene que ver y se tiene que chocar un cupo de modelos pesados, distinto del tope de despachos, y ver que porcentaje del barato cierra a la primera.
Ingeniería: PKG-C implementer inherit. MODE_BUDGETS scoped=8 byte-equal. Caps as constants not JSON. P001 not frontier. Techo > salvage and promote. No --route-decide. No Engram.

[2026-08-19T16:25:32+00:00] PKG-B · orchestrator · done
Cliente: El escritor barato ya esta en default y el salvamento unico funciona. Si el barato falla dos paquetes seguidos, el proximo sube un escalon. Eso ya esta cerrado.
Ingeniería: Review found two real defects: consecutive-fail reset on a partial gate pass, and empty salvage spending the slot. Both repaired and confirmed in delta review with six tests green. Runtime QA waived. Next is the separate frontier cap and the green-on-first-attempt percent in the cost report.
Aprendimos: A named-gate PASS is not package close. The consecutive-miss counter is a package grain; resetting it per event hid promotion.
Conviene ahora: Implement the frontier cap of four per package and sixteen per feature, plus the cost-report percent that must not count salvage-green as first attempt.
Por qué ahora: Without a cap distinct from spawn count, salvage and judges still burn quota inside the same budget as cheap writers.
Alternativa: none

[2026-08-19T16:41:52+00:00] PKG-C · local-gate-runner · started · spawns 2/12
Cliente: Chequeo rapido de que el cupo de modelos pesados no toco archivos ajenos.
Ingeniería: P001 after A/B leftover waivers.

[2026-08-19T16:42:42+00:00] PKG-C · gate-runner · started · spawns 3/12
Cliente: Verificar el cupo de modelos pesados y que el porcentaje no cuente un salvamento como primer acierto.
Ingeniería: AC-C cluster plus PKG-B salvage regression plus build --check via heartbeat-run.

[2026-08-19T16:43:55+00:00] PKG-C · orchestrator · done
Cliente: El cupo de modelos pesados ya se puede ver y se puede chocar: el quinto de un lote para, y un salvamento verde no cuenta como acierto a la primera.
Ingeniería: Eleven harness tests green including fifth-frontier reject, cap-beats-salvage, reopen directed reset, and salvage-green excluded from the first-attempt percent. Spawn budget scoped remains eight. Generated trees still match the build.
Aprendimos: Frontier used is a counter beside spawn count, not inside attempts, so reopen can reset it without touching spawn budget.
Conviene ahora: Independent review plus a security pass on whether the cap can be bypassed by omitting flags.
Por qué ahora: A cap that does not fire is quota theatre; a cap that can be skipped by leaving --model empty is the remaining abuse path.
Alternativa: none

[2026-08-19T16:43:56+00:00] PKG-C · package-reviewer · started · spawns 4/12
Cliente: Alguien que no escribio el cupo revisa si realmente corta y si el porcentaje no miente.
Ingeniería: package-reviewer inherit. Same-model degradation in evidence. No --route-decide.

[2026-08-19T16:43:56+00:00] PKG-C · security-auditor · started · spawns 5/12
Cliente: Revisar si se puede gastar de mas omitiendo el modelo o el flag de salvamento.
Ingeniería: security-auditor inherit. Cap classification and omit --model. No --route-decide.

[2026-08-19T16:51:58+00:00] PKG-C · finding-verifier · started · spawns 6/12
Cliente: Antes de arreglar el cupo, alguien intenta tumbar el hallazgo de que un comando chico disfraza un modelo pesado.
Ingeniería: finding-verifier. SEC-001 only. When in doubt uphold. No --route-decide.

[2026-08-19T16:55:49+00:00] PKG-C · repair-agent · started · spawns 7/12
Cliente: Hay que cerrar el agujero: un comando chico no puede disfrazar un modelo pesado para saltarse el cupo.
Ingeniería: repair-agent inherit. SEC-001: remove or role-gate spawn_commands_are_p001 in is_frontier_spawn. Keep local-gate-runner exemption. Unittest 5th heavy implementer with git diff --check rejected. No --route-decide.

[2026-08-19T17:03:01+00:00] PKG-C · delta-reviewer · started · spawns 8/12
Cliente: Revisar solo el arreglo: un comando chico ya no disfraza un modelo pesado.
Ingeniería: delta-reviewer inherit. Focused on is_frontier_spawn. Same-model degradation. No --route-decide.

[2026-08-19T17:07:34+00:00] PKG-C · orchestrator · done
Cliente: El cupo de modelos pesados ya corta de verdad: el quinto de un lote para, y un comando chico ya no disfraza un modelo caro. El reporte muestra que porcentaje del barato cierra a la primera.
Ingeniería: Security review found a real bypass: P001 --command un-classified any role. Repair removed that short-circuit; only local-gate-runner stays exempt. Delta confirmed four tests green. Remaining work is Cursor role pins, the last package.
Aprendimos: A caller-controlled --command list is not a role. The 033 P001 exemption is the local-gate-runner role, not the allowlist riding on a heavy spawn.
Conviene ahora: Emit Cursor frontmatter model per role: cheap writers, distinct-family judges, rewrite the inherit-everywhere test instead of deleting it.
Por qué ahora: Without Cursor pins the cheap default only exists on OpenCode; this host would keep spending whatever the user picked for every role.
Alternativa: none

[2026-08-19T17:07:35+00:00] PKG-D · implementer · started · spawns 1/12
Cliente: En Cursor cada rol tiene que declarar su modelo: los que escriben codigo barato, los que juzgan en otra familia.
Ingeniería: PKG-D implementer inherit. V-D01 slugs measured 2026-08-19 from cursor.com/docs/subagents and models-and-pricing. No --route-decide. No Engram. Rewrite test_no_cursor_agent_pins_a_model, do not delete.

[2026-08-19T17:21:38+00:00] PKG-D · local-gate-runner · started · spawns 2/12
Cliente: Chequeo rapido de que los pines de Cursor no tocaron archivos ajenos.
Ingeniería: P001 after generated-tree and leftover waivers.

[2026-08-19T17:22:35+00:00] PKG-D · local-gate-runner · started · spawns 3/12
Cliente: Segundo chequeo: los tests vecinos eran del lote de ruteo organico, no de los pines.
Ingeniería: P001 retry. Neighbor init fixtures from PKG-A.

[2026-08-19T17:23:18+00:00] PKG-D · gate-runner · started · spawns 4/12
Cliente: Verificar que cada rol Cursor declara modelo y que el escritor y el juez no son la misma familia.
Ingeniería: CursorRuntimeTargetTests plus cheap-pin and organic-routing regressions plus build --check.

[2026-08-19T17:24:16+00:00] PKG-D · orchestrator · done
Cliente: En Cursor cada rol ya declara su modelo: quien escribe codigo usa el barato, quien juzga usa otra familia.
Ingeniería: Fourteen tests green including CursorRuntimeTargetTests. implementer and repair-agent pin composer-2.5; package-reviewer pins gpt-5.6-sol. build check still matches generated trees. --route-decide remains forbidden on this host.
Aprendimos: Cursor cheap is not the OpenCode zen free id; it is a measured Cursor slug in a new models.toml dimension, while RUNTIMES stays without cursor.
Conviene ahora: Independent review of pins and a security pass on whether inherit-universal or a heavy repair-agent pin can sneak back.
Por qué ahora: A pin that silently becomes inherit everywhere would spend the session model on every role again, which is the quota leak this package exists to stop.
Alternativa: none

[2026-08-19T17:24:17+00:00] PKG-D · package-reviewer · started · spawns 5/12
Cliente: Alguien que no eligio los pines revisa si el escritor barato y el juez distinto son reales.
Ingeniería: package-reviewer inherit. Same-model degradation in evidence. No --route-decide.

[2026-08-19T17:24:17+00:00] PKG-D · security-auditor · started · spawns 6/12
Cliente: Revisar si un pin pesado de repair o inherit universal puede volver a gastar la cuota entera.
Ingeniería: security-auditor inherit. Pins, catalog.cursor die, RUNTIMES unchanged. No --route-decide.

[2026-08-19T17:29:16+00:00] PKG-D · finding-verifier · started · spawns 7/12
Cliente: Antes de arreglar, alguien intenta tumbar el hallazgo de que inherit en el juez comparte el modelo del escritor.
Ingeniería: finding-verifier SEC-001. When in doubt uphold. No --route-decide.

[2026-08-19T17:34:08+00:00] PKG-D · repair-agent · started · spawns 8/12
Cliente: Hay que cerrar el agujero: un juez que dice inherit no puede terminar usando el mismo modelo que el que escribe codigo.
Ingeniería: repair-agent inherit. SEC-001: inherit on review-ro/audit/judge dies at generate. Unittest mixed inherit on audit dies; shipped tree stays green. No heavy repair-agent pin. No Cursor in RUNTIMES. No --route-decide. No Engram.

[2026-08-19T17:41:20+00:00] PKG-D · delta-reviewer · started · spawns 9/12
Cliente: Revisar solo el arreglo: un juez que dice inherit ya no puede compartir el modelo del que escribe.
Ingeniería: delta-reviewer inherit. Focus generate.py:768-778 models_config.py:644-652 test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate. Same-model degradation. No --route-decide. No Engram.

[2026-08-19T17:45:46+00:00] PKG-D · orchestrator · done
Cliente: En Cursor cada rol ya declara su modelo: el que escribe codigo usa uno barato, el que juzga usa otra familia, y si el juez deja el modelo en blanco el sistema lo corta. Los cuatro lotes de este trabajo estan cerrados.
Ingeniería: The last package pins Cursor frontmatter per role and rejects inherit on reviewers because inherit is the parent model, not a second family. Repair added that guard; delta re-ran the two named tests green. Runtime QA was waived because this package has no app UI. All four packages of the feature are now accepted.
Aprendimos: Cursor inherit is an alias of the parent, so treating the slug as its own family made a reviewer look independent while sharing the writer.
Conviene ahora: Integrate the four accepted packages: run the global verify, write the integration evidence, then the independent judge. Memory stays in the Obsidian vault, not Engram.
Por qué ahora: Without a global verify the four packages can be locally green and still fail together. The judge cannot run until that evidence exists.

[2026-08-19T17:45:47+00:00] PKG-D · integrator · started · spawns 10/12 WARN 80%
Cliente: Los cuatro lotes ya estan cerrados. Hay que comprobar que juntos siguen haciendo lo que se pidio, y dejar esa prueba por escrito.
Ingeniería: integrator inherit. All packages accepted. Write docs/specs/034-cuota-organica-y-writer-barato/evidence/INTEGRATION.md. Run verify.sh via heartbeat-run. module-impact-detect PKG-D. No Engram. No --route-decide. Do not reopen packages.

[2026-08-19T18:05:42+00:00] PKG-D · gate-runner · started · spawns 11/12 WARN 80%
Cliente: Hay que volver a correr la prueba grande ahora que se ajustaron dos tests viejos al escritor barato.
Ingeniería: gate-runner inherit. heartbeat-run verify.sh after two separation bites retargeted to cheap BASE. Not P001. No --route-decide. No Engram.

[2026-08-19T18:22:09+00:00] PKG-D · adversarial-judge · started · spawns 12/12
Cliente: Alguien que no escribio el trabajo revisa si la prueba final y los cuatro lotes cubren lo que se pidio.
Ingeniería: adversarial-judge inherit. Evidence docs/specs/034-cuota-organica-y-writer-barato/evidence/. VERIFY_PASS 1363/13m46s. Same-model degradation. No --route-decide. No Engram.

[2026-08-19T18:30:20+00:00] PKG-D · orchestrator · done
Cliente: Engram no hace falta: el contexto ya vive en tu vault de Obsidian. El trabajo de cuota y escritor barato cerro: un arreglo chico no abre ceremonia, el que escribe codigo arranca barato, hay un techo de modelos pesados, y en Cursor cada rol declara su modelo.
Ingeniería: Feature 034 is DONE. Four accepted packages, JUDGE_PASS, verify.sh 1363 tests green. Engram stays a no-goal because the vault is already mandatory. Cursor inherit on a reviewer dies at generate. Frontier caps sit beside MODE_BUDGETS; scoped spawn ceiling stays eight. Memory landed in docs/ai/knowledge, not in Engram.
Aprendimos: Treating Cursor inherit as its own family made reviewers look independent while they shared the parent model. The vault already covers what Engram would copy.
Conviene ahora: Nothing left in this pipeline. Commit or release only if you ask for it.
Por qué ahora: The judge and the global suite already passed, so the remaining work is a human cut, not another agent.
