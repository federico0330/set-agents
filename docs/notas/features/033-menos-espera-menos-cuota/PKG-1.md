# 033-menos-espera-menos-cuota · PKG-1

<!-- notas:auto -->
## Motivo

- objetivo: Una sola dimension opencode: colapsar go-zen/zen/openai-only en un solo valor por area
- complejidad: high
- riesgo: high
- paths: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`, `ai/scripts/generate.py`, `build.sh`, `active-profile`

## Tareas

- [ ] models.toml: 38 mapas de tres lanes pasan a string, conservando el valor go-zen (planned)
- [ ] models_config: sacar LANES, active_profile y auto_profile; adaptar resolve_role y load_role_tiers (planned)
- [ ] setup_models y build.sh: sacar el eje lane de la UI y del flag --profile (planned)
- [ ] AC-1.6: prueba de que un proveedor agotado falla ruidoso o rutea a otro, nunca en silencio (planned)
- [ ] reescribir los 7 archivos de test que fijan las tres lanes conservando su invariante (planned)

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
