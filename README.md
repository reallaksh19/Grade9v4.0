# Grade9V3

Self-study learner-material production system for **Physics, Mathematics and Chemistry**, **CBSE grades 9–11** (with explicit IIT-JEE tier classification where applicable).

**Current Owner progression:** Physics is sequenced **Grade 9 → Grade 10 → Grade 11**, with **Grade 9 first**. Mathematics/Chemistry and cross-subject infrastructure remain available, but they are not the present completion target.

**Learner outcome:** make the learner increasingly capable of deciding what she knows, discovering with little external steering what she does not know, repairing the right Physics gap, and independently verifying a solution. Grade 9 is complete enough when the foundation is usable for Grade 10—not when every optional extension is exhausted.

## Agent start here

If you are an agent or maintainer entering this repository without prior conversation context, **do not plan from issue titles, old roadmap documents, or repository breadth**. Read these first:

1. [`relay/PROTOCOL_SELECTION.yaml`](relay/PROTOCOL_SELECTION.yaml) — which engineering protocol is active. It selects **V3.1**, a recorder: it records and reconstructs work and is never permission to start or stop it. Work state lives in `relay/STATE.yaml` and `relay/WORK/`.
2. [`docs/method/INDEX.md`](docs/method/INDEX.md) — how one learner product is authored, reviewed and accepted: house rules, protocol, roles, templates. The Owner alone publishes, by accepting one exact rendered digest.
3. [`docs/method/FIRST-STAGE-REVIEW.md`](docs/method/FIRST-STAGE-REVIEW.md) — which Core to show first and what the first-stage packet contains. A Core the Owner requests wins; otherwise supplied questions start with Core2 and a syllabus alone starts with Core1.
4. To start a job from raw questions or a syllabus, use [`public/raw-intake/index.html`](public/raw-intake/index.html) or `python3 Shared/tools/raw_intake.py --input request.json`. It never returns a hold: every gap becomes research or authoring work. [`docs/method/REQUESTS.md`](docs/method/REQUESTS.md) explains who chooses the first Core, how a subtopic is named, and the two meanings of "rung".
5. For programme intent (Grade-9 Physics first, learner independence) read [`agents/relay/roadmap/OVERALL_ROADMAP.yaml`](agents/relay/roadmap/OVERALL_ROADMAP.yaml) and [`ODR-0003`](agents/relay/roadmap/owner-decisions/ODR-0003-G9-PHYSICS-INDEPENDENCE.yaml).
6. To author a record (a Core1A concept, a Question Bank question at D1-D4, a Core2B transfer task, a figure), start from [`template/v4/README.md`](template/v4/README.md): `python3 Shared/tools/authoring_templates.py new ...` makes the template for your package, and `check FILE --into <package> --product <manifest>` runs the library intake and the renderer on it before it joins. What the Owner approves first (scope, D1-D4 targets, rung ladders) comes from `authoring_templates.py packet atlas|rungs`.

**`agents/relay/` is frozen history.** `relay/PROTOCOL_SELECTION.yaml` records it as `READ_ONLY_HISTORY` since 2026-09-22. Its `REPO_STATE.yaml` describes the repository at that time, including `execution: WAITING`, `can_continue: false` and `material_authority: NONE`; those values are a snapshot, not an instruction, and are not a reason to stop. Take intent from its roadmap and Owner decision records, and take permission to work from the Owner's request in front of you.

Do not copy live state (percent, work package, active EP) into this README as a second state store; follow the structured sources instead.

The other roadmap-like documents remain useful, but they have different roles:

| Document | Role |
|---|---|
| [`docs/PROGRAM-PLAN.md`](docs/PROGRAM-PLAN.md) | Product/architecture programme context; not live execution authority |
| [`docs/ROADMAP-LEARNER-READY.md`](docs/ROADMAP-LEARNER-READY.md) | Learner-readiness conceptual/historical predecessor; current Grade-9 progression intent is the roadmap + ODR-0003 above |
| [`docs/PLAN-R0-R2.md`](docs/PLAN-R0-R2.md) and [`docs/PLAN-R3-R4.md`](docs/PLAN-R3-R4.md) | Prior execution plans retained as engineering history |
| [`docs/FUTURE-ROAD-PLAN.md`](docs/FUTURE-ROAD-PLAN.md) | Evidence-gated ideas and anti-overarchitecture guardrails; the Grade-9 scope/exit items promoted by RM-0006 are no longer merely future ideas |

