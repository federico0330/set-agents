# D2-trabajo-visible — verificación adversarial, ciclo 2

Package: `D2-trabajo-visible`  
Base fija: `489ecff52a7c8aca84ce931180c6f0005cb8a63c`  
Modo: análisis focal read-only del producto; este archivo es la única escritura autorizada.

## Checkpoint previo a reproducciones

- Leídos completos el context pack `context/D2-trabajo-visible.md`, `evidence/D2-delta-review.md`,
  la evidencia D2 anterior y `spec.md` (AC-04/AC-05).
- El worktree ya contenía modificaciones y evidencia no trackeada de otros agentes. Se preservan
  sin revertirlas ni incluirlas en el juicio; `git rev-parse HEAD` confirmó la base fija.
- Superficies bajo juicio: `cmd_provider_verify` / `_provider_liveness` y los dos instaladores
  interactivos envueltos por `with_progress` (`run_tty` y post-update sin `--yes`).
- No se ejecutarán `verify.sh`, suite global ni comandos del paquete siguiente. Las reproducciones
  focales previstas duran menos de un minuto; si alguna se extiende, se reintentará mediante
  `python3 ai/scripts/heartbeat-run.py --interval 20 -- <cmd>`.

## Lectura independiente del árbol

- D2-F01: `_provider_liveness` conserva timeout declarado de 2 s
  (`ai/scripts/set_agents_app.py:2676,2689-2713`) y `cmd_provider_verify` lo llama directamente
  (`ai/scripts/set_agents_app.py:2755-2765`), sin `tui.with_progress`.
- D2-DR01: `with_progress` ejecuta `fn` en un worker mientras el caller escribe frames cada 100 ms
  después de 300 ms (`ai/scripts/tui.py:577-640`). `run_tty` envuelve un `subprocess.run` con TTY
  heredada en ese wrapper (`ai/scripts/set_agents_app.py:3612-3620`). La instalación post-update
  usa la misma forma y sólo agrega `--yes` si `yes=True`
  (`ai/scripts/set_agents_app.py:1441-1454`). `suspend_terminal()` restaura el modo de terminal,
  pero no transfiere ownership del stream ni detiene los frames que escribe el caller.

## Reproducciones

### D2-F01 — `cmd_provider_verify` con liveness de 350 ms

Comando literal:

```bash
python3 -c 'import io,sys,time; from unittest import mock; sys.path.insert(0,"ai/scripts"); import set_agents_app as app; entry=app.provider_registry.ProviderEntry(origin="user",spec={"npm":"@ai-sdk/openai-compatible","name":"mine","options":{"baseURL":"http://x/v1"},"models":{"m":{"name":"m"}}}); out=io.StringIO(); err=io.StringIO(); snapshots=[]; slow=lambda _url:(snapshots.append((out.getvalue(),err.getvalue())),time.sleep(0.35),snapshots.append((out.getvalue(),err.getvalue())),"alive")[-1]; patches=(mock.patch.object(app,"_load_providers_registry",return_value={"mine":entry}),mock.patch.object(app,"_provider_liveness",side_effect=slow),mock.patch.object(sys,"stdout",out),mock.patch.object(sys,"stderr",err)); [p.start() for p in patches]; started=time.monotonic(); rc=app.cmd_provider_verify(); elapsed=time.monotonic()-started; [p.stop() for p in reversed(patches)]; print("PROVIDER_VERIFY elapsed=%.3fs rc=%d silent_during_wait=%s stderr=%r stdout=%r"%(elapsed,rc,all(not o and not e for o,e in snapshots),err.getvalue(),out.getvalue()))'
```

Exit code: `0`.

Salida literal:

```text
PROVIDER_VERIFY elapsed=0.350s rc=0 silent_during_wait=True stderr='' stdout='PROVIDER_VERIFY mine origin=user shape=ok liveness=alive at=2026-08-17T02:57:58.727165Z\n'
```

La demora cruza el umbral contractual y ambas muestras tomadas inmediatamente antes y después
de los 350 ms permanecen vacías. La única línea aparece en stdout después de finalizar; no existe
progreso en stderr ni estado persistente separado. La reproducción confirma exactamente D2-F01.

### D2-DR01 — prompts interactivos

#### Ruta `run_tty`

Comando literal:

```bash
python3 -c 'import io,sys,time,types; from unittest import mock; sys.path.insert(0,"ai/scripts"); import set_agents_app as app; stream=type("TTY",(io.StringIO,),{"isatty":lambda self:True})(); child=lambda *_a,**_k:(stream.write("CONFIRMAR? [s/N] "),stream.flush(),time.sleep(0.45),stream.write("CHILD_DONE"),types.SimpleNamespace(returncode=0))[-1]; patches=(mock.patch.object(app.subprocess,"run",side_effect=child),mock.patch.object(sys,"stderr",stream),mock.patch.dict(app.os.environ,{"NO_COLOR":"","TERM":"xterm"},clear=False)); [p.start() for p in patches]; started=time.monotonic(); rc=app.run_tty(["fake-installer"]); elapsed=time.monotonic()-started; [p.stop() for p in reversed(patches)]; text=stream.getvalue(); between=text.split("CONFIRMAR? [s/N] ",1)[1].split("CHILD_DONE",1)[0]; print("RUN_TTY elapsed=%.3fs rc=%d frame_after_prompt_before_child_done=%s tail=%r"%(elapsed,rc,"\r" in between,text))'
```

