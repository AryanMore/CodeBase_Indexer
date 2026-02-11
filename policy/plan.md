# Expansion & Ingestion Architecture Plan

## 1. Objective

Introduce a controlled, rulebook-driven context expansion system into the RAG pipeline while keeping:

* Deterministic legality enforcement
* Policy-driven configuration
* Minimal architectural complexity
* Future extensibility toward recursive multi-hop reasoning

This document captures:

* Finalized chunk formats philosophy
* Rulebook structure
* Expansion cost model
* Depth and budget control
* Expansion loop design
* Required ingestion changes

---

# 2. Core Design Principles

## 2.1 Separation of Responsibilities

* **LLM** → Reasoning + deciding when and what to expand
* **Orchestrator** → Enforcement + state management
* **Expansion pipeline (module)** → Legal validation + chunk resolution (functionally part of orchestrator)
* **Rulebook** → Static expansion permissions
* **Formats** → Static structural metadata

No reasoning happens inside the orchestrator.
No legality is decided by the LLM.

---

# 3. Expansion Control Model

## 3.1 Budget (Global Per Query)

Defined in `.env`:

```
EXPANSION_BUDGET=4
```

* Integer only
* Decremented per approved expansion
* Cost determined by rulebook

## 3.2 Depth (Local Per Primary Chunk)

Defined in `.env`:

```
MAX_EXPANSION_DEPTH=1
```

* Depth tracked per primary RAG chunk
* Prevents deep recursive traversal
* Allows architecture to support recursion later

Depth and budget are independent controls.

---

# 4. Expansion Cost Model

## Tier 0 (Cost = 0)

Structural context within file:

* Imports
* Docstrings
* Class header from class function

These are cheap contextual enrichments.

## Tier 1 (Cost = 1)

One-hop semantic expansion via metadata:

* `uses`
* `member_functions`
* `class_name`
* `external_scripts`

No file-based penalty.
Cost reflects semantic hop, not filesystem structure.

---

# 5. Rulebook Structure

Each language has its own rulebook JSON.

Structure:

```json
{
  "chunk_rules": {
    "chunk_type": {
      "allow_expansion": true,
      "expansions": [
        {
          "via": "metadata_field",
          "allowed_target_types": [],
          "cost": 1
        }
      ]
    }
  }
}
```

Notes:

* No depth stored in rulebook
* No budget stored in rulebook
* No file-level logic inside rulebook
* Only metadata-driven expansion allowed

Blind chunks are terminal.
Docstrings and imports are terminal.

---

# 6. Expansion Loop Design

## 6.1 LLM Output Protocol

LLM must output strictly structured JSON:

### Expansion Request

```json
{
  "action": "expand",
  "via": "uses",
  "target_identifier": "function_name"
}
```

### Final Answer

```json
{
  "action": "answer",
  "content": "..."
}
```

No mixed prose + JSON.
Strict protocol.

## 6.2 Expansion Handling Flow

1. Orchestrator receives structured expansion request.
2. Expansion module validates:

   * `allow_expansion`
   * `via` allowed
   * identifier present in metadata
   * target type allowed
   * budget sufficient
   * depth not exceeded
   * chunk not previously visited
3. If approved:

   * Fetch target chunks
   * Deduct budget
   * Update depth tracking
   * Add to context
4. If denied:

   * Return structured denial response
   * Include reason
   * Reinforce rulebook or format as necessary

---

# 7. Structural Reassembly Requirement

When structured chunks are split due to size:

* All fragments retain `identifier`, `file_path`, `chunk_type`
* At retrieval time:

  * If a structured chunk is retrieved
  * Fetch all chunks sharing same `file_path + identifier`
  * Sort by `chunk_number`
  * Merge before sending to LLM

This is not expansion. It is structural integrity restoration.

---

# 8. Required Ingestion Changes

## 8.1 Python

* Attach decorators to their respective functions/classes
* Include decorator calls in `uses`
* Ensure all split structured chunks retain full metadata
* Populate:

  * `uses`
  * `member_functions`
  * `class_name`

## 8.2 JavaScript

* Normalize function forms:

  * FunctionDeclaration
  * FunctionExpression
  * ArrowFunctionExpression
* Populate:

  * `uses`
  * `member_functions`
  * `class_name`
* Extract `javascript_import`

## 8.3 HTML

* Segment structural blocks
* Extract `external_scripts` from `<script src>`
* Do NOT attempt DOM-behavior mapping

---

# 9. Future Evolution Path

Phase 1 (Current Capstone):

* Depth = 1
* Limited budget
* Controlled single-hop expansion

Phase 2:

* Increase depth
* Enable recursive multi-hop traversal

Phase 3 (Cursor-like System):

* Larger budgets
* Smarter expansion heuristics
* Possible dynamic cost tuning

Architecture is already prepared for this progression.

---

# 10. Completion Status

Formats: ✅
Rulebooks: ✅
Expansion Model: Defined
Ingestion Changes: Planned
Expansion Pipeline: To Implement

End of current planning phase.
