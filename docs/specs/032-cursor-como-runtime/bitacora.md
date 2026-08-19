# Bitácora — 032-cursor-como-runtime

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-19T18:30:21+00:00

[2026-08-18T14:16:01+00:00] orchestrator · blocked
Cliente: Aviso honesto: esta tanda la escribi y la probe yo mismo, sin un revisor independiente, porque la sesion tiene la delegacion desactivada. Los tests estan y pasan, pero la revision cruzada que el harness normalmente exige quedo pendiente.
Ingeniería: La doctrina dice que quien implementa no aprueba su propio trabajo, y esta sesion corre bajo una instruccion de entorno que prohibe invocar otros agentes. Por eso los dos paquetes quedan con las tareas completas y el gate corrido, pero sin aceptar: aceptarlos seria firmar una revision que nadie hizo.
Aprendimos: La prohibicion de delegar no bloquea el trabajo, bloquea la aceptacion: se puede entregar codigo probado y dejar el sello pendiente sin mentir en el estado.
Conviene ahora: Cuando haya un proveedor con cuota, correr un revisor independiente sobre los dos paquetes y recien ahi aceptarlos.
Por qué ahora: Registrar la degradacion es la unica forma de que despues no se lea como un paquete aceptado normalmente.
Alternativa: La alternativa era aceptarlos igual apoyandose en que los tests pasan, o revisarlos yo mismo con contexto limpio; las dos convierten la separacion de deberes en un tramite.

[2026-08-18T14:16:24+00:00] C1 · orchestrator · done
Cliente: Cursor ya puede correr el harness: quedan instalados los 28 roles y las 42 habilidades, y cada proyecto recibe las reglas y los comandos. Ningun rol elige modelo por su cuenta: usan el que vos elijas en Cursor, justamente para que no vuelva a pasar lo de las cuotas.
Ingeniería: El generador armaba artefactos para cuatro runtimes y Cursor no era uno, asi que abrir un proyecto ahi dejaba al agente sin roles ni doctrina. Ahora emite un quinto arbol donde cada rol hereda el modelo de la sesion y el permiso de solo lectura sale del mismo predicado que ya usaba el sandbox de Codex (ai/scripts/generate.py:494).
Aprendimos: Cursor tambien lee subagentes desde los directorios de Claude Code, pero su frontmatter propio no coincide con el de ese runtime, asi que el atajo de reusar la instalacion existente habria mentido sobre lo que el agente puede hacer.
Conviene ahora: Revision independiente de los dos paquetes, y hooks de evento de Cursor como trabajo siguiente.
Por qué ahora: Federico agoto las cuotas de opencode, codex y claude; Cursor es el unico runtime pago disponible y era el unico que el harness no sabia configurar.
