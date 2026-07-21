# Conocimiento global — Seguridad

> Capa CROSS-PROYECTO del "departamento" de security. Vive en el repo SET-AGENTES y se distribuye a cada
> proyecto como `docs/ai/knowledge/_global/security.md` (solo lectura ahí; se refresca en cada
> `sync-project.sh`). Se alimenta promoviendo entradas de la sección `## Candidatos a global` de los
> proyectos cuando aplican a cualquier stack. Nunca secretos, tokens, PII ni datos de un cliente.

## Invariantes
- Seguridad es decisión de día uno, no diferible por YAGNI: authn/authz, aislamiento de tenant y validación de
  todo input externo se diseñan antes de la primera línea, no se agregan después.
- Nunca confiar en input del cliente para autorización: el servidor re-verifica identidad y permisos en cada
  request. Un id/rol que viaja en el body o el token sin re-chequeo del lado servidor es una vulnerabilidad.
- Secretos nunca en el repo, logs, mensajes de error ni en el estado del harness. Se leen de entorno/secret
  manager. Un `.env` real jamás se lee, copia ni imprime.
- Autorización por defecto-denegado: lo no permitido explícitamente se rechaza (rutas, queries por tenant,
  comandos de shell de los agentes).
- Errores hacia afuera no filtran detalle interno (stack, SQL, rutas, existencia de recursos): mensaje genérico
  al cliente, detalle sólo en logs del servidor.

## Errores conocidos y causas raíz
- **IDOR / broken object-level auth**: la query trae por id sin filtrar por el tenant/dueño del caller → un
  usuario lee o edita datos de otro. Causa raíz: confiar en el id del request sin `WHERE tenant_id = :caller`.
- **Enumeración por respuestas distintas**: login/recuperación que responde distinto para "usuario no existe"
  vs "contraseña mala" permite enumerar cuentas. Respuesta y timing uniformes.
- **Secret en el diff**: una key hardcodeada "temporal" que quedó commiteada. Rotar la key comprometida, no sólo
  borrarla del código (git conserva la historia).
- **Auth chequeada sólo en el cliente**: guard únicamente en el frontend (ocultar un botón) sin gate en la API →
  bypass directo por el endpoint.

## Decisiones y porqués
- El `security-auditor` corre en una sola pasada ofensiva+defensiva (ataque + hardening/detección) y es
  MANDATORIO antes del judge cuando el paquete toca auth, dinero, PII o input externo. Porqué: separar "encontrar
  el ataque" de "arreglarlo" duplicaba trabajo sin subir la calidad.
- Migraciones destructivas y flujos de dinero/identidad se tratan como `HUMAN_DECISION_REQUIRED`: el costo de un
  error es irreversible, así que un humano confirma antes.
