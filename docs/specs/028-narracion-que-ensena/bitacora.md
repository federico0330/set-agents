# Bitácora — 028-narracion-que-ensena

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-19T18:30:21+00:00

[2026-08-17T22:28:08+00:00] N1-campos-que-obligan · package-reviewer · started · modelo anthropic/sonnet
Cliente: Mande a alguien de afuera a revisar la narracion que ensena: el codigo estaba escrito pero nadie lo habia mirado con ojo critico.
Ingeniería: package-reviewer read-only sobre f688531, contexto limpio, modelo distinto al escritor (Cursor/Copilot). Cubre N1/N2/N3b contra AC-01..AC-20. Independencia por ADR-0011: proveedor y modelo distintos al implementer.

[2026-08-18T01:06:42+00:00] N2-doctrina-que-explica · package-reviewer · started · modelo anthropic/sonnet
Cliente: revisor independiente cubrió N1, N2 y N3b en una sola sesión sobre f688531
Ingeniería: mismo revisor que N1, misma sesión; todos los hallazgos de 028 bajo docs/specs/028-narracion-que-ensena/evidence/N-package-review.md

[2026-08-18T01:07:40+00:00] N3b-los-campos-donde-se-leen · package-reviewer · started · modelo anthropic/sonnet
Cliente: revisor independiente sobre f688531 cubrió N1/N2/N3b
Ingeniería: misma sesión de revisión independiente; N3b hallazgo N3b-F01 sobre el límite de render vs escritura
