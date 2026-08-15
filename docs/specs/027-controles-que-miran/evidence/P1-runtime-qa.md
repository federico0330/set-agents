# P1 runtime QA — CLI ownership gate

Date: 2026-08-14  
Package: `P1-alcance-y-aislamiento`  
Result: **PASS**

## Runtime under test

The canonical production CLI was run directly: `/home/federico/SET-AGENTES/ai/scripts/check-owned-paths.py`.
The disposable Git repository fixture was `/tmp/p1-runtime-qa.Nn1Kmv`, initialized with an empty baseline commit plus a tracked `state.json`:

```json
{"packages":[{"package_id":"fixture-package","owned_paths":["owned/**"]}]}
```

No real feature state, configuration, credentials, or production repository files were used as CLI input. No browser or MCP connector was used: this is a CLI-only runtime surface.

## Scenario 1 — untracked file outside `owned_paths`

Fixture created: `/tmp/p1-runtime-qa.Nn1Kmv/unowned/escape.txt` (untracked).

```text
$ python3 /home/federico/SET-AGENTES/ai/scripts/check-owned-paths.py --state-file state.json --package-id fixture-package --baseline HEAD
exit code: 2
{
  "changed_files": ["unowned/escape.txt"],
  "ok": false,
  "out_of_scope": ["unowned/escape.txt"],
  "owned_paths": ["owned/**"]
}
OWNERSHIP_FAIL
```

**PASS:** the real CLI surfaced the untracked out-of-scope path, emitted `OWNERSHIP_FAIL`, and returned `2`.

## Scenario 2 — untracked file inside `owned_paths`

After removing the first fixture file, fixture created: `/tmp/p1-runtime-qa.Nn1Kmv/owned/within.txt` (untracked).

```text
$ python3 /home/federico/SET-AGENTES/ai/scripts/check-owned-paths.py --state-file state.json --package-id fixture-package --baseline HEAD
exit code: 0
{
  "changed_files": ["owned/within.txt"],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": ["owned/**"]
}
OWNERSHIP_PASS
```

**PASS:** the real CLI surfaced the untracked in-scope path, emitted `OWNERSHIP_PASS`, and returned `0`.

## Code trace

- `ai/scripts/check-owned-paths.py:51-82` obtains individually listed untracked files from `git status --porcelain -z --untracked-files=all` and merges them with the baseline diff.
- `ai/scripts/check-owned-paths.py:95-106` selects Git-derived changes, loads `owned_paths`, and records unmatched paths as violations.
- `ai/scripts/check-owned-paths.py:108-122` prints the JSON result and returns `2`/`OWNERSHIP_FAIL` when violations exist, otherwise `0`/`OWNERSHIP_PASS`.

## Cleanup and limitations

The disposable repository `/tmp/p1-runtime-qa.Nn1Kmv` was removed after these observations. This focused runtime pass verifies only the two requested untracked-file ownership flows; it does not exercise browser UI, MCP, real feature state, credentials, or other ownership/read-only patterns.
