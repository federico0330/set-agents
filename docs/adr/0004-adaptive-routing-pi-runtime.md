# ADR 0004 — Deterministic adaptive routing with opt-in Pi runtime

## Estado

Approved on 2026-07-24. Superseded in part by ADR-0005 only for the JSON/JSONL routing-journal decision; all
other decisions remain accepted historical context.

## Contexto

SET-AGENTES needs OAuth-backed OpenAI Pro and Claude Max execution without new API keys and needs proportional
flows that avoid a full agent review cycle for simple work. Pi supplies the provider runtime, while routing and
permission invariants must remain owned by SET-AGENTES.

## Opciones consideradas

1. Keep three runtimes and only tune prompts: lowest implementation cost, but no direct Pi OAuth/runtime support.
2. Fork Gentle-AI/RDD: broad doctrine reuse, but imports a workflow and product boundary that do not match
   SET-AGENTES.
3. Add Pi as a generated managed runtime plus a local deterministic router: preserves the existing canonical role
   system and makes route decisions testable and explainable.
4. Add a remote routing service or model-based router: unnecessary operations, privacy, availability, and cost
   surface for a bounded local catalog.

## Decisión

Choose option 3. Pi is opt-in and managed below a SET-AGENTES-owned directory. `route_task` is pure,
deterministic, catalog-bound, and privacy-preserving. Gentle-AI is a doctrinal reference, not a fork. The Pi
OpenCode bridge stays disabled until separately audited and benchmarked.

The Pi security boundary is a common fail-closed dispatch policy, not a command denylist. `pi-subagents` is
parent-only, children have no delegation tool and depth zero, and native gates map versioned IDs to immutable
argv. Telemetry uses an installation-keyed HMAC and private, rotating local files.

No API gateway, database, queue, cache, remote service, or deployment platform is introduced — not yet (YAGNI).
The activation threshold for a durable transactional store is concurrent cross-project writers that cannot be
made safe with per-project atomic files. The activation threshold for a remote control plane is a demonstrated
multi-host coordination requirement that local operation cannot satisfy.

## Consecuencias

- SET-AGENTES owns Pi permission guards because Pi executes with process permissions.
- Existing role sources and separation-of-duty rules remain authoritative across four runtimes.
- Routing behavior can be tested without an LLM or live provider.
- Package installation and OAuth availability become explicit doctor checks and operational dependencies.
- Pi cannot become the default until the 5–10-run opt-in rollout threshold is met.
- The MVP never promotes itself; any default-runtime change remains a separate human decision.