Six learner products per subtopic bucket:

| Product | Purpose |
|---|---|
| Core1 | Compact basic notes / semantic orientation |
| Core2 | Source questions with ladder hints, source identity and answers |
| Core1A | Declarative detailed teaching, by intrinsic subtopic difficulty |
| Core1B | Open-ended conceptual reconstruction (self-tutor) |
| Core2A | Purpose-adjusted practice with complete solution breakdowns |
| Core2B | Supported application and transfer |

## Shape

```
Shared/            subject-neutral engine — no subject, topic or gate identifier may be hardcoded here
  roles/           the six Core role specifications
  gates/           technical engineering gate schema + validator        (P2)
  library/         microtopic library engine: intake, promotion, resolver (P3)
  publication_host/ composition, closure, storage, audit, figures        (P1)
  tools/           guardrails and generators
Physics/ Mathematics/ Chemistry/
  adapter/         subject contract: validator families, representation vocabulary,
                   equation semantic fields, curriculum bindings
  gates/           subject gate data, grades 9–11
  library/         microtopic packages
  content/         authored runs and published products
tools/             topic library browser, run builder, portal            (P4)
docs/              program plan and architecture
```

The governing rule: **subject and topic variation is governed data, never a branch in engine code.** `Shared/` is checked for this automatically — see `Shared/tools/topic_independence_guard.py`.

## Running it

```sh
# compile one bucket from its library into publication inputs
python3 Shared/library/compile_inputs.py Mathematics/library/*.json \
  --bucket BUCKET-LINEAR-EQUATION --subject Mathematics \
  --topic-id MATH-LINEQ-G9 --title "Linear equations in one unknown" --out /tmp/lineq

# publish through that subject's adapter
python3 Mathematics/run.py publish --plan /tmp/lineq/plan.json \
  --baseline /tmp/lineq/baseline.json --source-root /tmp/lineq --out /tmp/lineq/publication

# research-first job from raw questions/syllabus (see docs/RESEARCH-FIRST-WORKFLOW.md)
python3 Shared/tools/raw_intake.py --input request.json
python3 Shared/tools/render_core.py build --manifest product.json --out /tmp/job
python3 Shared/tools/quality_gate.py /tmp/job --subject Physics --product-id P

python3 -m unittest discover -s tests -p "test_*.py"   # full suite
python3 Shared/tools/topic_independence_guard.py       # engine carries no subject
python3 Shared/tools/build_manifest.py                 # regenerates the manifest and tools/data.js
```

A committed publication pins a snapshot of the engine that produced it, and the suite re-verifies every committed run. So after changing the engine or a subject adapter, refresh them:

```sh
python3 Shared/tools/republish.py            # verify every committed run against its snapshot
python3 Shared/tools/republish.py --write    # refresh them
```

`--write` refuses if the composed pages or figures would change, because that is a change to what a learner reads rather than a routine refresh. Pass `--accept-output-change` when you mean it, and say so in the commit message.

`tools/index.html` opens over `file://` with no build step.

## Status

Two subjects publish end-to-end: Physics (relative motion, frozen as the port oracle) and Mathematics (linear equations, compiled from its library on demand). Chemistry has a contract but no library yet.

For current engineering execution, use the V2.5 relay sources in **Agent start here** above. [docs/PROGRAM-PLAN.md](docs/PROGRAM-PLAN.md) remains product/architecture programme context and records what earlier phases established. **Nothing here claims independent academic review, learner release or curriculum authority** — machine checks establish structure, custody and supported computation, not that an explanation teaches.

## Provenance

Architecture derives from the V3B work in `reallaksh19/Common` (draft PR #364, branch `draft/core-relay-architecture-review-20260913`), with adaptations from the parallel tracks in that repository: PR #350/#383 (Physics engineering gates, curriculum-scope binding, authority delegation) and PR #395 (Mathematics observability, subtopic intelligence library, topic-independence guarding). Those tracks are referenced and adapted, never copied wholesale.