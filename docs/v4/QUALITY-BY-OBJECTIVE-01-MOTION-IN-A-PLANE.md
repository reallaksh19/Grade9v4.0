# Quality by objective 01: Motion in a Plane, for one learner

**What this is.** Twelve review questions that judge a question's hint ladder, figure, helpers and misconceptions against one learner and one question.
- Each question has a clear objective: a verb and a named target, filled from the record.
- Each is answered in words: YES, PARTLY or NO, with the line that shows it.
- Nothing is counted.

**Worked on:** Motion in a Plane (`PRODUCT-PHY-KIN-2D-MOTION`), Core 2, for a learner who knows about half of it and finds it hard.

**Why counting is not enough.** For this product the renderer reports 2 gaps at the floor depth (two figures that do not mount) and 58 at the reference depth:
- 50 are presence or counts ("HINT_LADDER has 3 of the 5 rungs", "REPRESENTATION is absent");
- 5 are figure label sizes;
- 2 are the unmounted figures;
- 1 is a missing link to the toughest question.

Apart from the label sizes, none of them catches what section 5 lists. That list includes:
- a hint that repeats what the page already shows;
- a trap panel that gives the method away before the attempt;
- figure stages that are fragments;
- a "Key move" that is not the key move.

## 1. The learner

The Owner's description: hard topic, about 50% known; consolidating and aiming to excel, perhaps in a competitive exam; working from Core 2 or the syllabus.

The learner-profile schema stores a percentage but never selects anything from it ("a summary the system stores and never computes from"). So the 50% is written per capability:

| Capability | Held | For this learner |
|---|---|---|
| `CAP-VECTOR-SIGNED-COMPONENT` | DEMONSTRATED | resolves a launch velocity into signed components |
| `CAP-KIN-CONSTANT-ACCELERATION` (1D) | DEMONSTRATED | uses the 1D equations |
| `CAP-KIN-2D-INDEPENDENT-COMPONENTS` (R1) | DEMONSTRATED | one clock for x and y in standard problems |
| `CAP-KIN-2D-CONSTANT-ACCELERATION` (R2) | UNCERTAIN | does not reliably check, axis by axis, whether the 1D equations apply |
| `CAP-KIN-PROJECTILE-MODEL` (R3) | UNCERTAIN | has R, H and T for a same-height flight; does not yet choose the event condition, or notice when a shortcut's conditions fail |
| `CAP-RELATIVE-V` | UNCERTAIN | has met relative velocity for constant velocities only |

The standard half is in place; the model-choice half is not. That is the 50%.

- **Hard** describes the questions, not the concept. The library badges all three microtopics MEDIUM. For this learner the hard part is the Core 2 past papers at D3–D4.
- **Purpose:** PRACTICE now, aiming at COMPETITION (from the purpose vocabulary: mixed, timed, minimum support).
- **Support posture:** STANDARD. The ladder stays closed until the learner asks.
- **What this asks of every hint, figure and helper:**
  - don't re-teach what is held;
  - aim at the question's non-standard feature;
  - leave the decisive move to the learner.
- **Confirm it, don't assume it.** The research-first workflow starts with a short diagnostic (`min_items: 3`) and adjusts support from actual attempts. Use three of the library's own diagnostic prompts, one per rung, each answered with a reason:
  1. R1: "May x(2 s) be combined with y(3 s) to describe the particle's position?"
  2. R2: "If a_x is constant but a_y changes with time, may the same constant-acceleration displacement formula be used exactly on y over the whole interval?"
  3. R3: "A ball launched from a roof lands on the ground below. May the same-height time-of-flight shortcut be used without checking the vertical displacement?"

  Scoring: right answer with the right reason → DEMONSTRATED; right answer with a weak reason → UNCERTAIN; wrong → MISSING.

