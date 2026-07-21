# Conocimiento global — Arquitectura y patrones

> Capa CROSS-PROYECTO del "departamento" de architecture. Vive en el repo SET-AGENTES y se distribuye a cada
> proyecto como `docs/ai/knowledge/_global/architecture.md` (solo lectura ahí; se refresca en cada
> `sync-project.sh`). Se alimenta promoviendo entradas de la sección `## Candidatos a global` de los
> proyectos cuando aplican a cualquier stack. Nunca secretos, tokens, PII ni datos de un cliente.

## Invariantes
- La arquitectura por defecto es la aburrida: cliente → servidor stateless → una base de datos. Cada desviación
  (cache, cola, réplica de lectura, sharding, API Gateway, microservicio) necesita un trigger concreto que la
  justifique, o se difiere con YAGNI anotando el umbral medible que la activaría.
- Tres ejes NO se deciden por defecto silencioso porque su costo/reversibilidad es alto: tipo de store
  (relacional vs no-relacional vs vector/semántico), si va API Gateway, y la plataforma de deploy (Serverless/PaaS
  vs VPS/IaaS vs managed). Sin ADR que los cubra, se pregunta al usuario antes de implementar.
- Dependencias apuntan hacia adentro (Clean/Hexagonal): dominio no conoce infraestructura. La lógica de negocio no
  importa el ORM, el framework web ni el proveedor externo; esos son detalles enchufables en el borde.
- Contratos públicos (APIs, esquemas, eventos) se preservan salvo que el spec aprobado diga lo contrario; romper
  un contrato es una decisión explícita, no un efecto colateral de un refactor.

## Errores conocidos y causas raíz
- **Deriva a "quick-fix" lo que era una decisión de arquitectura**: "agregá búsqueda semántica a la página de
  docs" parece una línea, pero es una decisión de store. Se escala a scoped con checkpoint de arquitectura.
- **Microservicios/colas prematuros**: complejidad distribuida sin el trigger de escala que la justifique →
  paga latencia y operación sin beneficio. El default monolito con una DB cubre la enorme mayoría.
- **Lógica de negocio en el controller/UI**: reglas que deberían vivir en el dominio quedan pegadas al borde →
  imposibles de testear y duplicadas. Causa raíz: saltarse la capa de dominio "por rapidez".

## Decisiones y porqués
- El `architect` sólo emite ADR para las DESVIACIONES del baseline elegido; lo que es conforme al baseline no
  necesita ADR. Porqué: los ADR documentan por qué te apartaste de lo obvio, no repiten lo obvio.
- `docs/architecture/overview.md` y el índice de ADRs se mantienen vivos: es cómo el equipo (y el cliente
  ingeniero) ven la forma del sistema sin releer cada ADR.
- El paralelismo de paquetes se apoya en `owned_paths` disjuntos: dos slices verticales que no comparten rutas de
  escritura pueden construirse a la vez (ver `ready-packages`); el aislamiento de ownership ES la señal de que es
  seguro paralelizar.
