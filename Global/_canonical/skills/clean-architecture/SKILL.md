---
name: clean-architecture
description: SOLID principles plus Clean/Hexagonal/Screaming Architecture — dependencies point inward, the domain never imports framework or IO, and boundaries are crossed through ports and adapters. Load when designing, implementing, or auditing module structure and dependency direction.
license: MIT
compatibility: opencode
metadata:
  enabled_for: architect, implementer, refactor-specialist, auditor
---

# Clean Architecture

## When to use
Designing a new module, deciding where code belongs, reviewing layering, or breaking a dependency that points the wrong way. Use whenever framework, IO, or transport concerns risk leaking into business logic.

## Principles
- **SRP** — one reason to change per unit; split a class that mixes policy and IO.
- **OCP** — extend via new implementations of an interface, not by editing stable code.
- **LSP** — a subtype must honor the supertype's contract; no strengthened preconditions.
- **ISP** — many small role interfaces over one fat interface; clients depend only on what they call.
- **DIP** — high-level policy depends on abstractions; details (DB, HTTP) depend on the abstraction, not vice versa.
- **Clean/Hexagonal** — concentric layers: entities → use cases → adapters → frameworks.
- **Screaming Architecture** — top-level folders name the domain (orders, billing), not the framework (controllers, models).
- **Ports & Adapters** — domain defines ports (interfaces); adapters implement them at the edge.
- Prefer composition over inheritance; inject collaborators.
- No speculative generality — add abstraction when a second concrete case exists, not before.

## Rules
- The dependency rule is absolute: source dependencies point inward only. The domain imports nothing from outer layers.
- Domain and use-case code must not import frameworks, ORMs, HTTP, filesystem, or env.
- Cross boundaries with interfaces owned by the inner layer; map DTOs at the edge.
- No business logic in controllers, repositories, or framework callbacks.
- One concrete reason justifies one abstraction; delete unused seams.

## Verification ideas
- Grep inner layers for framework/IO imports — there must be none.
- Trace one use case end to end: does control flow cross only inward-pointing interfaces?
- Could you swap the DB or web framework without touching domain or use cases? If not, a dependency leaks.
- Do top-level folder names describe the business or the framework?
