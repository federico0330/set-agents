# 049 — Identidad honesta de modelos y convergencia de la consola

- **Estado:** Approved — aprobación explícita de implementar esta enmienda consolidada.
- **Contrato:** `049-model-identity/v0.3.0`.
- **Huella contractual:** `sha256:47923adc4a83d40a78edd210aedf91959397e97d319d9d64f406258a07813278`; se calcula al final con el comando reproducible de este documento.
- **Depende de:** 045 PKG-B, 046, 047 y 048.

## Problema, alcance y lenguaje público

Una consola puede mostrar cuatro hechos distintos: el último envío que SET pudo observar, el default deseado por SET para una sesión futura, la proyección instalada y la política de routing. Ninguno es un “modelo actual”. `/model` gobierna la sesión abierta: no modifica SET ni la instalación. El footer de una respuesta es evidencia de esa respuesta; un selector prepara el siguiente envío. Un rótulo decorativo de plugin no es evidencia: su productor sigue **sin verificar**.

049 publica un estado singular para el **runtime primario resuelto por SET** y el rol `orchestrator`; no hay selector público de runtime ni rol. Si el runtime no se resuelve, el scope informa `unavailable`. La observación de sesión sólo se intenta cuando ese runtime es `opencode`; en cualquier otro runtime se degrada a `unobserved/unsupported_runtime` sin invocar OpenCode. Las referencias de modelo son strings opacas o `null`: SET no las cataloga, interpreta ni hardcodea.

La nueva API pública es sólo lectura:

```text
set-agents --model-state [--project DIR] [--json]
```

No admite flags de mutación, instalación, generación, routing, TUI, selector de rol/runtime ni posicionales. Una combinación inválida o un proyecto inválido termina con rc 2, explicación humana por stderr, cero mutaciones y cero JSON parcial. Una fuente ausente o no observable devuelve rc 0 y estado degradado.

## Contrato JSON estable

`--json` imprime un objeto UTF-8 una vez. Una clave o enum nuevo exige `schema_version` nuevo. La salida humana muestra el mismo estado y no divulga más.

```json
{
  "schema_version": 1,
  "scope": {"runtime": "<primary-runtime>|unavailable", "role": "orchestrator"},
  "observed": {"status": "observed|unobserved", "source": "opencode-sanitized-export|unavailable", "model": "<opaque-string>|null", "observed_at": "<RFC3339 UTC>|null", "reason": "<ModelStateReason>|null"},
  "desired": {"status": "resolved|unavailable", "source": "set-effective-config|unavailable", "model": "<opaque-string>|null", "reason": "<ModelStateReason>|null"},
  "installed": {"status": "installed|absent|unreadable", "source": "installed-runtime|unavailable", "model": "<opaque-string>|null", "reason": "<ModelStateReason>|null"},
  "routing": {"status": "dynamic|pinned|unavailable", "source": "model-preference.toml|unavailable", "reason": "<ModelStateReason>|null"},
  "convergence": {"status": "applied|pending_apply|unknown"},
  "refresh": {"observed": {"status": "fresh|stale|error|unavailable", "checked_at": "<RFC3339 UTC>|null", "reason": "<ModelStateReason>|null"}, "desired": {"status": "fresh|stale|error|unavailable", "checked_at": "<RFC3339 UTC>|null", "reason": "<ModelStateReason>|null"}, "installed": {"status": "fresh|stale|error|unavailable", "checked_at": "<RFC3339 UTC>|null", "reason": "<ModelStateReason>|null"}, "routing": {"status": "fresh|stale|error|unavailable", "checked_at": "<RFC3339 UTC>|null", "reason": "<ModelStateReason>|null"}}
}
```

`ModelStateReason` es el único enum de razones, usado por todas las evidencias y refreshes: `not_checked`, `unsupported_runtime`, `opencode_absent`, `project_unresolved`, `timeout`, `invalid_json`, `output_limit`, `session_limit`, `no_project_root`, `no_submitted_message`, `cache_read_failed`, `probe_failed`, `child_failed`, `not_installed`, `unavailable`. Un campo que no tiene razón usa `null`; no existen enums alternativos por sección. Antes de la primera medición, cada `refresh.*.checked_at` es exactamente `null` y su razón es `not_checked`.

Nunca se publica `session_id`, título, prompt, respuesta, herramientas ni metadata no allow-listed. `observed_at` sólo es no nulo con `observed.status=observed`; todos los modelos pueden ser `null` fuera de su estado resuelto/instalado/observado.

## Reglas e invariantes

| Evidencia | Significado | Fuente y ausencia |
|---|---|---|
| Último envío observado | último mensaje `user/submitted` de la raíz canónica seleccionada; no modelo actual | interfaces oficiales OpenCode; `unobserved` ante ausencia, límite o ambigüedad |
| Default deseado | preferencia efectiva de SET para futuras sesiones | configuración efectiva; no toca la sesión abierta |
| Default instalado | valor releído del artefacto del runtime | proyección local; diferencia implica `pending_apply` |
| Routing | pin o decisión dinámica para trabajo futuro | `model-preference.toml`; no representa ejecución |

