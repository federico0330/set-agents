# AC-11's apt/dnf/zypper obsidian identifiers were fabricated, not source-verified

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/005-portable-harness|005-portable-harness]] · [[features/005-portable-harness/P2-vault-mandatory|P2-vault-mandatory]]

## Contexto

005-P2's approved contract (AC-11) and ADR-0012's DEC-7 both claimed apt/dnf/zypper obsidian install commands were cited against Obsidian's own published docs, 'not invented'. The security-auditor's review of the finished package flagged this as likely unverified (SEC-007); the finding-verifier then checked the real Debian/Ubuntu package APIs and obsidian.md's own download page live and confirmed there is no installable apt/dnf/zypper obsidian package -- only .deb/AppImage/Flathub/snap. pacman, brew, and winget ARE correct.

## Decisión

tools.toml's [cli.obsidian.install] drops apt/dnf/zypper entirely rather than ship a command that fails or silently installs the wrong package; its doc fallback now points at the real Flatpak/Snap channels. AC-11's literal text (dry-run TOOL_PLAN for all seven managers) is now technically unsatisfiable for three of them by design, not by omission -- the corresponding test was updated to assert their ABSENCE (tests/test_harness.py, test_obsidian_catalog_has_verified_pm_identifiers_plus_doc) instead of silently weakening it. platform_pm()'s seven-manager detection logic is untouched: this is a catalog-content fix, not an architecture change.

## Consecuencias

AC-11 and ADR-0012 DEC-7 both still read as if apt/dnf/zypper work; ADR-0012 DEC-7 got an inline dated amendment note, but acceptance.md's AC-11 prose was deliberately NOT edited (spec text is not silently patched mid-package). A future feature that revisits 005's acceptance criteria should correct AC-11's prose to match; until then this decision is the source of truth for the gap.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
