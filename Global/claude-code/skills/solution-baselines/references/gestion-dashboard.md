# Baseline — Webapp de gestión / dashboard (CRUD + auth + roles + reportes)

Caso típico: sistema interno de operaciones para una pyme (cobros, stock, clientes, turnos), pocos usuarios
concurrentes (< 200), datos relacionales, reportes tabulares y algún gráfico.

## Stack golden-path
- **Backend**: ASP.NET Core (si el cliente/equipo es .NET) o Next.js API routes/NestJS (si es JS). Monolito
  en capas con dominio aislado (clean-architecture skill aplica entera).
- **Frontend**: Next.js + shadcn/ui, o Razor/Blazor si el backend es .NET puro y no hay SPA real que
  justifique dos runtimes. Tablas con paginación servidor SIEMPRE.
- **Auth**: proveedor gestionado (Supabase Auth / ASP.NET Identity) con roles simples (admin/operador/
  lectura). Nunca auth artesanal.
- **Reportes**: SQL directo con vistas/consultas dedicadas; exportar CSV antes que PDF (el PDF casi siempre
  es un no-goal disfrazado).

## Los tres ejes (pre-decididos)
| Eje | Postura | Umbral YAGNI (deviation → ADR) |
|---|---|---|
| Data store | **Relacional (PostgreSQL)**, normalizado, migraciones versionadas | Búsqueda semántica/embeddings pedida explícitamente → recién ahí evaluar pgvector (NO un vector DB aparte) |
| API Gateway | **No.** Monolito con un cliente | Tercer consumidor externo de la API con contratos/limiting propios |
| Deploy | **PaaS** (Vercel/Railway/Fly) o el hosting que el cliente ya paga; DB gestionada (Supabase/Neon) | Requisito de datos on-premise/regulatorio, o costo PaaS > VPS×2 sostenido 3 meses |

## Forma típica de paquetes
1. Dominio + persistencia de la entidad núcleo (modelo, migración, repositorio, reglas).
2. API + validaciones + errores tipados (409/404, middleware global — error-handling-http).
3. UI del flujo principal (lista paginada + alta/edición + estados de error — frontend-error-ux).
4. Reportes/exportes (si están en alcance) como paquete propio.

## Riesgos recurrentes (y el skill que los audita)
- Paginar en memoria y N+1 en listados → `performance-scalability` (bloqueante, no "V1 aceptable").
- Confirmaciones multi-entidad sin transacción atómica; concurrencia optimista ausente → `db-integrity`.
- Roles chequeados solo en UI, no en servidor → `security-review` (authZ por objeto).
- Dinero en float → `db-integrity` (decimal/integer-centavos, decidido día uno).
- Auditoría de intentos fallidos ausente (quién intentó qué) → `db-integrity`.
