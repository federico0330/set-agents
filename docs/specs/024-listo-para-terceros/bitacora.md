# Bitácora — 024-listo-para-terceros

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-14T06:20:46+00:00

[2026-08-14T05:11:39+00:00] C1-estado-fuera-del-producto · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que quien clone el proyecto no herede tu historial de trabajo, y que vos no pierdas el tuyo.
Ingeniería: AC-01/02, clase migration. Medido: ai/state pesa 2,3 MB con 23 features, y ONCE modulos de ai/scripts lo leen. El path se MANTIENE -historial a docs/historia/estado-2026-08, ai/state gitignoreado y sembrado desde ai/state.seed-, que es lo que baja el cambio de 11 modulos a cero. Regla que protege al dueno: la siembra solo puebla un ai/state ausente, nunca pisa uno existente.
