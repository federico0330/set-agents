# 041 — Code literacy lint

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · señal `public-contract`.

## Alcance

`narration_lint.py`: on `--result done|blocked` with `--milestone yes`, `--tech` must include `file:line`.

## Criterios

- **AC-01** Missing `file:line` in milestone `--tech` → `TECH_EVIDENCE_REQUIRED`.
- **AC-02** Tests in `tests/test_narracion_contrato.py` or `tests/test_harness.py`.

## ## Supersedes

- none
