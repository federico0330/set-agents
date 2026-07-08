---
name: data-structure-selection
description: Pick the right data structure by access pattern BEFORE writing code — the 8 fundamentals (array, linked list, stack, queue, hash table, BST, heap, graph) mapped to the operation that dominates (read, insert/delete, priority, relationships) with their time-complexity tradeoffs. Load when implementing logic that stores, looks up, orders, or traverses data, or when reviewing such code.
license: MIT
metadata:
  enabled_for: implementer, architect, performance-auditor
---

# Data-structure selection

## When to use
Before writing any code that stores, looks up, orders, queues, or traverses a collection. Choosing the
structure that fits the dominant operation is a design decision, not an afterthought — the wrong pick turns an
O(1) path into O(n) at scale. Complements `performance-scalability` (which audits queries/loops after the fact);
this skill fixes the in-memory structure up front.

## First question: what is the dominant operation?
Decide this before picking a structure.
- **Read / random access by key or index** → Array (by position) or Hash Table (by key).
- **Frequent insert/delete in the middle** → Linked List.
- **Always touch the most-recent / highest-priority item** → Stack, Queue, or Heap.
- **Relationships between entities** → Graph.
If two operations compete, favor the one on the hot path and name the tradeoff.

## The 8 fundamentals
1. **Array** — random access by index in O(1); cache-friendly, compact. Best for read-heavy, fixed-ish
   collections. AVOID frequent insert/delete in the middle (shifts every later element, O(n)).
2. **Linked List** — O(1) insert/delete once you hold the node; no random access (traverse node by node, O(n)).
   Use when the collection mutates constantly and you rarely index into it.
3. **Stack (LIFO)** — last in, first out. Undo/redo, call stacks, expression/syntax validation, backtracking,
   DFS.
4. **Queue (FIFO)** — first in, first out. Messaging, event handling, server request buffering, background job
   processing, BFS frontier.
5. **Hash Table** — the workhorse: average O(1) lookup/insert/delete by unique key. The DEFAULT for
   dictionaries/maps, caches, deduplication, and frequency counting. Watch for collisions and unstable ordering.
6. **Binary Search Tree (balanced)** — ordered data with O(log n) search/insert/delete AND in-order traversal.
   Use when you need sorted order or range queries, not just point lookups (filesystems, the DOM, hierarchies).
7. **Heap / Priority Queue** — O(1) peek at the min/max, O(log n) push/pop. Indispensable for "always process
   the highest/lowest priority next": Dijkstra/A*, schedulers, top-K.
8. **Graph** — nodes + edges for complex relationships (social graphs, recommendations, routing, dependencies).
   Use **adjacency lists** for sparse graphs (scales in memory); **BFS** to explore by levels / shortest path in
   unweighted graphs, **DFS** for reachability/cycles.

## Rules
- State the dominant operation and the chosen structure in a one-line comment or the task note when the choice
  is non-obvious — so the auditor can check it.
- Consider time complexity at 10×/100× the data before committing; a linear scan inside a hot loop is a finding.
- Prefer the most **compact** structure that fits the problem — memory is scarce (this often runs on small local
  models / constrained RAM); do not reach for a graph/tree when a hash table or array suffices.
- Do not hand-roll a structure the standard library already provides correctly (dict/map, deque, heapq, set).

## Inputs / Outputs
- In: the task's data-access needs (what is stored, how it is looked up/ordered/traversed, expected volume).
- Out: the structure choice justified by the dominant operation and its complexity, realized in the diff.
