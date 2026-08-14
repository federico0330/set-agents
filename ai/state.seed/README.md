# ai/state.seed/

ADR-0047. This is the tracked skeleton of a functional, empty harness — no feature,
no decision, no narrative entry of anyone's real work. `ai/scripts/seed-state.py`
copies it into `ai/state/` (the runtime path every `ai/scripts/` module already
reads and writes, unchanged) the first time `ai/state/` is absent — a fresh clone,
a fresh machine.

Two rules keep this safe:

- The copy only ever happens into an *absent* `ai/state/`. An `ai/state/` that
  already exists — because this machine has real history, or because a previous
  seed already ran — is never touched, never merged, never partially overwritten.
  Running the seed twice is the same call twice: idempotent by construction.
- This directory itself is never written to by anything at runtime. It is edited
  by hand, in the same commits that touch the seeding mechanism, exactly like any
  other tracked source file.

`ai/state/` itself is gitignored (ADR-0047) and carries no history in this
repository going forward; the archive of everything it held up to the migration
lives at `docs/historia/estado-2026-08/`, tracked and readable, read by nobody at
runtime.
