# Baseline — Scraping + datos / ML

Caso típico: recolectar datos de sitios/APIs de terceros, normalizarlos, almacenarlos con historia y servir
features (precios, stock, leads, señales) a un consumidor humano o a un modelo.

## Stack golden-path
- **Scraping**: Python. httpx/requests + selectolax/BeautifulSoup para HTML estático; Playwright SOLO para
  páginas que realmente renderizan en JS (es 10× más caro de operar). Un módulo por fuente con contrato
  común (`fetch → parse → normalize → upsert`).
- **Orquestación**: cron/systemd timers al principio. NADA de Airflow/Prefect/colas hasta el umbral.
- **Almacenamiento**: PostgreSQL con tablas raw (payload crudo + fetched_at) separadas de tablas
  normalizadas. El raw es el seguro contra reprocesos.
- **ML**: empezar con features + heurísticas/estadística en SQL/pandas; un modelo (sklearn/XGBoost) recién
  cuando hay métrica de negocio que lo justifique y datos etiquetados. Servir por batch antes que online.

## Los tres ejes (pre-decididos)
| Eje | Postura | Umbral YAGNI (deviation → ADR) |
|---|---|---|
| Data store | **PostgreSQL** (raw + normalizado). Parquet/duckdb para análisis ad-hoc | Embeddings/búsqueda semántica sobre texto scrapeado → pgvector; volumen > ~50M filas calientes → evaluar particionado antes que otra DB |
| API Gateway | **No.** Los consumidores son internos | Se vende el dato como API a terceros (rate limiting, keys, contratos) |
| Deploy | **VPS barato** (los scrapers necesitan IP estable, cron y disco; serverless complica Playwright y timeouts) | Escala horizontal real de workers o necesidad de IP rotativas gestionadas |

## Forma típica de paquetes
1. Fuente nueva: fetch+parse+normalize+upsert con fixture de HTML real congelado como test.
2. Esquema/migraciones de normalizado + reglas de dedupe/merge.
3. Scheduling + observabilidad mínima (última corrida OK/fail por fuente, alerta simple).
4. Features/consultas de consumo (o el modelo, como paquete propio con su métrica).

## Riesgos recurrentes (y el skill que los audita)
- Parser que "funciona" con el fixture pero muere con el sitio real (selectores frágiles, layouts A/B) →
  test con HTML real + tolerancia a campos ausentes; `audit-diff` exige el caso ausente.
- Sin idempotencia en upserts: corridas repetidas duplican filas → `db-integrity` (clave natural + ON CONFLICT).
- Ausencia como señal: "el producto ya no está" es dato, no error → spec debe definir universo (product-analyst).
- Bans/rate limits: respetar robots/ToS del cliente, backoff con jitter, User-Agent honesto → riesgo legal
  es decisión del CLIENTE (Question policy), no del implementador.
- Playwright en todas las fuentes "por las dudas" → costo operativo; auditar la elección por fuente.
