# Por que el harness agota cuotas: convierte un prompt humano en N prompts de proveedor

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator

## Contexto

Federico pregunto si el harness es lo que le quema las cuotas. Medicion con ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10: 246 sesiones, 252.9M de input, 14.9M de output y 5.9G de cache_read (92% del total de 6.4G). O sea, 246 despachos en ocho dias, cada uno releyendo un contexto enorme. La documentacion de GitHub (docs.github.com, about-premium-requests, consultada 2026-08-18) dice que Copilot cobra POR REQUEST, no por token, que Pro trae 300 premium requests al mes y Pro+ 1500, y que las acciones autonomas de una sesion NO cuentan aparte: solo cuentan los prompts que uno manda.

## Decisión

La conclusion medida es que el harness no gasta de mas por prompt: gasta porque multiplica prompts. Cada spawn que el orquestador despacha por CLI es, para el proveedor, un prompt nuevo iniciado por el usuario, no una tool call autonoma adentro de una sesion. 246 despachos contra un tope de 300 mensuales explica exactamente 'dos prompts mios = un mes de cuota'. En opencode-go el mecanismo es otro pero el efecto es igual: tope diario, y el coordinador solo ya lo agotaba.

## Consecuencias

Dos consecuencias practicas. Una: en Cursor la delegacion es por subagentes NATIVOS adentro de la misma sesion, asi que no hay abanico entre proveedores; por eso 032 lo modela como runtime anfitrion y no como lane de ruteo. Dos: el numero a mirar cuando se elige un plan no es tokens sino cantidad de despachos por paquete, y hoy ese numero vive en models.toml [routing.budgets] (feature_spawns_per_package = 12).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
