# Baseline — E-commerce / landing con conversión

Caso típico: tienda chica-mediana o landing de producto/servicio donde el objetivo es CONVERTIR (venta,
lead, reserva), con UI brand-grade y pagos locales (MercadoPago primero en Argentina).

## Stack golden-path
- **Frontend**: Next.js en Vercel. Estático/SSG por defecto; SSR solo donde el dato lo exige (stock/precio
  en vivo). Core Web Vitals como gate (web-frontend-fundamentals).
- **UI**: `aesthetic-frontend` + `frontend-design` obligatorios — una landing genérica de template ES un
  defecto de entrega en esta categoría. Design tokens + tipografía deliberada desde el día uno.
- **Catálogo/checkout**: si el cliente no exige plataforma propia, integrar (Tienda Nube/Shopify/Snipcart)
  antes que construir carrito artesanal — construir checkout propio es la deviation que MÁS justificación
  necesita en esta categoría.
- **Pagos**: MercadoPago Checkout Pro (redirect) antes que API de pagos propia; webhooks de pago siguen el
  baseline `api-b2b-integraciones` (inbox + idempotencia).
- **Analytics**: eventos de conversión definidos en el spec (qué es "convertir") + herramienta liviana
  (Plausible/GA4). Sin datos de conversión no hay criterio de éxito medible.

## Los tres ejes (pre-decididos)
| Eje | Postura | Umbral YAGNI (deviation → ADR) |
|---|---|---|
| Data store | Landing pura: **ninguno propio** (CMS/formularios gestionados). Tienda: PostgreSQL para catálogo/órdenes si es plataforma propia | Personalización/recomendaciones → recién ahí evaluar eventos + pgvector |
| API Gateway | **No** | Nunca en esta categoría salvo que mute a marketplace multi-tenant |
| Deploy | **Vercel** (preview deployments por rama = herramienta de venta con el cliente) | Backend con worker/pagos complejos → separar ese servicio a PaaS/VPS, el front queda en Vercel |

## Forma típica de paquetes
1. Sistema de diseño + layout base (tokens, tipografía, componentes núcleo, responsive).
2. Páginas de conversión (hero/catálogo/producto) con contenido real del cliente — nunca lorem ipsum.
3. Checkout/pago o formulario de lead + webhook/notificación + página de éxito/error.
4. SEO técnico + analytics + performance pass (LCP/CLS medidos, no estimados).

## Riesgos recurrentes (y el skill que los audita)
- UI genérica de template → `ux-ui-designer` gate obligatorio (frontend-engineer lo declara en su contrato).
- Estado de pago solo del lado del redirect (usuario cierra la pestaña) → webhook como fuente de verdad,
  redirect solo UX → `db-integrity` + baseline B2B.
- Stock vendido dos veces en el checkout propio → concurrencia (CAS/reserva con expiración) → `db-integrity`.
- Imágenes sin optimizar matando LCP → `performance-scalability` / `web-frontend-fundamentals`.
- Precios/promos hardcodeados en el front → contrato de datos único (el front no calcula precios).