- El universo de observación contiene **sólo sesiones raíz** cuya ruta de proyecto canónica es exactamente el proyecto canónico. Hijas/subagentes se excluyen, aun si pertenecen a esa raíz.
- Entre esas raíces, se selecciona por `updated_at` descendente; `session_id` opaco sólo desempata internamente. De la única raíz elegida se toma su último mensaje `user/submitted` válido; el desempate interno de mensajes es `(submitted_at, message_id)` descendente. No hay fallback a otra raíz si la elegida no puede probarse.
- Se llaman exclusivamente `opencode session list --format json --pure` y `opencode export --sanitize --pure`, con ID exacto cuando el export lo requiere. Nunca SQLite privada. El export se procesa y descarta en memoria; SET no lo cachea, registra, reemite ni escribe a temporal.
- La observación completa tiene deadline de **5 s**, como máximo **20 sesiones raíz candidatas** y **1 MiB de stdout total** agregado entre sus children. Exceder cualquiera degrada con el reason único correspondiente; no hay cap por-child que extienda esos máximos.
- `generate()` en [`ai/scripts/generate.py:495`](../../../ai/scripts/generate.py#L495) usa efectiva sólo para instalación local y drift local; `Global/**`, `build --check` y `build --diff` permanecen factory-only conforme ADR-0071.
- Tras confirmación, un lock exclusivo cubre sin interrupción `persistir → generar → instalar → releer`. Un segundo writer del mismo store falla reintentable antes de mutar cualquier archivo o instalación. Si instalar o releer falla, la preferencia durable queda y el estado es `pending_apply`.
- “Dejar que el router elija” borra todos y sólo los pins `[model_pin]`. “Restaurar defaults de SET” borra sólo overrides locales de modelos. La restauración de fixtures debe preservar hosts y subscriptions byte-idénticos.
- Los plugins/rótulos detectados por 049 son estrictamente advertencias read-only: no se ofrece ni ejecuta backup, deshabilitación, edición, borrado o cambio de configuración.
- El primer frame del home simple no hace subprocesses y usa cache o ausencia honesta. `Actualizar estado` hace las mediciones. `Modo experto` es una acción directa del home simple. 049 supersede de 048 cualquier onboarding automático y `first_run`: no se evalúan ni se fuerzan en ese ingreso.

## Alcance, no-goals y paquetes

049 cubre proyección efectiva local, `ModelState`, CLI, consola/modelos y sus regresiones. No cubre cambiar `/model` o una sesión abierta; SQLite privada; retención de conversación; modelos hardcodeados; cambios a `Global/**`; modificación de plugins; lanes; ni limpieza o atribución del árbol preexistente de 045–048.

| Paquete | Resultado |
|---|---|
| A | instalación/drift locales desde proyección efectiva sin modificar la fábrica |
| B | `ModelState` singular, privado y con observación acotada |
| C | home cache-first, experto directo, refresh recuperable y apply serializado |
| D | ayuda, advertencias read-only, regresiones, TTY y huella |

## Auditoría de spec

- **Universo/ausencia:** el universo declara sólo raíces canónicas; raíz ausente, mensaje no enviado, runtime no OpenCode, límite y error tienen outcomes cerrados del enum único.
- **Conflictos:** `/model` temporal no contradice defaults; desired/installed distinto gana `pending_apply`; router-auto y restore tienen universos disjuntos; el lock tiene precedencia sobre un segundo writer; plugin nunca muta.
- **Fixtures que engañan:** lista ya ordenada, hija más nueva, modelos conocidos, cache caliente, y TOML sin hosts/subscriptions. Los AC requieren raíces desordenadas, hija excluida, strings opacas, cache ausente y bytes preservados.
- **Sin verificar para implementación:** campos oficiales que identifican raíz y `user/submitted` en export OpenCode 1.18.14 y el readback por runtime. Si no se prueban, degradan; no habilitan heurísticas.

## Método de huella contractual

Desde la raíz del repositorio, este comando normaliza sólo el valor autorreferente, concatena `ruta + NUL + contenido + NUL` de los cuatro documentos contractuales en el orden indicado e imprime la huella reproducible:

```bash
python3 -c 'from pathlib import Path; import hashlib,re; paths=("docs/specs/049-identidad-honesta-modelos/spec.md","docs/specs/049-identidad-honesta-modelos/acceptance.md","docs/specs/049-identidad-honesta-modelos/proposal.md","docs/specs/049-identidad-honesta-modelos/design.md"); b=b"".join(p.encode()+b"\0"+re.sub(rb"sha256:(?:[0-9a-f]{64}|<CONTRACT_SHA256>)",b"sha256:<CONTRACT_SHA256>",Path(p).read_bytes())+b"\0" for p in paths); print("sha256:"+hashlib.sha256(b).hexdigest())'
```

El valor publicado se reemplaza al final por el resultado de ese comando, que conserva el literal normalizado y evita autorreferencia.