**The profile as a record.** It validates against `Shared/library/learner-profile.schema.json`. An agent may only write `SYNTHETIC_TEST`. For a real learner it becomes `OWNER_ESTIMATE`, until the diagnostic replaces the estimates.

```json
{
  "profile_id": "PROFILE-PHY-KIN2D-CONSOLIDATING-50",
  "label": "Motion in a Plane: about half known, finds it hard, consolidating toward competitive exams",
  "provenance": "SYNTHETIC_TEST",
  "held": {
    "CAP-VECTOR-SIGNED-COMPONENT": "DEMONSTRATED",
    "CAP-KIN-CONSTANT-ACCELERATION": "DEMONSTRATED",
    "CAP-KIN-2D-INDEPENDENT-COMPONENTS": "DEMONSTRATED",
    "CAP-KIN-2D-CONSTANT-ACCELERATION": "UNCERTAIN",
    "CAP-KIN-PROJECTILE-MODEL": "UNCERTAIN",
    "CAP-RELATIVE-V": "UNCERTAIN"
  },
  "knowledge_percentage": 50,
  "support_posture": "STANDARD",
  "observation_refs": [],
  "owner_waiver": {
    "instruction_ref": "docs/v4/QUALITY-BY-OBJECTIVE-01-MOTION-IN-A-PLANE.md",
    "instruction": "Review profile: used to judge hints, figures, helpers and misconceptions, never to route a learner. The held map is the Owner's '50%, hard' written per capability until a three-item diagnostic replaces it."
  },
  "measured_fit_claim": false
}
```

## 2. The twelve review questions

There are three questions per part, with the same three verbs throughout: **clarify**, **correlate**, **open the way**.
- The blank ⟨…⟩ is filled from the question record (Core 2) or the microtopic (syllabus), and from the profile.
- The answer is a judgement.

### Hint ladder

