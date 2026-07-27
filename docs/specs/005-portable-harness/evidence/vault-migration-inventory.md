# Evidence — real vault migration inventory (AC-13 / T-205)

Gathered read-only by the orchestrator on 2026-07-27, before package planning. The spec's own audit records
that the product-analyst **could not** verify this ("Could not verify: the real-world content of the four
`~/iey/` vault directories… the migration task (AC-13) must re-verify the actual file list and any conflicts
at implementation time"). This file closes that gap with measured facts. The implementer MUST still re-verify
at execution time — filesystem state can change between now and then — but the migration is no longer being
planned blind.

## Observed state

Every one of the four `<vault>/Proyectos/<name>` entries is a **real directory**, not a symlink — i.e. all
four are in the legacy `--private` (vault-resident) topology, and all four target repos exist on disk.

| Project | Vault files | Repo exists | Repo `docs/notas/` | Migration shape |
|---|---|---|---|---|
| `iey-ai` | 13 | yes | **real dir, 2 files** | **merge** (see below) |
| `SistemaOrganizacionCobros` | 9 | yes | absent | pure move |
| `ScrappingML` | 6 | yes | absent | pure move |
| `pymepilot` | 1 | yes | absent | pure move |

**Total: 29 files.**

## The only non-trivial case: `iey-ai`

`~/iey/iey-ai/docs/notas/` already exists as a real directory holding two files that are **not** harness-
generated notes:

- `analisis-puntos-de-dolor-2026-07-23.md`
- `README.md`

The vault side holds 13 harness-generated notes (`00 - Proyecto.md`, `features/replenishment-v2.md`,
`features/sync-ventas.md`, and 10 package notes under `features/replenishment-v2/`).

**Name-collision check: empty set.** No path under the vault directory matches any path under the repo
directory. So the migration into `iey-ai` is a clean union — AC-13's byte-compare-and-abort rule
(`VAULT_LINK_CONFLICT`) has nothing to trip on here, and the two pre-existing human files must survive
untouched.

## Consequences for T-205

1. **No conflicts are predicted in any of the four projects.** If the implementation's `--dry-run` reports a
   conflict, that is new information since 2026-07-27 and a `HUMAN_DECISION_REQUIRED` trigger per the spec —
   not something to resolve by picking a side.
2. **`iey-ai` proves the merge path is required**, not just the pure-move path. An implementation that only
   handles "repo side absent" would silently do the wrong thing (or refuse) on the one project that matters
   most (13 of the 29 files).
3. **The two pre-existing `iey-ai` files are not harness artifacts** and must not be moved, renamed, or
   folded into a `notas:auto` block. They live outside the generated region by definition.
4. The vault directories are the ONLY copy of these notes: they are absent from every target repo's git
   history (the link was lost 2026-07-23). Any destructive step before a verified copy exists is
   unrecoverable.

## Reproduction

```sh
cd ~/iey/obsidian/Proyectos
for p in */; do n="${p%/}"
  [ -L "$n" ] && echo "$n: symlink" || echo "$n: real dir ($(find "$n" -type f | wc -l) files)"
done
comm -12 <(find ~/iey/obsidian/Proyectos/iey-ai -type f -printf '%P\n' | sort) \
         <(find ~/iey/iey-ai/docs/notas      -type f -printf '%P\n' | sort)
```
