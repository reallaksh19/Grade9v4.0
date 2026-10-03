# One method for authoring a learner product

Start with [HOUSE-RULES.md](HOUSE-RULES.md), then [PROTOCOL.md](PROTOCOL.md). The unit author owns the design, records, prototype and revisions; source readers and an independent reviewer contribute evidence and judgement. Nothing in this method authorizes publication. The Owner accepts or rejects one exact rendered digest.

[First-stage review and six-Core guidance](FIRST-STAGE-REVIEW.md) maps each Core's dependencies and defines the current first-stage sequence: establish the real denominator/source state; choose Core2 with a usable supplied bank/source-question corpus or source-grounded Core1 without one; triage canonical difficulty, why the material is difficult and interaction value; author/review the hardest worthwhile vertical slice(s) first inside that route; then present the learner HTML/PDF together with the **complete denominator/coverage view** before generating the remaining Cores. Hard-first is authoring/review priority only; it does not rewrite authentic source order or require Hard-first learner navigation. These are advisory authoring guidelines with no new blocker or CI requirement.

A proposed reusable promotion/audit extension is under review in [LPAP-v1 — Learner Product Audit & Promotion Protocol](LEARNER-PRODUCT-AUDIT-PROMOTION.md) for learner-facing artifacts arriving through a draft PR, upload, or TEST-page intake. While its status remains **PROPOSED**, treat it as design guidance rather than active repository protocol. It defines exact-version intake, deduplication/lineage reconciliation, a common audit kernel, deep profiles for Core2/Core1A/interactive webpages, lighter profiles with content-triggered escalation for the remaining Cores, and promotion/navigation evidence without replacing this authoring method or the Owner's exact-digest publication decision.

| When | Read or use | Artifact |
|---|---|---|
| Scope and source | [Source-reader role](roles/SOURCE-READER.md), [source-reader prompt](prompts/source-reader.prompt.md) | acquisition, inventory, cards, independent `readback[]` |
| Design and prototype | [Unit-author role](roles/UNIT-AUTHOR.md), [unit-author prompt](prompts/unit-author.prompt.md), [golden candidates](../../golden/INDEX.md) | `UNIT.md`, `DESIGN-NOTE.md`, `SELF-CRITIQUE.md`, `WORKLOG.md` |
| Build observations | `python3 Shared/tools/self_check.py --unit SUBJECT/slug`; `python3 Shared/tools/diff_readback.py --subject SUBJECT --node NODE` | local advisory report and existing readback comparison |
| Independent review | [Reviewer role](roles/REVIEWER.md), [reviewer prompt](prompts/reviewer.prompt.md), [REVIEW-GUIDE.md](REVIEW-GUIDE.md), [anti-pattern cards](../../golden/anti/) | review v2 tied to the exact render digest |
| Owner decision | `Shared/tools/accept_product.py` | acceptance record and exact build copy |

The [techniques](../../golden/TECHNIQUES.md) and [anti-pattern cards](../../golden/anti/) are examples for reasoning, not fields to fill. Both v1 goldens are marked CANDIDATE and rendered through `render_core.py`; no candidate is a published product. Research the unit's teaching choices and factual sources afresh.

Reusable templates: [UNIT](templates/UNIT.md), [DESIGN-NOTE](templates/DESIGN-NOTE.md), [SELF-CRITIQUE](templates/SELF-CRITIQUE.md), [WORKLOG](templates/WORKLOG.md), [OWNER-NOTES](templates/OWNER-NOTES.md). `DESIGN-NOTE.md` owns difficulty-first authoring rationale and interaction purpose; `WORKLOG.md` owns current lot/slice execution state and full-denominator coverage state. Do not create a parallel difficulty/lot datastore unless a real shared machine consumer proves the need. Superseded parallel instructions remain in [archive/](archive/) for historical reconstruction.

Record templates (generated from the blueprint and the schemas): [template/v4/README.md](../../template/v4/README.md). They are for the records a renderer reads (Core1A units, questions D1-D4, transfer tasks, figures); the templates above are for planning and notes.

Starting a new job, choosing the first Core, naming a subtopic and the two meanings of "rung": [REQUESTS.md](REQUESTS.md).