| | After this rung the learner can … | Review question | Fill the blank from |
|---|---|---|---|
| **H1** clarify | say what the question turns on: the condition, event or quantity they would otherwise misread | Can H1 help this learner clarify ⟨X⟩? | X: the question's crux (`stable_crux_move`, `common_wrong_route`) where it meets a capability the learner holds as UNCERTAIN |
| **H2** correlate | connect X with something they already hold | Can H2 help this learner correlate ⟨X⟩ with ⟨Y⟩? | Y: a DEMONSTRATED capability, or a standard result in the syllabus (microtopic `inferential_jump`, a misconception's `repair`) |
| **H3** open the way | start the decisive move themselves | Can H3 give this learner the way to ⟨Z⟩ while leaving ⟨W⟩ to them? | Z: the crux move. W: the step that decides the answer |

A rung counts as YES only if, in addition:
- nothing the page shows before the attempt already says it (the conditions, the common wrong route, "Why this difficulty?");
- it gives no value that ends the problem;
- it reads correctly on the page, with math typeset, not spelled out as letters.

Three notes:
- **Numbering.** The Owner's message names the rungs H1–H3. The page and the R2 reference grammar number them from H0, so H1 here is the page's H0. In `learner_stage` terms: H1 is REPRESENTATION, H2 is KEY_CONCEPT, H3 is CRUX.
- **The blank depends on the learner.** Take Q29 below. For a learner with R1 MISSING, H1 would need to clarify that a position and a velocity are different vectors. For this learner, H1 needs to clarify that the angle asked is the velocity's, not the position's.
- **Rung count is not the measure.** The band table (3 rungs for D1–D2, 5 for D3–D4) becomes advice. Rungs 4 and 5 (the relation, an intermediate result) can stay for learners who need them, because the ladder opens only on request. This review judges the first three against their objectives.

### Figure (SVG)

| | Objective | Review question |
|---|---|---|
| **S1** clarify | the first stage shows this question's situation, including its non-standard feature, and nothing that answers it | Does stage 1 help this learner see ⟨X⟩? |
| **S2** correlate | a stage puts the concept on the picture, using the question's own numbers or symbols | Does a stage show ⟨Y⟩ on this picture? |
| **S3** open the way | a later stage shows the construction and still leaves the result | Does a stage show the way to ⟨Z⟩ without the value? |

For YES, every stage must also:
- be a complete picture on its own, because the page shows one stage at a time;
- have labels of at least 14 px on the 12.7-inch reference tablet (1366 px wide);
- keep every label inside the figure.

### Helpers: the panels around the question

| | Panels | Objective | Review question |
|---|---|---|---|
| **P1** | before the attempt: conditions, common wrong route, "Why this difficulty?" | they leave the decisive step to the learner | Does every panel the learner can open before attempting leave ⟨W⟩ to them? |
| **P2** | while stuck: "Need the concept again?" | the link lands where X is repaired | Does the link take this learner to the unit that repairs ⟨X⟩? |
| **P3** | after the attempt: working, "Key move", independent check | the working says why each step holds, the key move is the crux, the check tests the result another way | Does each "Why valid" say why this step holds here, and does the check test the result by another route? |

### Misconceptions

| | Objective | Review question |
|---|---|---|
| **M1** diagnose | the wrong idea this learner most likely brings to this question is listed, at their level | Is ⟨the wrong idea⟩ in the list? |
| **M2** detect | the diagnostic prompt separates a learner who holds the idea from one who slipped | Would a learner holding it answer the prompt differently? |
| **M3** repair | the repair shows why the idea fails, then gives the rule that replaces it | Does the repair give this learner something to see or check, not only "No"? |

## 3. A few questions for this learner

Four Core 2 past papers, from an entry check to a stretch:

| Question | Band | Why this one, for this learner | Answer |
|---|---|---|---|
| JEE Main 2026 · 04 Apr S2 · Q29 | D2 | Entry check: is R1 really held? Velocity direction from components at one instant | 45° |
| JEE (Adv) 2022 · P1 · Q8 | D3 | R3 at its edge: the apex state carries into a new region; one thing changes | n = 0.95 |
| JEE (Adv) 2024 · P2 · Q9 | D3 | Two bodies on one clock; needs relative motion, which this learner has met only for constant velocities | 2 |
| IIT-JEE 2011 · P2 · Q26 | D4 | The competitive move: one fall time serves two bodies, then momentum across the hit | 500 m/s |

## 4. The review, applied

### Q29 · D2 · direction of the velocity at t = 2 s (x = 24t, y = 43.6t − 4.9t²)

| | Objective, blank filled | Existing rung | Verdict |
|---|---|---|---|
| H1 | the angle asked is the velocity's direction at t = 2 s, not the position's direction from the origin | "The question asks for the direction of velocity, so differentiate both coordinate functions first." | **NO.** The open trap panel already says it ("Using y/x at t=2 s instead of differentiating…"). For this learner the rung adds nothing |
| H2 | the direction of motion ↔ (v_x, v_y) at that instant, which they can read | "Use tan(theta)=v_y/v_x only after evaluating both components at t=2 s." | **PARTLY.** The relation is right, but it is given as an instruction, not a connection. On the page "theta" shows as five italic letters |
| H3 | — | — | **Not needed.** After H2 the rest is evaluation this learner holds |

Rewritten rungs (the *prompt*, then what the rung reveals):
- **H1.** *At t = 2 s, is the angle asked about where the particle is, or where it is heading?* — Where it is heading: the direction of its velocity at that instant. The direction from the origin to the particle (y/x) is a different angle.
- **H2.** *Which two numbers fix the direction of the velocity at one instant?* — Its components at that instant, v_x = dx/dt and v_y = dy/dt, both at t = 2 s. The angle with the horizontal has tan θ = v_y/v_x.

### 2022 · P1 · Q8 · D3 · stronger gravity after the apex

Setup: range d; from the apex on, the downward acceleration is g/0.81; the new range is d′ = n d.

| | Objective | Existing | Verdict |
|---|---|---|---|
| H1 | what carries over at the apex (position d/2 and height H; velocity v cos θ across, zero vertically) and what changes (only the downward acceleration, only for the descent) | "Use symmetry only for the ordinary projectile to identify the apex position." | **PARTLY.** It clarifies one quantity that carries over, and rightly limits symmetry to the first half. It says nothing about the velocity and height that carry over |
| H2 | the descent ↔ a horizontal launch from height H, whose fall time depends only on H and the downward acceleration | "Compare the fall time from a fixed height under g and g/0.81." | **YES** |
| H3 | from the time ratio to the second segment, leaving the ratio and the sum | "Convert that time ratio into the second-stage horizontal distance." | **PARTLY.** It says what to do, not why it works (v_x is unchanged) |

Rewritten:
- **H1.** *At the apex the projectile enters the new region. Which of its position, velocity and acceleration carry over, and which change?* — Position (d/2 across, at height H) and velocity (v cos θ across, zero vertically) carry over. Only the downward acceleration changes, to g/0.81, and only for the descent.
- **H3.** The horizontal velocity is the same on both sides of the apex, so each horizontal segment is v cos θ times its time. Compare the second segment with the first, d/2.

### 2024 · P2 · Q9 · D3 · two projectiles meet

Setup: a ball is thrown from (0, 0) at v0 and θ0. A stone is thrown from (L, 0) towards it at 180° − θ1, with the speed chosen so they hit. Find (T1/T2)².

| | Objective | Existing | Verdict |
|---|---|---|---|
| H1 | a hit means the same point at the same instant: two conditions on one T, with the stone's speed as the extra unknown | "Write the ball-minus-stone relative position; what happens to the identical gravitational acceleration terms?" | **NO.** It skips the condition and gives the method. The method is also open before the attempt, in the trap panel ("…without exploiting common gravitational acceleration") and in "Why this difficulty?" ("The clean route uses relative projectile motion to cancel gravity…") |
| H2 | two bodies with the same acceleration ↔ relative motion at constant velocity, which they have met | none | **NO.** No rung makes the link. "Need the concept again?" sends the learner to the projectile model and independent components. No unit in the library teaches it: the relative-motion package has no acceleration in it |
| H3 | the vertical condition fixes the stone's speed, leaving the algebra and the two angle pairs | "Use the vertical collision condition to eliminate the stone's unknown launch speed." (page H1) | **YES**, as H3 |
| — | — | "Evaluate the resulting collision-time expression for the two angle pairs." (page H2) | Evaluation this learner already holds |

Rewritten:
- **H1.** *What must be true at the instant they hit: about x, about y, and about the time?* — Both are at the same point at the same instant T: x_ball(T) = x_stone(T) and y_ball(T) = y_stone(T). That is two conditions on one T; the stone's speed is the extra unknown.
- **H2.** *Both fall with the same acceleration g. What is the ball's acceleration as seen from the stone?* — Zero. Seen from the stone, the ball moves in a straight line at constant velocity. So when you subtract the two positions, the −½gt² terms cancel.
- **H3.** Keep the existing rung.

### 2011 · P2 · Q26 · D4 · bullet, ball and a 5 m post

Setup: a 0.2 kg ball sits on a 5 m post. A 0.01 kg bullet at speed V hits it. They land 20 m and 100 m away. Find V.

| | Objective | Existing | Verdict |
|---|---|---|---|
| H1 | both start horizontally, with no vertical velocity, from the same 5 m; 20 m and 100 m are landing distances, not speeds | "Find the common time to fall 5 m." | **PARTLY.** "Common" carries the key idea but only asserts it. The open trap panel already names it ("…without first establishing the common fall time") |
| H2 | the two flights ↔ "the fall time depends only on the height", so one time serves both | "Convert each horizontal range into its post-collision horizontal speed." | **PARTLY.** It gives the next step, not the reason the step is valid |
| H3 | horizontal momentum across the brief hit, leaving the equation | "Apply horizontal momentum conservation across the brief collision." | **YES** |

Rewritten:
- **H1.** *Just after the hit, how is each body moving vertically, and from what height?* — Both leave the top of the post moving horizontally, with no vertical velocity, from 5 m. The 20 m and 100 m are where they land, not their speeds.
- **H2.** *The bullet leaves five times faster than the ball. Does it reach the ground sooner?* — No. With no vertical velocity at the same height, both fall for the same time, set by the 5 m alone. Each range is its horizontal speed times that time.

This H2 also tests a misconception the library already lists: "Horizontal speed determines how long a horizontally launched object takes to fall."

### Figures

None of the 15 Core 2 questions shows a figure. Thirteen have none, and the other two name representations that are not in the product's packages. So the figure questions are applied twice: to an existing Core 1A figure, and as the brief for a missing one.

**Existing figure: `REP-KIN-2D-LEVEL-APEX-RETURN`.** This is in the Core 1A unit on apex and return events. "Need the concept again?" sends a learner stuck on 2022 Q8 here.

| | Verdict |
|---|---|
| S1 | **YES.** Stage 1 shows the launch, its components, the dashed path, "highest point (apex)" and "back at launch height". Nothing gives the answer |
| S2 | Content **YES**: stage 2 puts v_x = 6 m/s and a_y = −10 m/s² at the apex, and both conditions on one timeline. Picture **NO**: shown alone, it has no path, no ground and no launch point |
| S3 | **NO.** Stage 3 ("Event times") is two dots and two equations; stage 4 is two dots and two brackets. There is no curve and no timeline |
| Every stage | **NO.** The renderer's own reference check: the smallest label renders at 8.9 px on the 12.7-inch tablet, against a 14 px floor |

The figure was drawn as layers: each stage adds to the one before. The page shows one stage at a time, because the renderer treats every figure with more than one stage as a sequence of separate pictures.
- A scan finds the same pattern in 12 of the package's 24 staged figures: a later stage without the first stage's curve.
- I clicked through one of them on the page.

**Missing figure: 2024 Q9.** The three questions, used as the brief:
- **S1:** both launch points, both launch directions and both paths, with "same point, same instant T" where they meet.
- **S2:** the same scene seen from the stone. The ball moves in a straight line at constant velocity; gravity is gone from this view.
- **S3:** the relative velocity with its vertical part zero ("this fixes the stone's speed"), and the closing speed along the line ("T = L ÷ closing speed"). No values.
- Every stage is complete on its own and uses the question's symbols (v0, θ0, θ1, L).

### Helpers

| | Q29 | 2022 Q8 | 2024 Q9 | 2011 Q26 |
|---|---|---|---|---|
| **P1** before the attempt | **NO.** Trap: "…instead of differentiating…" | **NO.** Trap: "…instead of changing only the descent" | **NO.** The trap panel and "Why this difficulty?" both give the route | **NO.** Trap: "…without first establishing the common fall time" |
| **P2** concept link | **PARTLY.** Right microtopic (R1), but no unit there repairs velocity direction vs position direction | **YES.** The projectile-model microtopic has the apex-event unit | **NO.** Points away from the crux, and no unit for it exists | **PARTLY.** Fall time yes; linear momentum conservation is not a capability in the library |
| **P3** after the attempt | **NO.** "Why valid" is a stock sentence. "Key move" marks the arithmetic step v_y = 24 m/s. The check restates the solution | **PARTLY.** Stock "Why valid". The check is a real bound (0.5 < n < 1) | **PARTLY.** Stock "Why valid". "Key move" is not the crux the record's analysis names. The check reuses the derived formula | **PARTLY.** Stock "Why valid". The check explains rather than tests |

The blueprint already forbids the P1 failures: its TRAP authoring hint says "It must not give the answer or the right route". Even so, 11 of the 15 Core 2 trap texts name the right route by contrast ("instead of …", "without …").

Checks that test the result by another route, for the three questions that need one:
- **Q29:** the launch direction is tan⁻¹(43.6/24) ≈ 61°, and the angle falls while the particle rises. t = 2 s is before the apex (≈ 4.4 s), so the answer lies between 0° and 61°.
- **2024 Q9:** gravity cancels, so T cannot depend on g. With g = 0, both move in straight lines and meet at the same T.
- **2011 Q26:** the bullet must slow down in the hit (100 m/s < V), and kinetic energy cannot rise. At 500 m/s it is 1250 J before the hit and about 90 J after.

### Misconceptions

| Question | Wrong idea this learner most likely brings | M1 | M2 · M3 |
|---|---|---|---|
| Q29 | the direction of motion is the direction of the position vector (y/x) | **NO** | proposed below |
| 2022 Q8 | the whole velocity is zero at the apex, so nothing carries over | **YES** (projectile model) | M2 **YES**: "Which of v_x, v_y and a_y is zero?" M3 **PARTLY**: "Only v_y is zero…" states the rule but gives nothing to see. Add: if v_x were zero at the apex, the path would have a corner there, and it has none |
| 2024 Q9 | two bodies collide wherever their paths cross | **NO** | proposed below |
| 2011 Q26 | the faster body falls in less time | **YES** (projectile model) | M2 **YES**. M3 **PARTLY**: it states the rule. Add something to see: a coin flicked off a table and one dropped at the same instant land together |

Proposed additions:
- **Velocity direction vs position direction** (R1 microtopic).
  - Diagnostic: "At t = 2 s a particle is at (48, 67.6) m with velocity (24, 24) m/s. Which way is it moving?" A learner who holds the idea answers about 55°; one who does not answers 45°.
  - Repair: position says where the particle is from the origin; velocity says where it goes next. The two directions agree only for straight-line motion out of the origin.
- **Paths crossing vs collision** (with the missing unit below).
  - Diagnostic: "Two balls' paths cross at P. Ball A passes P at t = 1.0 s and ball B at 1.4 s. Do they collide at P?"
  - Repair: a path is drawn without time. A collision needs the same point at the same instant, so check x and y for both bodies at one T.

## 5. What the review found that no count did

1. **Spoilers before the attempt.**
   - 11 of 15 trap texts name the right route, against the blueprint's own rule.
   - In all four reviewed questions, "Why this difficulty?" names the method.
2. **Empty rungs.** In three of the four questions, H1 says what an open panel has already said.
3. **Rungs with no stated purpose.**
   - `learner_stage` and `prompt` are empty on all 43 rungs of the 15 questions, so the page labels the rungs by operation (Represent, Connect, Carry out).
   - `visual_ref` lets a rung show a figure stage; none of the bank's 109 rungs uses it.
4. **"Key move".** It is move 2 in all 15 questions. For Q29 and 2024 Q9, that is not the crux the record's own analysis names.
5. **Stock working.** Across the physics exam bank, 69 of 110 solution moves use one of four stock "Why valid" sentences, and 47 show "Result: intermediate result N".
6. **Math as letters.** Q29's second rung shows "theta" as five italic letters.
7. **Figures.**
   - No Core 2 question shows a figure.
   - In Core 1A, 12 of 24 staged figures appear to show fragments one stage at a time.
   - The five figures Core 1A units mount render labels at 8.5–9.9 px, against a 14 px floor.
   - The renderer reports the label sizes only at the reference depth, and the fragments not at all.
8. **The library.**
   - Nothing teaches two bodies with the same acceleration.
   - 2024 Q9's concept link points elsewhere.
   - The misconception 2024 Q9 needs most is not listed.
9. **The benchmark page.**
   - In 51 of its 59 questions, Hint 1 repeats the "Decisive Physical State" panel, which is shown open above the ladder.
   - 50 of the 59 questions share all three hint prompts with another question; there are 22 distinct prompt sets in all.
   - Its shape is right (prompt then reveal; key physics, then representation, then first move). Its words are often generic.

The existing quality rules check specificity mechanically. `C2A-SPECIFIC-SUPPORT` passes when no rung text repeats across a page, so a rung that is unique but adds nothing for this learner still passes.

## 6. Where it lives (proposal: nothing changed yet)

- **The review that already exists.**
  - REVIEW-GUIDE step 3 asks the independent reviewer to compare hints, figure stages and captions "against the learner's actual state". It does not say which learner, or how to compare.
  - The profile supplies the learner. The twelve questions are the comparison.
- **Findings.** Each NO or PARTLY becomes a `product-review/v2` finding:
  - `learner_impact` names the objective and the learner, e.g. "H1 cannot help this learner clarify that a hit needs one T; the trap panel has already given the method".
  - `suggested_fix` carries the rewritten rung.
  - Two optional fields make findings traceable: `profile_ref` on the review, and `asks` (H1 … M3) on each finding. The review schema accepts extra fields today; declaring them is a small change.
- **Severity** (proposed):
  - S0: a falsehood.
  - S1: a learner-visible breakage (math as letters, a fragment stage, a label under 14 px or cut off) or a spoiler (anything before the attempt, or any rung, that does the decisive step).
  - S2: a NO.
  - S3: a PARTLY.

  Whether S0 or S1 should hold back publication is the BLOCK/ADVISE question still open from the last round. Today the review method says no severity does.
- **Authoring.**
  - Fill `learner_stage` and `prompt` on every rung; both fields exist.
  - Optionally put a figure stage on a rung with `visual_ref` and `visual_stage_ref`.
  - Add one new field, `objective` on each scaffold (`{verb: CLARIFY | CORRELATE | OPEN_THE_WAY, target}`). The author writes the blank, and the reviewer answers the question it makes. This needs a schema change, because the scaffold definition allows no other fields.
- **Tooling.**
  - `authoring_templates.py review --question Q --profile P` would print the twelve questions, with the blanks filled from the record and the profile, for the reviewer.
  - The question templates would carry the three hint questions beside the rungs.

## 7. For the Owner to decide

1. **The profile.** Use this one as OWNER_ESTIMATE and run the three-item diagnostic, or give me another.
2. **Spoilers.** Rewrite the 11 trap texts to the blueprint's rule, and move the "Why this difficulty?" note behind the attempt. The band pill stays visible.
3. **Layered figures.** Either let a representation declare that its stages are layers, or redraw 12 figures. The page script can already show stages cumulatively. I recommend the declaration.
4. **Counts become advice.** The band-to-rung table stops judging depth; the review does that.
5. **Content.** Add a unit for two bodies with the same acceleration, and the two misconceptions above. This is research, not template work.
6. **The four rewritten ladders.** Apply them to the bank records, with `learner_stage` and `prompt` filled in.

## How the numbers were measured

- **Gaps:** `python3 Shared/tools/render_core.py gaps --manifest products/physics/phy-kin-2d-motion.manifest.json [--reference]`.
- **What the learner sees:** a draft render (`render_core.py build … --draft`), opened in Chromium at 1366 × 854. I opened each rung and clicked each figure stage chip.
- **Records, trap texts, crux pointers and stock sentences:** read from `Physics/library/phy-kin-2d-motion.v1.json` and `Physics/library/exam-bank/competitive-exam-question-bank.v2.json`.
- **Layered figures:** the scan flags a staged SVG when a later stage has no `<path>` or `<polyline>` but the first stage has one. It points a reviewer at a figure; it does not prove a fault.
- **Benchmark:** `public/standalone/practice/core2-motion-in-a-plane-tablet.html`, 59 question cards.
