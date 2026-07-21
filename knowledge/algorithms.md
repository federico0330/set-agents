# Conocimiento global — Algoritmos y estructuras de datos

> Capa CROSS-PROYECTO del "departamento" de algorithms. Vive en el repo SET-AGENTES y se distribuye a cada
> proyecto como `docs/ai/knowledge/_global/algorithms.md` (solo lectura ahí; se refresca en cada
> `sync-project.sh`). Se alimenta promoviendo entradas de la sección `## Candidatos a global` de los
> proyectos cuando aplican a cualquier stack. Nunca secretos, tokens, PII ni datos de un cliente.

## Invariantes
- La estructura de datos se elige por las operaciones calientes, no por costumbre: lookup por clave → hash/map;
  orden/rango → árbol balanceado o array ordenado; FIFO/LIFO → deque; membership → set. Elegir mal convierte
  O(1) esperado en O(n) por operación.
- Antes de optimizar, medir: la complejidad importa cuando el N es grande y el path es caliente. Un O(n²) sobre
  10 elementos no es un bug; el mismo sobre 100k sí.
- Preferir lo correcto y legible primero; la micro-optimización sin evidencia de cuello de botella es deuda.

## Errores conocidos y causas raíz
- **O(n²) escondido por búsqueda lineal en loop**: `for x in a: if x in lista` con `lista` como array → cuadrático.
  Causa raíz: usar list donde correspondía set/dict. Se arregla con un set de membership.
- **Recalcular lo mismo en cada iteración**: invariantes de loop que se computan adentro en vez de una vez fuera.
- **Ordenar de más**: re-ordenar en cada paso cuando alcanzaba mantener la estructura ordenada o usar un heap.

## Decisiones y porqués
- El `package-reviewer` incluye complejidad/escalabilidad algorítmica en su checklist; no hace falta un agente
  aparte salvo que el paquete sea intensivo en algoritmos.
- Lógica dura (concurrencia, transacciones atómicas, reglas de dinero, seguridad) NO la escribe el modelo leaf
  barato: un primer borrador flojo justo en esa lógica genera más retrabajo de auditoría del que ahorra. Se rutea
  a un implementer fuerte (hosted) desde el plan del paquete.
