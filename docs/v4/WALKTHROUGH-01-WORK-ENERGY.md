# Walk-through 01: one agent job, done cold with the v4 templates

**Job.** Grade 9 Work and Energy (`BUCKET-PHY-WORK-ENERGY-POWER`), the gap the atlas packet shows:
- the microtopic `MIC-PHY-WEP-ENERGY-DERIVATIONS` has no Core1A units;
- the bucket has no D4 question.

**Done as an agent would:** templates, then fill, then `check`, then library, then renderer, then the page on a tablet width.

**Where the work is kept:**
- The records are fixtures in `tests/fixtures/authoring/wep/`, not library content. Adding them to the library is the Owner's call.
- Every mistake below is replayed in `tests/test_authoring_templates.py` (`TheWalkThroughThroughTheRealGates`).

## Result

| | Before | After |
|---|---|---|
| Renderer gaps for `PRODUCT-PHY-WORK-ENERGY-POWER` (`render_core.py gaps`, floor / reference depth) | 66 / 78 | 64 / 76; closes `AUTHOR_CONSTRUCTION_UNITS` and `CORE2B AUTHOR_PRACTICE`, opens none |
| Library intake findings on the new records | — | 0 |
| Assurance on the package | — | `STRUCTURAL_VALIDITY` PASS, `REFERENCE_INTEGRITY` PASS, 0 new canonical findings |
| Pages | — | Core1A: two units, each with a 4-stage figure and stage chips. Core2B: the transfer task with a safe figure, attempt before solution, lineage check |

Getting there took 14 problems. The first version of `check` passed the records at each of them. The renderer, the library intake or the browser found them later.

## What an agent hits, in order

| # | Where | What happened | Cause | Fixed now by |
|---|---|---|---|---|
| F1 | Start | Nothing an agent reads (README "Agent start here", `docs/method`) pointed at the templates | missing pointer | README item 6; `docs/method/INDEX.md` |
| F2 | Core1A | The microtopic already existed (5 teaching steps); the template was a blank whole microtopic | no "existing record" path | `new core1a --package P --microtopic ID` carries the record over |
| F3 | Core1A | A unit needs a figure; this package had none, and nothing said how to make one (117 hand-drawn SVGs exist, no tool) | no figure template | `core1a/representation.template.json` and `.svg` |
| F4 | Question | Ids, capabilities, families and sources follow package conventions the template did not show | blank template | `new question --package P` offers the package's own ids |
| F5 | Question | The template said "lands in `questions[]`" but not that the product manifest must select it | missing step | destination names `selection.core2a` / `core2b` |
| F6 | Core2B | A D4 transfer task needs a transfer block, a safe figure and novelty, none of which were in the template; only the renderer knew | Core2B blueprint has 0 components | `transfer-question.D1..D4` templates (from the schema, with a note) |
| F7 | `check` | Passed Core1A units that named two figures that did not exist yet | `check` re-implemented a few rules instead of running the gates | `check --into --product` runs intake, depiction and the renderer in place |
| F8 | `check` | Accepted a waiver reason that said "waived for this walk-through" | waivers taken as given | every declared waiver is listed for a reviewer |
| F9 | Assurance | Self-containment stays INCONCLUSIVE: no question in the library (0) declares a `problem_specification`; the recompute engine has 4 models (linear and projectile kinematics), none for energy | missing fields; missing model | templates carry `problem_specification` and `answer_contract`; the energy model is open (below) |
| F10 | Core1A | The unit named a package question as its crux; the renderer requires a question of the product's bank, and this bank has none for Work and Energy | wrong hint | rule in the template; `check` looks for crux questions in the exam banks |
| F11 | Core2B | Protected move set to a TRANSFORM move, and the template's hint ladder supported move 1; library intake requires a DECIDE move that no hint supports | Core2 hint skeleton conflicts with Core2B transfer rules | transfer templates protect MOVE-1 (DECIDE) and move its hint |
| F12 | Assurance | The library intake's transfer rules are a real gate that `check` did not run | as F7 | as F7 |
| F13 | Page | Options showed "(A) (A) The ball...": the page writes the letters, the record repeated them | unstated convention | rule in the template |
| F14 | Page | Figure stages 2–4 showed text with no drawing: the page shows one stage at a time | the STAGED_VISUAL hint does not say each stage must be a complete picture | rule in the templates; SVG skeleton |
| F15 | `check --product` | Found two more after the job "passed": a safe figure bound to a relation it never labels (depiction calls it decoration; nothing ran depiction), and a label past the figure's edge (only reported at the reference depth) | depiction is run by no gate; renderer default is the floor | `check` runs depiction, and the renderer at the reference depth |

## Still open (blueprint and library, not the templates)

- **Blueprints with no components:** Core1, Core1B, Core2A and Core2B. What they need lives only in the renderer's code (F6), so a template for them is written from the schema and the renderer, not generated from a blueprint. WP-C.
- **Blueprint hints to change, with their version bump (WP-A):**
  - STAGED_VISUAL: each stage is a complete picture (F14);
  - QUESTION_BRIDGE / CONSTRUCTION_STEPS: the crux is a bank question (F10);
  - the Core2 hint skeleton versus Core2B protection (F11).
- **Math is shown as typed** (`v^2`, `Delta K`) on the pages, in old records and new. `math_policy` has no executor (G1 in ARCHITECTURE.md).
- **Answer recompute** (ANSWERABILITY) has no model for energy conservation. Without one, a Work and Energy answer is never recomputed.
- **One derivation question in this package covers both units,** so both units show the same worked example. A second, unit-specific question is content work, and no gate notices the duplicate.
- **Method versus gates (Owner decision).** `docs/method` tells authors to "add no new blocker, CI or completeness quota" and to use an advisory self-check. The v4 invariants make these checks blocking. One of them has to give way, and it is the Owner's choice which.
