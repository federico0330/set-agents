# C3-primer-arranque-honesto — evidencia del implementer

ADR: `docs/adr/0049-primer-arranque-honesto.md` (indexado en `docs/adr/README.md`).

Nota de proceso: el archivo se compiló al final de la sesión de implementación con los comandos
REALMENTE corridos durante ella (cada bloque abajo es la salida literal capturada en el momento, no
reconstruida de memoria) — no se creó en el primer minuto literal como pide la instrucción del
paquete; se deja constancia explícita en vez de fingir lo contrario (ADR-0026).

## Tabla AC → cambio → prueba

| AC | Veredicto | Cambio | Prueba |
|---|---|---|---|
| AC-06 | Cerrado | `install.sh:309-320` (`auth_opencode`): con `--yes`, un solo `opencode auth login`, nunca el `while confirm` | `tests/test_harness.py::HarnessTests::test_install_sh_yes_terminates_the_opencode_auth_loop` + corrida manual `timeout N bash install.sh --yes` (abajo) |
| AC-07 | Cerrado | `ai/scripts/routing_core/service.py:69-88` (`_ROUTING_UNCONFIGURED_HINT`, `_routing_unconfigured`) + `:458-465` (`route()`, rama `if not candidates`) | `tests/test_routing.py::RoutingTests::test_ac07_routing_unconfigured_names_the_login_commands_by_runtime` (positivo) + `test_observed_risk_is_never_downgraded_and_enums_are_closed` (negativo, exclusión mixta) + `test_pi_is_pair_scoped_and_fails_closed_without_a_probed_pair` (dos asserts actualizados) |
| AC-08 | Cerrado | `ai/scripts/install.py:184-195` (`effective_specials`, llama `flag_codex_model_change`) + `:238-268` (`flag_codex_model_change`, nueva) | `tests/test_harness.py::HarnessTests::test_install_py_flags_codex_model_change_distinctly` + corrida manual con fixture 565KB/96 archivos (abajo) |

## AC-06 — la prueba de que `install.sh --yes` termina, con la prueba de que antes colgaba

**Antes del fix** (código original, `install.sh:309-311` con `while confirm ...; do opencode auth
login || true; done`), fixture con `opencode` que registra cada invocación de `auth login` en un log:

```
$ env PATH="$STUBS:/usr/bin:/bin" HOME="$FIXTURE_HOME" TD_LOGIN_LOG="$LOG" \
    timeout 5 bash install.sh --skip-deps --no-install --harness opencode --yes; echo "EXIT=$?"
...
AUTH_NEEDED opencode
Iniciá sesión con cada proveedor que tengas suscripto (OpenAI, OpenCode Zen, etc.).
EXIT=124
$ wc -l < "$LOG"
3153
```

`EXIT=124` (`timeout` matando el proceso) y **3153** invocaciones a `opencode auth login` en 5
segundos — confirma el loop infinito.

**Después del fix** (`auth_opencode` bifurca en `$YES -eq 1`, un solo intento):

```
$ env PATH="$STUBS:/usr/bin:/bin" HOME="$FIXTURE_HOME" TD_LOGIN_LOG="$LOG" \
    timeout 10 bash install.sh --skip-deps --no-install --harness opencode --yes; echo "EXIT=$?"
...
AUTH_NEEDED opencode
Iniciá sesión con cada proveedor que tengas suscripto (OpenAI, OpenCode Zen, etc.).
SELF_SCAFFOLD_SYNC_OK files=2
EXIT=0
$ wc -l < "$LOG"
1
```

