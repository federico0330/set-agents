# Proposal: trusted local routing for Pi runtime recovery

## The problem and business case

The current experimental routing layer cannot reliably prove why a worker was chosen, whether the decision used
real runtime facts, or whether a reviewer is independent from the person who made the change. That leaves the Pi
runtime rollout blocked and makes audit evidence less dependable. Replacing it with a trusted local routing record
reduces avoidable operational risk while preserving the existing working harnesses.

## Proposed solution

We will introduce a local trusted-routing service that separates a work request from facts measured by the harness,
builds decisions only from the approved role/model catalog and live availability, and records each dispatch in a
private local database. The service rejects incomplete facts, ambiguous provider status, and catalog-ID collisions
instead of guessing. Review assignments derive the writer identity from the earlier recorded successful dispatch, not
from caller claims. Operators receive clear, redacted explanations; explanation mode remains a simulation and can
never start or change work.

## Scope

- Trusted routing decisions, stable route IDs, independent review assignment, and local lifecycle evidence.
- Safe one-writer/one-fallback handling, crash recovery, privacy-preserving metrics, retention, and legacy-state
  warnings.
- Supported local persistence on POSIX filesystems only; unsupported Windows/network storage reports that routing is
  unavailable without changing the other Windows surfaces.
- Preservation of the 28 roles, existing OpenCode/Claude Code/Codex runtimes, schema-1 support, and opt-in Pi.

## Explicitly out of scope

- Remote services, gateways, queues, deployments, or hosted databases.
- Changing the role roster, turning Pi on by default, or changing existing runtime behavior.
- Importing or repairing old routing data.

## Assumptions

- The local installation can safely expose the approved catalog and runtime availability facts.
- The existing harness can retain a private local database with suitable filesystem permissions.

## Risks and mitigation

| Risk | Mitigation |
|---|---|
| A request tries to misrepresent risk or capability needs. | Use harness-observed facts as the only authority. |
| A review is assigned to the writer's own model family. | Resolve the writer from the recorded dispatch and exclude its family. |
| A crash or duplicate retry creates two writers. | Use atomic local authorization, a partial-write marker, and a single recorded fallback. |
| A fallback starts after the primary was already sent. | Close the fallback window durably before the primary external call. |
| Sensitive content leaks through logs or reports. | Store and display only allowlisted, redacted operational data. |
| Old state is mistaken for trusted evidence. | Leave it untouched and report a clear legacy-state warning. |
| Local storage cannot safely guarantee locking or permissions. | Do not mutate; report routing as unavailable on unsupported storage. |

## Delivery phases

1. Trusted inputs and decisions — **M**.
2. Durable local lifecycle and recovery — **M**.
3. Operator visibility, retention, and full verification — **M**.

## Measurable success criteria

- Every dispatch-capable route requires harness-observed facts and a harness-built catalog.
- A reviewer/auditor/judge is never assigned to the writer family, and lack of an independent option stops safely.
- Concurrent or restarted runs authorize at most one writer and at most one pre-write fallback.
- Explanations are non-mutating, and all errors/reports remain redacted and machine-readable.
- Invalid facts, provider probes, catalog collisions, or unsafe storage stop safely rather than selecting a fallback.
- Retained reports expose exact p50/p90 for their retained data, including per-route figures; empty groups report no
  value.
- Existing roles/runtimes/schema compatibility pass the full verification suite; Pi remains opt-in.
