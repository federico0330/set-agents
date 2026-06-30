# Cómo cambiar el modelo de un agente

Los modelos NO se editan en los archivos instalados (`~/.config/opencode/agents/*.md`) — esos los **genera**
`build.sh`. La fuente es **`manifest.tsv`**. Editás ahí, corrés `build.sh --install`, y se propaga a los 3 harnesses.

---

## Pasos (ejemplo: cambiar el modelo del `orchestrator` en OpenCode)

### 1. Mirá qué modelos válidos tenés
```bash
opencode models            # OpenCode (Zen = opencode/* · Go = opencode-go/* · GPT Plus = openai/*)
```
Copiá el ID exacto que querés (ej: `opencode/claude-sonnet-4-6`). Si ponés un ID que no existe, ese agente falla.

### 2. Editá `manifest.tsv`
```bash
cd ~/SET-AGENTES && $EDITOR manifest.tsv
```
Es una tabla separada por TABS. Columnas:
```
role  mode  temp  perm  opencode_model  claude_model  codex_model
```
Buscá la fila `orchestrator` y cambiá la columna del harness que quieras:
- `opencode_model` → para OpenCode
- `claude_model`   → para Claude Code (`opus` / `sonnet` / `haiku`)
- `codex_model`    → para Codex (`gpt-5.5`, `gpt-5.4-mini`, etc.)

Ejemplo — orquestador de OpenCode a Sonnet de Zen:
```
orchestrator  primary  0.1  coord  opencode/claude-sonnet-4-6  sonnet  gpt-5.5
```
> Respetá los TABS (no espacios) entre columnas, y no toques `role` (es la clave que matchea el archivo del agente).

### 3. Aplicá el cambio
```bash
./build.sh --install
```
Regenera e instala los 16 agentes en los 3 harnesses de una.

### 4. Verificá
```bash
rg '^model:' ~/.config/opencode/agents/orchestrator.md     # debe mostrar el nuevo ID
opencode run --agent orchestrator "Responde solo: OK"      # debe responder (confirma que el modelo anda)
```

---

## ⚠️ Importante: los perfiles pisan `manifest.tsv`

Los scripts `use-go-zen.sh` / `use-zen.sh` **sobrescriben `manifest.tsv`** con su versión de
`profiles/`. Entonces:

- Si editás `manifest.tsv` y NO vas a cambiar de perfil → con el Paso 3 alcanza (cambio temporal).
- Si querés que el cambio **sobreviva** a un `use-zen.sh` / `use-go-zen.sh` → editá también el/los archivos de
  perfil correspondientes y reaplicá:
  ```bash
  $EDITOR profiles/manifest.zen.tsv       # y/o profiles/manifest.go-zen.tsv
  ./use-zen.sh                            # (o ./use-go-zen.sh) para reinstalar desde el perfil
  ```

## Nota: modelo por defecto
El `model` de `~/.config/opencode/opencode.json` (y su fuente `Global/_shared/opencode.json`) es el modelo
**por defecto** que usa OpenCode cuando un agente no especifica uno. Como todos nuestros agentes especifican el
suyo, casi nunca importa — pero si lo querés cambiar, editá `Global/_shared/opencode.json` y `./build.sh --install`.

## Resumen en una línea
**Editá `manifest.tsv` (o el perfil en `profiles/`) → `./build.sh --install` → verificá con `rg '^model:'`.**
Nunca edites los `*.md` instalados a mano: el próximo build los pisa.
