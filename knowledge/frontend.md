# Conocimiento global — Frontend y UX

> Capa CROSS-PROYECTO del "departamento" de frontend. Vive en el repo SET-AGENTES y se distribuye a cada
> proyecto como `docs/ai/knowledge/_global/frontend.md` (solo lectura ahí; se refresca en cada
> `sync-project.sh`). Se alimenta promoviendo entradas de la sección `## Candidatos a global` de los
> proyectos cuando aplican a cualquier stack. Nunca secretos, tokens, PII ni datos de un cliente.

## Invariantes
- La UI nunca queda en genérico "defaults del framework": jerarquía visual, espaciado, tipografía y color con
  intención de marca. Un `ux-ui-designer` de grado marca pasa antes de dar por buena una superficie nueva.
- Accesibilidad no es opcional: contraste suficiente, foco visible, navegable por teclado, labels/roles ARIA
  correctos, `alt` en imágenes con contenido. Se diseña, no se parchea al final.
- Todo estado asíncrono tiene sus cuatro estados diseñados: cargando, vacío, error y éxito. El error es UX de
  primera clase: mensaje accionable en el idioma del usuario, no un stack ni un código crudo.
- Responsive por defecto: unidades relativas, `max-width` en media, y el contenido ancho (tablas, código) scrollea
  en su propio contenedor sin romper el layout de la página.

## Errores conocidos y causas raíz
- **Sólo el happy path**: se construye el estado de éxito y se olvidan loading/empty/error → la primera falla de
  red muestra pantalla rota o en blanco. Causa raíz: no diseñar los cuatro estados desde el arranque.
- **Error técnico filtrado al usuario**: mostrar el mensaje del backend/excepción tal cual → confunde y filtra
  detalle interno. Traducir a un mensaje humano y accionable.
- **Guard sólo visual**: ocultar un control sin gate real en la API da falsa sensación de permiso (ver security).
- **Contraste/foco insuficiente**: texto gris claro sobre blanco o foco invisible → inaccesible; se detecta con
  chequeo de contraste y navegación por teclado.

## Decisiones y porqués
- `frontend-engineer` hace presentación/interacción; la lógica de negocio vive en el backend/dominio. Su salida
  pasa por review estético del `ux-ui-designer`. Porqué: separar "se ve y se siente bien" de "hace lo correcto".
- El `runtime-verifier` ejercita la app corriendo (browser real), no relee código: la QA de una superficie visible
  es observar el comportamiento, con evidencia (URL, screenshots, checks), no una lectura del diff.
