# PKG-D2 — Integración sobre candidato C2 verificable

## Objetivo y contrato

Validar AC-09 sobre el commit C2, no sobre el root sucio: regresiones integradas, ayuda,
TTY aislada OpenCode 1.18.14 y huella contractual. Fuente: spec 049 aprobada
`0ed880d4…`, state revision 168. Depende de PKG-A, PKG-B y del `C2_REF` commiteado de PKG-C2.

## Identidad congelada (orquestador)

- `C2_REF` / `REPAIRED_C2_REF` = `ff91f5538c3ee588b29a6b7267ad82439191b5c1`
- Worktree aislado D2: `/tmp/set-agents-049-d2.OwbVs7` (detached en ese ref)
- Baseline de fundación C2 (no delta D2): `3878fb0dcf41a475ad8dcd4bb691ddd5c5ad018b`
- No partir del root sucio 045–048.

## Propiedad y restricciones

Owned: `tests/test_model_identity_integration_049.py`,
`tests/test_model_identity_tty_049.py`, `docs/specs/049-identidad-honesta-modelos/evidence/`.
Sólo lectura: `set_agents_app.py`, `model_state.py`, `setup_models.py`, `build.sh`,
`ai/scripts/verify.sh` y `spec.md`. No editar producción, `Global/**`, modelos/state/specs
ni packs anteriores. Un fallo de C2/A/B se devuelve a su dueño; D2 no lo corrige.

Madres relevantes: CLI `main()` `ai/scripts/set_agents_app.py:4535`, home `menu()` `:4012`,
wizard `setup_models.py:_edit_overlay_cell()` `:824` y generador `generate.py:496`.

## Aislamiento e identidad

1. Recibir `C2_REF` y comprobar que es commit: `git rev-parse "$C2_REF^{commit}"`.
2. Crear un worktree temporal detached desde ese ref; no desde root/HEAD sucio, sin reset ni
checkout del root:

```bash
WT=$(mktemp -d /tmp/set-agents-049-d2.XXXXXX)
git worktree add --detach "$WT" "$C2_REF"
git -C "$WT" status --porcelain=v1
```

3. Usar sólo el índice propio del worktree. Commitear pruebas/evidencia D2 y capturar
`D2_REF`; cada resultado debe identificar `C2_REF..D2_REF`. Al integrar, transportar sólo
los tres owned paths desde ese rango validado, nunca el árbol del worktree.

## Escenarios y gates

- Una sesión que cambia Astra→Luna muestra último envío Luna; Terra como default sigue
  neutral. `/model` no cambia SET ni artefactos.
- Help normal queda humano; `--help --avanzado` conserva ingeniería; argv inválido de
  `--model-state` da rc 2 sin JSON parcial.
- TTY con HOME/STATE/binario OpenCode falsos sólo prueba observación allow-listed o razón
  cerrada; no autentica, instala ni retiene transcript/ID/export.

```bash
python3 -m unittest -v tests.test_model_identity_integration_049 tests.test_model_identity_tty_049
./build.sh --check
./ai/scripts/verify.sh
git diff --check
python3 -c 'from pathlib import Path; import hashlib,re; paths=("docs/specs/049-identidad-honesta-modelos/spec.md","docs/specs/049-identidad-honesta-modelos/acceptance.md","docs/specs/049-identidad-honesta-modelos/proposal.md","docs/specs/049-identidad-honesta-modelos/design.md"); b=b"".join(p.encode()+b"\\0"+re.sub(rb"sha256:(?:[0-9a-f]{64}|<CONTRACT_SHA256>)",b"sha256:<CONTRACT_SHA256>",Path(p).read_bytes())+b"\\0" for p in paths); print("sha256:"+hashlib.sha256(b).hexdigest())'
git -C "$WT" diff --name-only "$C2_REF..$D2_REF"
```

Ejecutar desde `$WT`; el último comando y la evidencia tienen que demostrar ownership
cerrado. Guardar sólo resúmenes sanitizados de rc, versión, refs y gates.

## Revisión y hecho

Panel: `package-reviewer`, `security-auditor`; runtime surface true, strict TDD false,
test owner `test-writer`. Hecho cuando D2_REF existe, sus cambios se limitan a owned paths,
los gates pasan y la TTY demuestra observación segura o degradación segura sin atribuir
045–048 al candidato.