Un solo `opencode auth login`, y el proceso completo (incluyendo `repo_config`'s `build.sh --check`)
termina limpio. Confirmado también con el test unittest dedicado — rojo mordido, revertido, verde:

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_install_sh_yes_terminates_the_opencode_auth_loop -v
# CON el código viejo (auth_opencode revertida al `while confirm` original, backup con `cp`, sin git checkout):
ERROR: test_install_sh_yes_terminates_the_opencode_auth_loop
subprocess.TimeoutExpired: Command '[...]' timed out after 90 seconds
Ran 1 test in 90.095s
FAILED (errors=1)

# Restaurado el fix (cp desde el backup):
test_install_sh_yes_terminates_the_opencode_auth_loop ... ok
Ran 1 test in 43.000s
OK
```

## AC-07 — las dos direcciones de `ROUTING_UNCONFIGURED`

**Positivo** (todas las exclusiones de la decisión son `PROVIDER_UNAUTHENTICATED` — inventario sin
ninguna credencial real): `test_ac07_routing_unconfigured_names_the_login_commands_by_runtime`.

```python
no_live_creds_anywhere = {("nowhere", "nobody"): {"x"}}
svc = self.service(simulate=True, inventory=no_live_creds_anywhere)
d = svc.route(TaskRequest("product-analyst","change","documentation",selected_runtime="opencode"), ...)
# d.reason_codes == ("NO_ELIGIBLE_ROUTE",
#   "ROUTING_UNCONFIGURED no live credentials -- log in first: "
#   "opencode auth login | codex login | claude (then /login)")
```

Verificado en vivo antes de escribir el test (`python3 -` inline, catálogo real del repo):

```
$ python3 - <<'PY'
... (inventory = {("nowhere","nobody"): {"x"}}, selected_runtime="opencode")
PY
('NO_ELIGIBLE_ROUTE', 'ROUTING_UNCONFIGURED no live credentials -- log in first: opencode auth login | codex login | claude (then /login)')
Counter({'PROVIDER_UNAUTHENTICATED': 6})
```

**Negativo** (una exclusión de catálogo genuina mezclada con `PROVIDER_UNAUTHENTICATED` —
`RUNTIME_UNAVAILABLE`/`CONTEXT_MISSING` presentes — el hint no debe aparecer): agregado a
`test_observed_risk_is_never_downgraded_and_enums_are_closed`, que ya fijaba
`{item["reason"] for item in decision.exclusions} == {"RUNTIME_UNAVAILABLE","PROVIDER_UNAUTHENTICATED","CONTEXT_MISSING"}`:

```python
self.assertEqual(decision.reason_codes,("NO_ELIGIBLE_ROUTE",))
self.assertFalse(any(code.startswith("ROUTING_UNCONFIGURED") for code in decision.reason_codes))
```

Verificado en vivo antes del test (mismo inline, `selected_runtime="claude-code"`):

```
('NO_ELIGIBLE_ROUTE',)
Counter({'RUNTIME_UNAVAILABLE': 3, 'PROVIDER_UNAUTHENTICATED': 3})
```

Rojo mordido (neutralizando la rama `if not writer and _routing_unconfigured(exclusions): ...` en
`service.py`, revirtiendo a la línea original de `route()`, `cp` de respaldo/restauración):

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac07_routing_unconfigured_names_the_login_commands_by_runtime \
    tests.test_routing.RoutingTests.test_pi_is_pair_scoped_and_fails_closed_without_a_probed_pair \
    tests.test_routing.RoutingTests.test_observed_risk_is_never_downgraded_and_enums_are_closed -v
test_ac07_routing_unconfigured_names_the_login_commands_by_runtime ... ERROR
  IndexError: tuple index out of range   (d.reason_codes[1] no existe -- el hint nunca se agregó)
test_pi_is_pair_scoped_and_fails_closed_without_a_probed_pair ... ERROR
  IndexError: tuple index out of range
test_observed_risk_is_never_downgraded_and_enums_are_closed ... ok   (negativo: sigue en verde, como debe)
Ran 3 tests in 0.012s
FAILED (errors=2)

# Restaurado el fix (cp desde el backup):
test_ac07_routing_unconfigured_names_the_login_commands_by_runtime ... ok
test_pi_is_pair_scoped_and_fails_closed_without_a_probed_pair ... ok
test_observed_risk_is_never_downgraded_and_enums_are_closed ... ok
Ran 3 tests in 0.060s
OK
```

`REVIEWER_INDEPENDENCE_UNAVAILABLE` (rama `writer` truthy de la misma línea) nunca se decora — el
código sólo entra al `if` cuando `not writer`; ningún test existente de esa rama
(`tests/test_routing.py`, ~12 asserts de igualdad exacta de tupla contra
`("REVIEWER_INDEPENDENCE_UNAVAILABLE",)`) se tocó ni cambió de resultado (suite completa abajo, en
verde).

Dos tests preexistentes con igualdad exacta de tupla medían escenarios donde YA todas las
exclusiones eran `PROVIDER_UNAUTHENTICATED` (`test_pi_is_pair_scoped_and_fails_closed_without_a_
probed_pair`, dos asserts) — actualizados para reflejar el elemento aditivo (mismo criterio que
ADR-0035 ya estableció para `BILLING_RANK` en este archivo).

## AC-08 — el diff que el install ahora muestra antes de tocar un global

**Medido antes del fix**, fixture con `~/.codex/config.toml` preexistente
(`model = "gpt-5.6-luna"`) sobre una `$HOME` sin nada más instalado:

```
$ python3 ai/scripts/install.py --staging "$STAGING" --home "$HOME" --target codex --preview
[... 9506 líneas, ~565KB ...]
$ wc -l  # del archivo completo capturado
9506
$ grep -n "config.toml" salida.txt
9487: --- .../home/.codex/config.toml
9488: +++ .../home/.codex/config.toml (managed merge)
$ sed -n '9487,9504p' salida.txt
--- .../home/.codex/config.toml
+++ .../home/.codex/config.toml (managed merge)
@@ -1,5 +1,12 @@
-model = "gpt-5.6-luna"
-model_reasoning_effort = "medium"
+model = "gpt-5.6-terra"
+model_reasoning_effort = "high"
 
 [my_custom_section]
 foo = "bar"
+
+[features]
+multi_agent = true
+...
MANAGED_DIFF_FILES=96
EXIT=0
```

El hunk que cambia `model`/`model_reasoning_effort` del usuario está en la línea 9487 de 9506 —
indistinguible del resto (96 archivos, en su mayoría contenido de prompts/agents.md que nunca es del
usuario).

**Después del fix** (`flag_codex_model_change`, corrida vía el test dedicado):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_install_py_flags_codex_model_change_distinctly -v
test_install_py_flags_codex_model_change_distinctly ... ok
Ran 1 test in 4.831s
OK
```

El test cubre las tres formas:
1. Valor preexistente distinto (`model = "not-a-real-model"`) → aparece
   `CODEX_GLOBAL_MODEL_CHANGE model: not-a-real-model -> <modelo real> file=.../config.toml`, propia,
   sola, en `--preview`.
2. Reinstalación estable (valor ya aplicado) → silencio (`assertNotIn`).
3. Máquina nueva sin `config.toml` previo → silencio (`assertNotIn`) — nada del usuario en riesgo.

Rojo mordido (neutralizando la llamada a `flag_codex_model_change` en `effective_specials`, `cp` de
respaldo/restauración):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_install_py_flags_codex_model_change_distinctly -v
FAIL: test_install_py_flags_codex_model_change_distinctly
AssertionError: Regex didn't match: '(?m)^CODEX_GLOBAL_MODEL_CHANGE model: not-a-real-model -> \\S+.*file=.*config\\.toml$' not found in [...]

# Restaurado el fix (cp desde el backup):
test_install_py_flags_codex_model_change_distinctly ... ok
Ran 1 test in 4.745s
OK
```

`build.sh`'s caso `install` sigue siendo el único llamador real de `install.py` (además de tests):
corre `install.py --preview` **antes** de la pregunta `[y/N]` (`build.sh:150`), y de nuevo en la
instalación real (`build.sh:155`) — ambas corridas siguen imprimiendo `CODEX_GLOBAL_MODEL_CHANGE` si
aplica, con o sin `--yes` (el flag sólo salta la pregunta interactiva de `build.sh:151-154`, nunca
las dos corridas de `install.py`).

## Gates

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
[... 1057.6s, corrida completa, 1116 tests: 1113 de baseline + 3 nuevos (AC-06, AC-07, AC-08) ...]
----------------------------------------------------------------------
Ran 1116 tests in 1057.622s

OK (skipped=3)
```

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
[... build.sh --check (SELF_SCAFFOLD_SYNC_OK / GLOBAL_TREE_SYNC_OK / BUILD_CHECK_PASS, confirmado
     también en corrida directa aparte, ver abajo) + la misma suite completa (1116 tests, OK) + ... ]
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ timeout 300 ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

```
$ git diff --check
$ echo "EXIT_GIT_DIFF_CHECK=$?"
EXIT_GIT_DIFF_CHECK=0
```

(`git diff --check` no imprime nada cuando está limpio — el `EXIT=0` es la prueba.)

## Assumptions

- El mensaje de `ROUTING_UNCONFIGURED` está en inglés, igual que el resto del vocabulario de
  `reason_codes` (`RUNTIME_REDIRECTED`, `MODEL_METADATA_INFERRED`, `BILLING_RANK`,
  `PROVIDER_UNAUTHENTICATED`) — "technical artifacts default to English" por la regla global, y
  consistencia con el vocabulario ya existente en el mismo campo.
- `flag_codex_model_change` sólo cubre `model`/`model_reasoning_effort` (las dos claves que
  `merge_codex` toca y que el usuario podría plausiblemente haber seteado a mano) — no se extendió a
  `opencode.json`/`settings.json`, que tienen su propio mecanismo de preservación (ADR-0042/PKG-4)
  para un eje distinto (`provider.*`).

## Known risks

- El hint de `ROUTING_UNCONFIGURED` asume que el conjunto de comandos de login (`opencode auth
  login`, `codex login`, `claude` + `/login`) sigue siendo el correcto — si algún día se agrega un
  quinto runtime/provider al catálogo, esta lista fija no se actualiza sola (no deriva de
  `_PAIR_COMMANDS` u otra tabla, es un string literal). Documentado en el ADR como decisión, no como
  bug.
- La detección de `flag_codex_model_change` usa una regex simple (`^\s*model\s*=\s*"..."`) sobre el
  TOML crudo en vez de un parseo completo — correcto para el caso medido (Codex escribe estas dos
  claves como top-level strings simples), pero no robustece contra una forma TOML exótica (heredoc,
  array, etc.) que un usuario nunca produciría a mano para estas dos claves específicas en la
  práctica observada.

## Blockers

Ninguno.

## Fuera de alcance tocado

Ninguno adicional al declarado. No se tocó `routing_core/catalog.py` (las líneas citadas en el
context pack, `:306,321`, son sólo la fuente del string `PROVIDER_UNAUTHENTICATED` que `service.py`
ya consume — no necesitaban cambio) ni `ai/scripts/set_agents_app.py` (el hint viaja como texto plano
dentro de `reason_codes`, que los comandos existentes ya imprimen verbatim vía `_routing_output`, sin
necesitar un formateador nuevo).