Exit code: `0`.

Salida literal:

```text
RUN_TTY elapsed=0.451s rc=0 frame_after_prompt_before_child_done=True tail='CONFIRMAR? [s/N] \r| ejecutando instalador…\r/ ejecutando instalador…CHILD_DONE\r                         \rejecutando instalador: listo\n'
```

El marcador `CHILD_DONE` delimita el fin del hijo. Los frames `\r|` y `\r/` aparecen después
del prompt y antes de ese marcador: el indicador y el proceso interactivo comparten el terminal
concurrentemente.

#### Ruta post-update sin `--yes`

Comando literal:

```bash
python3 -c 'import io,sys,time,types; from unittest import mock; sys.path.insert(0,"ai/scripts"); import set_agents_app as app; out=io.StringIO(); stream=type("TTY",(io.StringIO,),{"isatty":lambda self:True})(); seen=[]; child=lambda command,**_k:(seen.append(command),stream.write("ACTUALIZAR? [s/N] "),stream.flush(),time.sleep(0.45),stream.write("CHILD_DONE"),types.SimpleNamespace(returncode=0))[-1]; fake_git=lambda *args,**_k:types.SimpleNamespace(returncode=0,stdout="abc cambio\n",stderr=""); patches=(mock.patch.object(app,"tree_clean",return_value=True),mock.patch.object(app,"upstream_ref",return_value="origin/main"),mock.patch.object(app,"rev_count",side_effect=[1,0]),mock.patch.object(app,"short_sha",side_effect=["old","new"]),mock.patch.object(app,"git",side_effect=fake_git),mock.patch.object(app,"_upstream_remote_and_branch",return_value=("origin","main")),mock.patch.object(app,"_install_scope",return_value=None),mock.patch.object(app.subprocess,"run",side_effect=child),mock.patch.object(sys,"stdout",out),mock.patch.object(sys,"stderr",stream),mock.patch.dict(app.os.environ,{"NO_COLOR":"","TERM":"xterm"},clear=False)); [p.start() for p in patches]; started=time.monotonic(); rc=app.cmd_update(yes=False,no_install=False,assume_fetched=True); elapsed=time.monotonic()-started; [p.stop() for p in reversed(patches)]; text=stream.getvalue(); between=text.split("ACTUALIZAR? [s/N] ",1)[1].split("CHILD_DONE",1)[0]; print("POST_UPDATE elapsed=%.3fs rc=%d install_has_yes=%s frame_after_prompt_before_child_done=%s stderr=%r stdout=%r"%(elapsed,rc,"--yes" in seen[0],"\r" in between,text,out.getvalue()))'
```

Exit code: `0`.

Salida literal:

```text
POST_UPDATE elapsed=0.451s rc=0 install_has_yes=False frame_after_prompt_before_child_done=True stderr='aplicando actualización: listo\nACTUALIZAR? [s/N] \r| instalando actualización…\r/ instalando actualización…CHILD_DONE\r                            \rinstalando actualización: listo\n' stdout='Novedades (1 commits):\nabc cambio\nUPDATE_APPLIED old..new\n'
```

La llamada comprobó además que el argv interactivo no contiene `--yes`. Nuevamente, ambos frames
se escriben después del prompt y antes de `CHILD_DONE`. `suspend_terminal()` no evita la carrera:
sólo restaura el modo del terminal mientras `with_progress` conserva un renderer concurrente en el
caller.

## Veredictos

### D2-F01 — `upheld`

No se pudo refutar. El código citado llama la liveness alcanzable sin wrapper, y la reproducción
del flujo real de `cmd_provider_verify()` confirmó 350 ms de silencio completo antes de su única
línea final. Esto contradice AC-04 (`spec.md:50-51`).

### D2-DR01 — `upheld`

No se pudo refutar. Las dos rutas citadas usan `with_progress` sobre un hijo interactivo y ambas
reproducciones confirmaron frames posteriores al prompt mientras el hijo todavía ejecutaba. Esto
contradice el handoff requerido por AC-05 (`spec.md:52`).

```json
{
  "package_id": "D2-trabajo-visible",
  "verdicts": [
    {
      "id": "D2-F01",
      "verdict": "upheld",
      "reason": "La reproducción confirmó 350 ms de silencio total en cmd_provider_verify mientras _provider_liveness estaba en curso."
    },
    {
      "id": "D2-DR01",
      "verdict": "upheld",
      "reason": "Las reproducciones de run_tty y post-update sin --yes confirmaron frames del indicador después del prompt y antes de que terminara el hijo interactivo."
    }
  ],
  "observations": []
}
```

Resumen: ambos findings sobreviven sin cambios y deben pasar a reparación. D2-DR02 queda fuera de
esta verificación separada por instrucción del coordinador.

## Destilado (dominio: architecture)

- Un wrapper de progreso aplicado fuera de una operación interactiva conserva un renderer concurrente y no equivale a ceder ownership del terminal.
- Restaurar modo cooked con `suspend_terminal()` no pausa ni serializa escritores de stderr.
- Los límites de latencia dinámicos deben instrumentarse en el call site humano real; un timeout de red alcanzable sin wrapper deja el flujo silencioso.
