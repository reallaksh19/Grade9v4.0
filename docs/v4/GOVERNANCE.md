# Grade9v4.0 governance: required checks, ruleset, CODEOWNERS

What protects `main`, in what order it is switched on, and the one data repair the Owner asked for a proposal on. Measured on the seed content: Grade9v3.5 PR #2 head `266749f`, which is this repository's `main` except for `PROVENANCE.md`.

## 1. CI at the seed

| Workflow | Job (check name) | Runs on every PR? | Result at the seed | Stage |
|---|---|---|---|---|
| `canonical-assurance.yml` | Regression delta (exact test ids) | yes | pass | 1 |
| `learner-quality.yml` | code-tests | yes | pass | 1 |
| `learner-quality.yml` | blueprint-v2-render-snapshots | yes | pass | 1 |
| `v3-relay.yml` | validate-v31 | yes | pass | 1 |
| `content-ci.yml` | Verify 6-Suite Content Integrity Matrix | yes (PRs to `main`) | pass | 1, replaced in 3 |
| `canonical-assurance.yml` | Assurance (no worse than the baseline) | yes | **fail**: ledger keys use `\` (62 pages "worse"); 19 new canonical findings on `LIB-MATH-LINEAR-EQUATIONS` | 2 |
| `guardrails.yml` | guardrails | yes | **fail** (includes `build_manifest.py --check`, stale) | 2 |
| `learner-quality.yml` | core2-v2-browser-audit | yes | **fail** | 2 |
| `question-bank-platform.yml` | contracts | **no** (17 path filters) | **fail** (includes `build_pages_site.py --check`, stale) | 2, after the filter is removed |
| `core1a-tablet-browser.yml` | browser-audit | no (9 path filters) | not run on PR #2 | 3 (folded into `check`) |
| `friction-core-browser.yml` | friction-evidence | no (13 path filters) | not run on PR #2 | 3 (folded into `check`) |
| `pass1-question-bank-contract.yml` | validate | no (10 path filters) | not run on PR #2 | 3 (folded into `check`) |
| `canonical-assurance.yml` | Release status (informational, never gating) | yes | pass | never required, by design |
| `pass1-refresh-generated.yml` | refresh | push to `question-bank/pass1-provenance` only | — | never required (it pushes generated files to that branch) |

`blueprint_spec.py --check` (the generated blueprint spec, stale today) runs in **no** workflow.

**Rule for choosing:** a required check must report on every PR. A path-filtered job never reports on a PR outside its paths, and GitHub then waits on it forever ("Expected — waiting for status"). That is why the path-filtered jobs are folded into one unfiltered job before they become required.

**Actions on this repository:** after the seed push, the Actions API reports **0 workflow runs**. If Actions is disabled for the new repository (Settings → Actions → General), no check will ever report, and a ruleset that requires checks blocks every PR. This session cannot read that setting through its proxy.

## 2. Required checks, staged

| Stage | When | Required checks |
|---|---|---|
| **1** | now | Regression delta (exact test ids); code-tests; blueprint-v2-render-snapshots; validate-v31; Verify 6-Suite Content Integrity Matrix |
| **2** | each one as WP-A turns it green | + Assurance (no worse than the baseline); guardrails; core2-v2-browser-audit; contracts (path filter removed); a new **generated-files** job running `blueprint_spec.py --check`, `build_manifest.py --check`, `build_pages_site.py --check` |
| **3** | WP-G | one `check` job (every verifier through the assurance chain, no path filter) replaces the 6-suite job and absorbs browser-audit, friction-evidence and validate; + the gate-change job (section 4) |

## 3. Ruleset for `main` (the Owner applies it)

Settings → Rules → Rulesets → New branch ruleset:

| Setting | Value |
|---|---|
| Target | default branch (`main`); Enforcement: Active |
| Bypass list | repository admin (the Owner) only; no app or agent |
| Restrict deletions | on |
| Block force pushes | on |
| Require a pull request before merging | on: 1 approval; dismiss stale approvals on new commits; require review from Code Owners; require approval of the most recent push; require conversation resolution |
| Require status checks to pass | on: the Stage 1 list; add Stage 2 checks as they turn green |
| Require branches to be up to date | off (it forces merging `main` into PR branches; a stale branch is re-cut from `main` instead) |
| Require linear history | on (squash or rebase merges only; no merge commits on `main`) |

This session cannot apply it: the branch-protection API returns 403 to its integration, and rulesets are an Owner setting.

## 4. CODEOWNERS

`.github/CODEOWNERS` lists the gate surfaces: assurance, blueprint registry and ledger, policy, workflows, gates, intake workflow, tests, and the file itself.

What it does and does not do: the Owner already reviews and merges every PR, so CODEOWNERS adds no second reviewer. With "require review from Code Owners", a change to a gate file is marked on the PR and cannot merge on an approval given before it was pushed.

The check that catches an agent's escape is a CI job (WP-H, the **gate-change job**), not CODEOWNERS:
- (a) a PR that changes gate paths and content paths together fails;
- (b) raising a question's `status` or answer `verification_status` without a matching `review-promotion-receipt` fails (the `1448267` case below);
- (c) waivers, baseline and ledger files change only to what their own tools write (the job re-runs the tool and compares).

## 5. The Mathematics linear-equations records

**What happened** (commit `1448267`, "elevate font floor to 14px, fix KaTeX rendering, bridge Core 2 challenges to Question Bank"). 18 of the 32 questions in `Mathematics/library/linear-equations.v1.json` were edited:

| Field | Before | After | Valid? |
|---|---|---|---|
| `status` | `CANDIDATE` | `PUBLISHED` | no: the package schema allows DISCOVERED, CANDIDATE, REVIEWED, CURATED, DISPUTED, STALE, RETIRED. These are the only 18 `PUBLISHED` questions in all three libraries (899 CANDIDATE, 11 REVIEWED). |
| `answer.verification_status` | `CHECKED_BY_AUTHOR` | `VERIFIED_CANONICAL` | no: the enum is NOT_RUN, CHECKED_BY_AUTHOR, INDEPENDENTLY_CHECKED, DISPUTED |
| `extensions.grade9v3:question_bank.topic_ref` | absent | `TOPIC-MATHEMATICS-LINEAR-EQUATIONS` | unresolved (S1) |

**Why `topic_ref` cannot resolve:** `TOPIC-*` ids are not library entities. The Question Bank projection mints them (`question_bank_platform.topic_ref(subject, label)`), and they exist only in generated `public/data` files. A canonical record may reference library ids only. The bridge also left the Question Bank with two topics carrying the same label, "Linear Equations in One Variable":
- `TOPIC-MATHEMATICS-LINEAR-EQUATIONS`, with the 18 questions;
- `TOPIC-MATHEMATICS-LINEAR-EQUATIONS-IN-ONE-VARIABLE`, with none.

**Proposal**
1. Restore the 18 questions to what was true: `status: CANDIDATE`, `verification_status: CHECKED_BY_AUTHOR`, no `topic_ref`. Promotion happens only through a review-promotion receipt.
2. Make the Question Bank derive a library question's topic from the record's own ids: question → `primary_capability_ref` → microtopic → package `LIB-MATH-LINEAR-EQUATIONS`. Take the topic **id from the package id** (`TOPIC-MATHEMATICS-LINEAR-EQUATIONS`), not from a label, so no third id is minted.
3. Label it **"Linear Equations"**. The package holds `MIC-MAT-LEQ-04-TWO-VARIABLES-LINE-OF-SOLUTIONS`, so "in One Variable" is narrower than its content. The package title ("Linear equations in one unknown") has the same mismatch and should be retitled with it.
4. Retire the empty `TOPIC-MATHEMATICS-LINEAR-EQUATIONS-IN-ONE-VARIABLE` as an alias of the one id, so existing links still open.
5. If a manual binding is ever needed, it goes in the Question Bank's topic-link table (`resource_id`, `topic_ref`, `reason`), which is a projection input, never in a canonical record.

**Done when:**
- `assurance_run.py` reports 0 new canonical findings on `LIB-MATH-LINEAR-EQUATIONS`;
- the regenerated catalog has one Mathematics linear-equations topic;
- the 18 questions route to it.

Part of WP-A.
