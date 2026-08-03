---
description: Narrative log of what was done and why, in client and engineering language
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Report the narration log for: $ARGUMENTS

With a feature id, read `docs/specs/<feature_id>/bitacora.md` (fall back to
`ai/state/bitacora/<feature_id>.md`). Without arguments, read the `## Bitácora` section of
`ai/state/STATUS.md`. Regenerate first with `python3 ai/scripts/feature-state.py render-status` if the file
is missing or looks stale.

Present it as a story, oldest to newest, preserving both registers: what the client got or stopped risking
(`Cliente:`) and why each instance was necessary (`Ingeniería:`). Close with where the work stands now and
what the next step is. Do not edit files, run gates, or reconstruct the story from chat history — if an
entry is missing from the log, say it is missing rather than inventing it.
