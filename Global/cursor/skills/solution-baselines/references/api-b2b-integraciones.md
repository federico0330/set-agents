# Baseline — API B2B / integraciones

Caso típico: conectar el sistema del cliente con terceros (MercadoLibre/MercadoPago, ERPs, mensajería,
bancos): consumir APIs externas, exponer webhooks, sincronizar estado entre sistemas que no se conocen.

## Stack golden-path
- **Servicio**: un monolito de integración (ASP.NET Core o NestJS/Fastify) con un módulo por integración
  detrás de un puerto (clean-architecture: el dominio no importa SDKs de terceros).
- **Colas**: tabla outbox en PostgreSQL + worker con reintentos exponenciales. NADA de RabbitMQ/Kafka
  hasta el umbral.
- **Webhooks entrantes**: endpoint que valida firma, persiste el evento crudo YA (tabla inbox) y responde
  200 rápido; el procesamiento es asíncrono desde la tabla.
- **Config/secretos**: por entorno, nunca en repo (secrets-hygiene); tokens de terceros con refresh
  automático y expiración observada.

## Los tres ejes (pre-decididos)
| Eje | Postura | Umbral YAGNI (deviation → ADR) |
|---|---|---|
| Data store | **PostgreSQL**: inbox/outbox + estado de sincronización con versión/fingerprint por entidad | Volumen de eventos > ~1k/s sostenido → broker real (evaluar NATS/Rabbit) |
| API Gateway | **No** para 1-2 integraciones | ≥3 consumidores externos con auth/rate-limit/contratos distintos → gateway o BFF explícito |
| Deploy | **PaaS con worker persistente** (Railway/Fly/VPS); serverless SOLO si no hay worker de cola | Requisito de latencia/webhook con cold-start inaceptable, o worker >1 → VPS/contenedores |

## Forma típica de paquetes
1. Puerto + adaptador de la integración (cliente HTTP, auth, mapeo de errores del tercero a errores tipados).
2. Inbox de webhooks: firma, persistencia cruda, ack rápido, procesador idempotente.
3. Outbox + worker de reintentos con backoff y dead-letter (fila marcada, no borrada).
4. Reconciliación: job que compara estado local vs tercero y repara/alerta divergencias.

## Riesgos recurrentes (y el skill que los audita)
- Webhook procesado en línea y el tercero reintenta → duplicados. Idempotency key + inbox → `db-integrity`,
  `error-handling-http` (idempotencia en mutaciones reintentables).
- Retry sin idempotencia en el LADO SALIENTE (cobrar dos veces) → clave de idempotencia del proveedor
  SIEMPRE que exista; si no existe, fingerprint propio persistido antes del call.
- Estados imposibles por eventos fuera de orden → versionado/fingerprint por entidad, CAS al aplicar.
- Firmas de webhook sin validar o secretos en logs → `security-review`, `secrets-hygiene`.
- Contratos del tercero asumidos de memoria → `context-context7`/docs oficiales; el spec marca UNVERIFIED.
