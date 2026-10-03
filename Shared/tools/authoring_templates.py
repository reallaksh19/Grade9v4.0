#!/usr/bin/env python3
"""Templates an agent fills to author Core1A and Question Bank records, the check a filled one must pass, and the packets the
Owner approves rung ladders and the atlas from.

    python3 Shared/tools/authoring_templates.py write              # regenerate template/v4/ from the blueprint, schemas, vocabulary
    python3 Shared/tools/authoring_templates.py write --check      # exit 1 when template/v4/ is not what they give
    python3 Shared/tools/authoring_templates.py check FILE...      # a filled template, or an approval record
    python3 Shared/tools/authoring_templates.py packet rungs --matrix Physics/matrices/phy-kin-2d-motion.rungs.json
    python3 Shared/tools/authoring_templates.py packet atlas --subject Physics

A template is a projection, not a document someone wrote: field shapes come from the package and exam-bank schemas, what a page
needs and how much of it (by difficulty band D1 to D4) from the blueprint registry, the band score ranges and question types from
the learner metadata vocabulary. Change one of those and `write --check` fails until the templates are regenerated.

`check` is what makes a template more than a form. A filled template passes only when no placeholder is left, the record satisfies
its schema, it supplies what the blueprint asks for at the reference depth of its band, and it claims nothing an author cannot
claim: a new record is CANDIDATE, its key is at most CHECKED_BY_AUTHOR, its band agrees with its score.

An approval packet is generated from the data it asks the Owner to approve, and it carries that data's digest. The approval record
the Owner signs names the digest; `check` reports an approval whose subject has changed since as stale.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from Shared.tools import web_blueprint_contract as blueprints  # noqa: E402

PACKAGE_SCHEMA = REPO / "Shared/library/package.schema.json"
BANK_SCHEMA = REPO / "Shared/library/competitive-exam-bank.schema.json"
MATRIX_SCHEMA = REPO / "Shared/library/matrix.schema.json"
VOCABULARY = REPO / "Shared/vocabularies/learner-question-metadata.v1.json"
ASSURANCE_EXTENSION = REPO / "Shared/assurance/question-assurance-extension.schema.json"
SCRATCH = REPO / "build/authoring-check"                 # gitignored: where check stages a record next to its package
OUT = REPO / "template/v4"
BANDS = ("D1", "D2", "D3", "D4")
CORE2 = "BP-CORE2-SOURCE-QUESTION"
CORE1A = "BP-CORE1A-CONSTRUCTION"
HEADER = "$template"
PLACEHOLDER = re.compile(r"<<(FILL|ONE OF)[^>]*>>")
AUTHOR_STATUSES = ("CANDIDATE",)                       # a new record is a candidate; promotion is a review, with a receipt
AUTHOR_VERIFICATION = ("NOT_RUN", "CHECKED_BY_AUTHOR")  # an author cannot check their own key independently
APPROVAL_DECISIONS = ("PENDING", "APPROVED", "REVISE")
OFFICIAL_KEYS = ("OFFICIAL_PAPER_EMBEDDED_KEY", "OFFICIAL_FINAL_KEY", "OFFICIAL_NTA_FINAL_ANSWER_KEY",
                 "INDEPENDENTLY_CHECKED_AGAINST_OFFICIAL_QUESTION")


# ---------------------------------------------------------------- sources

def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    """sha256 of the file with line endings normalised, so a checkout on any platform gives the same value."""
    return "sha256:" + hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def blueprint(blueprint_id: str) -> dict:
    return next(b for b in blueprints.load_registry()["blueprints"] if b["id"] == blueprint_id)


def component(bp: dict, component_id: str) -> dict:
    return next(c for c in blueprints.components(bp) if c["id"] == component_id)


def band_range(band: str) -> tuple[int, int]:
    r = load(VOCABULARY)["question_difficulty_score_ranges"][band]
    return r["min"], r["max"]


def band_of_score(score: int) -> str | None:
    for band, r in load(VOCABULARY)["question_difficulty_score_ranges"].items():
        if r["min"] <= score <= r["max"]:
            return band
    return None


# ---------------------------------------------------------------- instances from a schema

def fill(label: str) -> str:
    return f"<<FILL: {label}>>"


def one_of(values: list) -> str:
    return "<<ONE OF: " + " | ".join(str(v) for v in values) + ">>"


def instance(node: dict, defs: dict, label: str, include: tuple[str, ...] = ()) -> Any:
    """The smallest value a schema node accepts once its placeholders are filled: required properties, one item where a list
    needs at least one, a placeholder for every string, number and choice."""
    if "$ref" in node:
        return instance(defs[node["$ref"].split("/")[-1]], defs, label, include)
    if "const" in node:
        return node["const"]
    if "enum" in node:
        return one_of(node["enum"])
    for key in ("anyOf", "oneOf"):
        if key in node and "type" not in node and "properties" not in node:     # alternatives, not a constraint on an object
            options = [o for o in node[key] if o.get("type") != "null"]
            return instance(options[0], defs, label, include) if options else None
    kind = node.get("type")
    if isinstance(kind, list):
        kind = next((k for k in kind if k != "null"), None)
    if kind == "object" or "properties" in node:
        props = node.get("properties", {})
        if not node.get("required") and node.get("minProperties") and props:   # "exactly one of these": offer the choice
            first = next((k for k, v in props.items() if v.get("type") == "string"), next(iter(props)))
            return {first: fill(f"{label}: keep exactly one key of " + " | ".join(props))}
        keys = list(node.get("required", [])) + [k for k in include if k in props and k not in node.get("required", [])]
        return {k: instance(props[k], defs, f"{label}.{k}" if label else k) for k in keys}
    if kind == "array":
        if node.get("minItems", 0) >= 1:
            return [instance(node.get("items", {}), defs, f"{label}[]")]
        return []
    if kind == "boolean":
        return one_of([True, False])
    if kind in ("integer", "number"):
        return fill(f"{label} ({kind})")
    return fill(label)


def tagged(fragment: Any, component_id: str, path: str = "") -> Any:
    """A blueprint skeleton fragment with its empty values turned into placeholders that name the component asking for them."""
    if isinstance(fragment, dict):
        return {k: tagged(v, component_id, f"{path}.{k}" if path else k) for k, v in fragment.items()}
    if isinstance(fragment, list):
        return [tagged(v, component_id, f"{path}[]") for v in fragment]
    if fragment == "" or fragment == 0:
        return fill(f"{component_id} {path}")
    if isinstance(fragment, str) and "{qid}" in fragment:
        return fragment.replace("{qid}", "<<FILL: question id>>")
    return fragment


def merge(into: dict, add: dict) -> None:
    for key, value in add.items():
        if isinstance(value, dict) and isinstance(into.get(key), dict):
            merge(into[key], value)
        else:
            into[key] = copy.deepcopy(value)


def guide(bp: dict, band: str | None) -> list[dict]:
    """Every component the blueprint lists, what it reads and how much it needs for this band."""
    rows = []
    for c in blueprints.components(bp):
        need = blueprints.target_for(c, band) if (c.get("target_items") or c.get("target_items_by_band")) else None
        row = {"component": c["id"], "level": c["level"], "fields": c.get("source") or []}
        if need:
            row["items_for_band" if band else "items"] = need
        if c.get("min_items"):
            row["floor"] = c["min_items"]
        if c.get("repeat"):
            row["repeat"] = c["repeat"]
        if (c.get("authoring") or {}).get("hint"):
            row["hint"] = c["authoring"]["hint"]
        rows.append(row)
    return rows


# ---------------------------------------------------------------- the templates

def assurance_extension() -> dict:
    """The fields that let the assurance checks run on a question instead of reporting it INCONCLUSIVE."""
    from Shared.assurance import typed
    schema = load(ASSURANCE_EXTENSION)["properties"]
    spec = schema["problem_specification"]["properties"]
    fact = spec["visible_facts"]["items"]["properties"]
    contract = schema["answer_contract"]["properties"]
    return {
        "problem_specification": {
            "requested_outputs": [{"id": fill("output id, e.g. v"), "quantity_kind": fill("what it is: speed, force, energy, ...")}],
            "visible_facts": [{k: (one_of(v["enum"]) if "enum" in v else fill(f"visible fact {k}")) for k, v in fact.items()}],
            "declared_assumptions": [fill("an assumption the stem or the conditions state")],
            "permitted_constants": [],
        },
        "answer_contract": {"answer_type": one_of(contract["answer_type"]["enum"]), "requested_outputs": [fill("output id")],
                            "equivalence_policy": one_of(contract["equivalence_policy"]["enum"])},
        "$computation_model_types": sorted(typed.MODELS),
    }


def transfer_block(defs: dict) -> dict:
    node = defs["question"]["properties"]["transfer"]
    block = instance(node, defs, "transfer", include=("dimension", "statement", "builds_on", "protected_move_ref", "invariant", "novelty"))
    block["protected_move_ref"] = "<<FILL: question id>>-MOVE-1"
    return block



def question_template(band: str, kind: str) -> dict:
    """kind LIBRARY: a question in a subject package (authored, adapted, NCERT, exemplar); kind TRANSFER: a package question for Core2B;
    kind PYQ: an exam-bank question."""
    package, bank = load(PACKAGE_SCHEMA), load(BANK_SCHEMA)
    pdefs, bdefs = package["$defs"], bank["$defs"]
    bp = blueprint(CORE2)
    lo, hi = band_range(band)
    vocab = load(VOCABULARY)
    record = instance(pdefs["question"], pdefs, "", include=("scaffolds", "learner_question_type"))
    record["version"] = "1.0.0"
    record["status"] = "CANDIDATE"
    record["evidence_refs"] = []
    record["learner_question_type"] = one_of(list(vocab["question_types"]))
    for c in blueprints.components(bp):                  # the page's own fields, as the blueprint shapes them
        merge(record, tagged((c.get("authoring") or {}).get("skeleton") or {}, c["id"]))
    ladder = component(bp, "HINT_LADDER")
    record["scaffolds"] = record["scaffolds"][: blueprints.target_for(ladder, band)]
    record["answer"]["verification_status"] = one_of(list(AUTHOR_VERIFICATION) + (["INDEPENDENTLY_CHECKED (only with an official key in source_custody)"] if kind == "PYQ" else []))
    difficulty = {
        "band": band,
        "score": fill(f"integer {lo} to {hi}: the sum of the five components below"),
        "components": {k: fill("integer 0 to 2") for k in pdefs["question_difficulty"]["properties"]["components"]["required"]},
        "basis": fill("why this band: what the learner must choose, translate, chain, compute and avoid"),
    }
    analysis = record.setdefault("extensions", {}).setdefault("grade9v3:analysis", {})
    extension = assurance_extension()
    models = extension.pop("$computation_model_types")
    record["extensions"].update(extension)
    if kind == "TRANSFER":                     # Core2B: the changed decision is protected, so no hint may hand it over
        record["transfer"] = transfer_block(pdefs)
        record["representation_roles"] = {"initial_ref": None, "safe_ref": fill("REP-... shown before the attempt; it must not show the protected move"),
                                          "bound_ref": None, "stage_refs": []}
        record["exposure"] = [{"core": "CORE2B", "role": "NEW_TRANSFER", "artifact_ref": None}]
        for rung in record["scaffolds"]:
            if rung["supports_move_ref"].endswith("-MOVE-1"):
                rung["supports_move_ref"] = rung["supports_move_ref"][:-1] + "2"
    if kind == "PYQ":
        record["origin"] = one_of(["ORIGINAL", "ADAPTED"])
        record["extensions"]["grade9v3:provenance_class"] = one_of(bdefs["exam_bank_question"]["properties"]["extensions"]
                                                                   ["properties"]["grade9v3:provenance_class"]["enum"])
        record["extensions"]["grade9v3:source_custody"] = instance(bdefs["source_custody"], bdefs, "source_custody")
        full = instance(bdefs["analysis"], bdefs, "analysis")
        merge(full, analysis)
        full["difficulty"] = difficulty
        record["extensions"]["grade9v3:analysis"] = full
    else:
        record["difficulty"] = difficulty
    record = {HEADER: {
        "kind": f"{kind}_QUESTION",
        "band": band,
        "band_label": vocab["question_difficulty"][band],
        "score_range": [lo, hi],
        "blueprint": f"{bp['id']}@{bp['version']}",
        "destination": ("an exam-bank file under <Subject>/library/exam-bank/" if kind == "PYQ"
                        else "questions[] of the subject package <Subject>/library/<slug>.v1.json, and its id in the product manifest's "
                             + ("selection.core2b" if kind == "TRANSFER" else "selection.core2a (or core2b for a transfer task)")),
        "rules": [
            "Replace every <<FILL: ...>> and <<ONE OF: ...>>; delete this $template block; run `authoring_templates.py check FILE`.",
            "status stays CANDIDATE: promotion is a review with a receipt, never an edit.",
            "answer.verification_status is NOT_RUN or CHECKED_BY_AUTHOR: an author cannot check their own key independently.",
            f"The band is {band}: score {lo} to {hi}, the sum of the five components. A different score means a different template.",
            f"scaffolds: {blueprints.target_for(ladder, band)} rungs for {band}, in the order the learner meets them.",
            "adaptation is null unless origin is ADAPTED; then it names the parent and what changed.",
            "options are the choices without letters: the page writes (A), (B), ... itself.",
            "Write math as the existing records do; the page shows it as written (typesetting is a separate duty).",
            "extensions.problem_specification and answer_contract let SELF_CONTAINMENT run. Add extensions.computation_model only when "
            f"the problem fits an implemented model ({', '.join(models)}); then ANSWER_CORRECTNESS recomputes your answer.",
            "An EXPECTED component you leave empty needs a written reason in extensions['grade9v3:component_waivers'] {COMPONENT_ID: reason}.",
            "Never write HTML: the renderer makes the page from this record.",
        ] + ([
            "Core2B protects the decision the transfer changes: transfer.protected_move_ref names a DECIDE move (MOVE-1 here), and no "
            "scaffold may support it, because pre-attempt help would hand it over. representation_roles.safe_ref is shown before the "
            "attempt and must not show that move. transfer.novelty names the earlier items you checked this against and why it is new.",
        ] if kind == "TRANSFER" else []) + [
            "Then run: authoring_templates.py check FILE --into <package> --product <manifest>. It runs the library intake and the "
            "renderer on the record in place and reports only what the record adds.",
        ],
        "components": guide(bp, band),
    }, **record}
    return record


def core1a_template() -> dict:
    package = load(PACKAGE_SCHEMA)
    defs = package["$defs"]
    bp = blueprint(CORE1A)
    steps_c, checks_c = component(bp, "CONSTRUCTION_STEPS"), component(bp, "QUICK_CHECK")
    record = instance(defs["microtopic"], defs, "", include=("construction_units",))
    record.update({"version": "1.0.0", "status": "CANDIDATE", "evidence_refs": [], "lineage": [], "question_family_refs": []})
    record["exit_task"]["answer"]["verification_status"] = one_of(list(AUTHOR_VERIFICATION))
    record["teaching_path"], record["construction_units"] = [], []
    roles = defs["independent_check"]["properties"]["role"]["enum"]
    number = 0
    for unit, (bands, crux) in enumerate(((("D1", "D2"), "a D1 or D2 question"), (("D3", "D4"), "a D3 or D4 question")), 1):
        need = blueprints.target_for(steps_c, bands[0])
        refs = []
        for _ in range(need):
            number += 1
            step = instance(defs["step"], defs, f"teaching_path step {number}")
            step["id"] = f"<<FILL: microtopic id>>-S{number}"
            step["inputs"] = []
            refs.append(step["id"])
            record["teaching_path"].append(step)
        cu = instance(defs["construction_unit"], defs, f"construction unit {unit}",
                      include=("decision", "relation_refs", "worked_anchor_ref", "representation_ref", "reveal_stage_refs",
                               "misconception_indexes", "independent_checks"))
        cu["id"] = f"CU-<<FILL: microtopic id without MIC->>-{unit}"
        cu["decision"] = fill(f"UNIT_HEADER unit {unit}: the decision this unit teaches the learner to make")
        cu["step_refs"] = refs
        cu["relation_refs"] = [fill(f"EQUATIONS unit {unit}: REL-... id")]
        cu["worked_anchor_ref"] = fill(f"WORKED_EXAMPLE unit {unit}: id of a library question worked as the example")
        cu["representation_ref"] = fill(f"STAGED_VISUAL unit {unit}: REP-... id of the representation")
        cu["reveal_stage_refs"] = []
        cu["misconception_indexes"] = [0]
        cu["independent_checks"] = [{"statement": fill(f"QUICK_CHECK unit {unit} {role}"), "role": role}
                                    for role in roles[: checks_c.get("target_items") or len(roles)]]
        record["construction_units"].append(cu)
    record = {HEADER: {
        "kind": "CORE1A_MICROTOPIC",
        "blueprint": f"{bp['id']}@{bp['version']}",
        "destination": "microtopics[] of the subject package <Subject>/library/<slug>.v1.json",
        "rules": [
            "Replace every <<FILL: ...>> and <<ONE OF: ...>>; delete this $template block; run `authoring_templates.py check FILE`.",
            "status stays CANDIDATE.",
            "One construction unit per decision the learner must make. The two units here show both depths: a unit needs "
            f"{blueprints.target_for(steps_c, 'D1')} steps, and {blueprints.target_for(steps_c, 'D3')} when it builds the crux of a D3 or D4 "
            "question of the product's bank (then its last step is the move that question turns on). Copy or delete units to match.",
            "Every step_refs id is a teaching_path step; every misconception index points into misconceptions.",
            "crux_question_refs and crux_step_ref name a question of the PRODUCT's bank (its bank_refs), never a package question; "
            "when the bank holds none for this concept, leave both out.",
            "worked_anchor_ref names a package question that exercises exactly this unit's move; give each unit its own if you can.",
            staged_visual_rule() + " Use core1a/representation.template.json and .svg.",
            f"QUICK_CHECK: {checks_c.get('target_items')} independent checks per unit, one per role ({', '.join(roles)}).",
            "Never write HTML: the renderer makes the page from this record.",
            "For a microtopic that already exists, start from `authoring_templates.py new core1a --microtopic ID`, which carries its "
            "fields over. Then run: check FILE --into <package> --product <manifest> [--with <representations.json>].",
        ],
        "components": guide(bp, None),
    }, **record}
    return record


def staged_visual_rule() -> str:
    c = component(blueprint(CORE1A), "STAGED_VISUAL")
    return (f"STAGED_VISUAL: {blueprints.target_for(c, 'D1')} stages, {blueprints.target_for(c, 'D3')} for a unit that builds the crux of a "
            "D3 or D4 question. The page shows ONE stage at a time, so every data-g9-stage-id group must be a complete picture "
            "(repeat the base drawing in each group). viewBox at most 440 wide, every label at least 14 units, a <title> and <desc> "
            "named by aria-labelledby.")


def representation_template() -> dict:
    defs = load(PACKAGE_SCHEMA)["$defs"]
    record = instance(defs["representation"], defs, "", include=("correspondence", "interactive_resource_refs", "reveal_stages"))
    record.update({"version": "0.1.0", "status": "CANDIDATE", "evidence_refs": [], "extensions": {}, "scene_instances": [],
                   "interactive_resource_refs": [],
                   "kind": fill("one of the representation_kinds the subject contract declares (<Subject>/adapter/CoreContracts.json)"),
                   "rendered_asset_refs": [fill("<Subject>/assets/representations/<REP id>.svg")]})
    record["reveal_stages"] = [{"id": f"<<FILL: stage id>>-V{n}", "label": fill(f"stage {n} label"), "purpose": fill(f"what stage {n} shows"),
                                "visible_elements": [fill("one of required_elements")]} for n in range(3)]
    record["correspondence"] = [{"element": fill("one of required_elements"), "symbol": fill("a symbol one of relation_refs declares"),
                                 "in_words": fill("what that part of the picture is, in words")}]
    return {HEADER: {"kind": "REPRESENTATION", "destination": "representations[] of the subject package, with its SVG beside the others",
                     "rules": [staged_visual_rule(),
                               "Each reveal_stages id is the data-g9-stage-id of one group in the SVG, in the same order.",
                               "correspondence binds an element the figure must contain to a symbol a bound relation declares.",
                               "Draw each unit its own picture; do not reuse one figure on many units."]}, **record}


def svg_skeleton() -> str:
    groups = "".join(
        f'<g data-g9-stage-id="STAGE-ID-V{n}" font-family="system-ui,sans-serif" font-size="14" fill="currentColor" stroke="currentColor">'
        f'<text x="16" y="24" stroke="none" font-weight="700">Stage {n + 1} title</text>'
        '<!-- the complete picture for this stage: repeat the base drawing, then add what this stage reveals -->'
        f'<text x="16" y="200" stroke="none">what stage {n + 1} adds</text></g>\n' for n in range(3))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 220" role="img" aria-labelledby="FIG-title FIG-desc">\n'
            '<title id="FIG-title">What the figure shows</title><desc id="FIG-desc">Stage by stage, in words.</desc>\n' + groups + "</svg>\n")


APPROVAL_RECORD = {
    "approval_id": "<<FILL: APPROVAL-<KIND>-<subject or matrix id>-<YYYYMMDD>>>",
    "kind": "<<ONE OF: RUNGS | ATLAS>>",
    "subject_ref": "<<FILL: repository path of what is approved (the matrix file, or the subject)>>",
    "subject_digest": "<<FILL: the digest printed at the top of the packet>>",
    "decision": "PENDING",
    "items": [{"ref": "<<FILL: rung or bucket id>>", "decision": "<<ONE OF: APPROVED | REVISE>>", "note": ""}],
    "band_targets": {},
    "approved_by": "Owner",
    "approved_at": None,
}


def readme() -> str:
    lines = [
        "# Authoring templates (generated)",
        "",
        "Generated by `python3 Shared/tools/authoring_templates.py write` from the blueprint registry, the package and exam-bank",
        "schemas and the learner metadata vocabulary. Do not edit these files: change a source and regenerate.",
        "",
        "| File | Use it to author | Lands in |",
        "|---|---|---|",
        "| `core1a/microtopic.template.json` | a Core1A concept (a microtopic with construction units) | `<Subject>/library/<slug>.v1.json` `microtopics[]` |",
    ]
    for band in BANDS:
        lines.append(f"| `question-bank/library-question.{band}.template.json` | an authored, adapted, NCERT or exemplar question at {band} | the package `questions[]` |")
    for band in BANDS:
        lines.append(f"| `question-bank/pyq-question.{band}.template.json` | a previous-year exam question at {band} | an exam-bank file |")
    lines += [
        "| `question-bank/transfer-question.D1..D4.template.json` | a Core2B transfer task (the changed decision is protected) | the package `questions[]` and `selection.core2b` |",
        "| `core1a/representation.template.json`, `.svg` | the picture a Core1A unit stages | the package `representations[]` and `<Subject>/assets/representations/` |",
        "| `approvals/owner-approval.template.json` | the Owner's decision on a rung ladder or the atlas | `approvals/` beside what it approves |",
        "",
        "An owner-supplied question is not authored from a template: `owner_bank.py new` keeps the Owner's words verbatim.",
        "",
        "## The loop an agent follows",
        "",
        "1. Find the work: `packet atlas --subject S` (scope, bands, missing D1-D4) and `packet rungs --matrix FILE` (the ladder).",
        "2. Start from a template made for the package: `new question --package P --band D4 [--role CORE2B]` or",
        "   `new core1a --package P --microtopic MIC-...`. Choose the band from the score (vocabulary ranges), never the other way round.",
        "3. Fill it. `$template.components` says, per component, which fields it reads, how many items the band needs and how to write them;",
        "   `$template.rules` says what the page and the gates expect (no option letters, one complete picture per stage, crux only from the bank).",
        "4. Delete `$template`, then `check FILE --into <package> --product <manifest> [--with representations.json]` until it prints `ok`.",
        "   This runs the library intake, the depiction checks and the renderer on the record in place and reports only what the record adds;",
        "   it also lists what it closes and any waiver, which a reviewer must accept.",
        "5. Add the record to its package and its id to the product manifest; render the product and look at the page on a tablet width.",
        "",
        "## Approvals",
        "",
        "`packet rungs --matrix FILE` and `packet atlas --subject S` write what the Owner reads, generated from the data, with its digest.",
        "The Owner's decision is an `owner-approval` record naming that digest; `check` reports it stale when the data changes after approval.",
    ]
    return "\n".join(lines) + "\n"


def outputs() -> dict[str, str]:
    out = {"README.md": readme(),
           "core1a/microtopic.template.json": dumps(core1a_template()),
           "approvals/owner-approval.template.json": dumps(APPROVAL_RECORD)}
    for band in BANDS:
        out[f"question-bank/library-question.{band}.template.json"] = dumps(question_template(band, "LIBRARY"))
        out[f"question-bank/transfer-question.{band}.template.json"] = dumps(question_template(band, "TRANSFER"))
        out[f"question-bank/pyq-question.{band}.template.json"] = dumps(question_template(band, "PYQ"))
    out["core1a/representation.template.json"] = dumps(representation_template())
    out["core1a/representation.template.svg"] = svg_skeleton()
    return out


def dumps(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def write(check_only: bool) -> int:
    stale = [name for name, text in outputs().items()
             if not ((OUT / name).is_file() and (OUT / name).read_text(encoding="utf-8") == text)]
    if check_only:
        if stale:
            print("template/v4 is stale; run Shared/tools/authoring_templates.py write:\n  " + "\n  ".join(stale))
            return 1
        print("template/v4 is current")
        return 0
    for name, text in outputs().items():
        if name in stale:
            (OUT / name).parent.mkdir(parents=True, exist_ok=True)
            (OUT / name).write_text(text, encoding="utf-8")
    print(f"wrote {len(stale)} file(s) in template/v4")
    return 0


# ---------------------------------------------------------------- checking a filled template

def placeholders(value: Any, path: str = "") -> list[str]:
    if isinstance(value, dict):
        return [p for k, v in value.items() if k != HEADER for p in placeholders(v, f"{path}.{k}" if path else k)]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in placeholders(v, f"{path}[{i}]")]
    return [f"{path}: {value}"] if isinstance(value, str) and PLACEHOLDER.search(value) else []


def schema_problems(record: dict, schema_path: Path, definition: str) -> list[str]:
    from jsonschema import Draft202012Validator
    schema = load(schema_path)
    local = {"$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"), "$defs": schema["$defs"],
             "$ref": f"#/$defs/{definition}"}
    return [f"schema {definition}: {'/'.join(str(p) for p in e.path) or '(record)'}: {e.message}"[:300]
            for e in Draft202012Validator(local).iter_errors(record)]


def library_questions() -> dict[str, dict]:
    found = {}
    for path in sorted(REPO.glob("*/library/**/*.json")):
        try:
            data = load(path)
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(data, dict):
            for q in data.get("questions") or []:
                if isinstance(q, dict) and q.get("id"):
                    found[q["id"]] = q
    return found


def bank_questions() -> dict[str, dict]:
    found = {}
    for path in sorted(REPO.glob("*/library/exam-bank/*.json")):
        try:
            data = load(path)
        except (ValueError, UnicodeDecodeError):
            continue
        for q in (data.get("questions") or []) if isinstance(data, dict) else []:
            if isinstance(q, dict) and q.get("id"):
                found[q["id"]] = q
    return found


def band_of_question(q: dict) -> str | None:
    d = q.get("difficulty") or (((q.get("extensions") or {}).get("grade9v3:analysis") or {}).get("difficulty")) or {}
    return d.get("band") if isinstance(d, dict) else None


def check_difficulty(d: Any, where: str) -> list[str]:
    if not isinstance(d, dict):
        return [f"{where}: no difficulty estimate"]
    out = []
    parts = d.get("components") or {}
    if isinstance(d.get("score"), int) and all(isinstance(v, int) for v in parts.values()) and parts:
        if sum(parts.values()) != d["score"]:
            out.append(f"{where}: score {d['score']} is not the sum of its components ({sum(parts.values())})")
        if band_of_score(d["score"]) != d.get("band"):
            out.append(f"{where}: band {d.get('band')} does not match score {d['score']} (the vocabulary puts it in {band_of_score(d['score'])})")
    return out


def check_question(record: dict, kind: str) -> list[str]:
    out = []
    if kind == "PYQ_QUESTION":
        out += schema_problems(record, PACKAGE_SCHEMA, "question")
        out += schema_problems(record.get("extensions", {}).get("grade9v3:analysis", {}), BANK_SCHEMA, "analysis")
        out += schema_problems(record.get("extensions", {}).get("grade9v3:source_custody", {}), BANK_SCHEMA, "source_custody")
        difficulty = ((record.get("extensions") or {}).get("grade9v3:analysis") or {}).get("difficulty")
        measured = record
    else:
        out += schema_problems(record, PACKAGE_SCHEMA, "question")
        difficulty = record.get("difficulty")
        # the blueprint reads the band where the exam bank keeps it; a package question keeps it at the top
        measured = copy.deepcopy(record)
        measured.setdefault("extensions", {}).setdefault("grade9v3:analysis", {})["difficulty"] = difficulty
    out += check_difficulty(difficulty, "difficulty")
    if record.get("status") not in AUTHOR_STATUSES:
        out.append(f"status {record.get('status')!r}: a new record is CANDIDATE; promotion is a review with a receipt")
    status = (record.get("answer") or {}).get("verification_status")
    allowed = AUTHOR_VERIFICATION
    authority = ((record.get("extensions") or {}).get("grade9v3:source_custody") or {}).get("answer_authority")
    if kind == "PYQ_QUESTION" and authority in OFFICIAL_KEYS:
        allowed = (*AUTHOR_VERIFICATION, "INDEPENDENTLY_CHECKED")     # the official key is the independent check
    if status not in allowed:
        out.append(f"answer.verification_status {status!r}: this record can claim only {' or '.join(allowed)}"
                   + ("" if kind != "PYQ_QUESTION" else " (INDEPENDENTLY_CHECKED needs an official key in source_custody.answer_authority)"))
    out += blueprints.record_problems(blueprint(CORE2), measured, "blueprint")
    return out


def check_core1a(record: dict) -> list[str]:
    out = schema_problems(record, PACKAGE_SCHEMA, "microtopic")
    if record.get("status") not in AUTHOR_STATUSES:
        out.append(f"status {record.get('status')!r}: a new record is CANDIDATE")
    exit_status = ((record.get("exit_task") or {}).get("answer") or {}).get("verification_status")
    if exit_status not in AUTHOR_VERIFICATION:
        out.append(f"exit_task.answer.verification_status {exit_status!r}: an author can claim only {' or '.join(AUTHOR_VERIFICATION)}")
    bp = blueprint(CORE1A)
    steps_c, checks_c = component(bp, "CONSTRUCTION_STEPS"), component(bp, "QUICK_CHECK")
    step_ids = {s.get("id") for s in record.get("teaching_path") or []}
    misconceptions = len(record.get("misconceptions") or [])
    questions = library_questions()
    bank = bank_questions()
    units = record.get("construction_units") or []
    if not units:
        out.append("construction_units: a Core1A concept is built in construction units; there are none")
    for cu in units:
        where = f"unit {cu.get('id')}"
        refs = cu.get("step_refs") or []
        missing = [r for r in refs if r not in step_ids]
        if missing:
            out.append(f"{where}: step_refs not in teaching_path: {missing}")
        bands = []
        for qid in cu.get("crux_question_refs") or []:
            q = bank.get(qid)
            if q is None:
                out.append(f"{where}: crux question {qid} is in no exam bank; a crux names a question of the product's bank "
                           "(bank_refs), or is left out")
            elif band_of_question(q):
                bands.append(band_of_question(q))
        band = max(bands) if bands else None
        need = blueprints.target_for(steps_c, band)
        if need and len(refs) < need:
            out.append(f"{where}: CONSTRUCTION_STEPS needs {need} steps for a {band or 'unbanded'} crux, the unit has {len(refs)}")
        checks = cu.get("independent_checks") or []
        if len(checks) < (checks_c.get("target_items") or 0):
            out.append(f"{where}: QUICK_CHECK needs {checks_c['target_items']} independent checks, the unit has {len(checks)}")
        roles = [c.get("role") for c in checks]
        if len(set(roles)) != len(roles):
            out.append(f"{where}: QUICK_CHECK roles repeat: {roles}")
        if not (cu.get("worked_anchor_ref") or cu.get("bank_anchor_ref")):
            out.append(f"{where}: WORKED_EXAMPLE needs a worked_anchor_ref or bank_anchor_ref")
        elif cu.get("worked_anchor_ref") and cu["worked_anchor_ref"] not in questions:
            out.append(f"{where}: worked_anchor_ref {cu['worked_anchor_ref']} is in no library")
        if not cu.get("representation_ref"):
            out.append(f"{where}: STAGED_VISUAL needs a representation_ref")
        bad = [i for i in cu.get("misconception_indexes") or [] if not (isinstance(i, int) and 0 <= i < misconceptions)]
        if bad:
            out.append(f"{where}: misconception_indexes {bad} point outside misconceptions[] ({misconceptions})")
    return out


def check_approval(record: dict, repo: Path = REPO) -> list[str]:
    out = []
    if record.get("decision") not in APPROVAL_DECISIONS:
        out.append(f"decision {record.get('decision')!r}: one of {', '.join(APPROVAL_DECISIONS)}")
    target = repo / str(record.get("subject_ref") or "")
    if record.get("kind") == "RUNGS":
        if not target.is_file():
            out.append(f"subject_ref {record.get('subject_ref')!r} is not a file")
        elif digest(target) != record.get("subject_digest"):
            out.append(f"STALE: {record['subject_ref']} has changed since it was approved ({record.get('subject_digest')} -> {digest(target)})")
    elif record.get("kind") == "ATLAS":
        now = atlas_digest(str(record.get("subject_ref")))
        if now != record.get("subject_digest"):
            out.append(f"STALE: the {record.get('subject_ref')} atlas has changed since it was approved ({record.get('subject_digest')} -> {now})")
    else:
        out.append(f"kind {record.get('kind')!r}: RUNGS or ATLAS")
    return out


def check_report(path: Path, into: Path | None = None, product: Path | None = None, extra: list[dict] = ()) -> dict:
    """check_file(), and with a package (and a product) what the real gates say the record adds, closes and waives."""
    problems = check_file(path)
    report = {"problems": problems, "closed": [], "waived": []}
    if into is None or any(p.startswith(("placeholder left", HEADER)) for p in problems):
        return report
    record = load(path)
    gates = gate_findings(record, into, product, list(extra))
    report["problems"] = problems + gates["new"]
    report["closed"], report["waived"] = gates["closed"], gates["waived"]
    return report


def check_file(path: Path) -> list[str]:
    record = load(path)
    if isinstance(record, dict) and "approval_id" in record and "subject_digest" in record:
        left = [f"placeholder left: {p}" for p in placeholders(record)]
        return left or check_approval(record)
    header = record.get(HEADER) if isinstance(record, dict) else None
    kind = (header or {}).get("kind") or ("CORE1A_MICROTOPIC" if "construction_units" in record else
                                          "PYQ_QUESTION" if "grade9v3:source_custody" in (record.get("extensions") or {}) else "LIBRARY_QUESTION")
    out = [f"placeholder left: {p}" for p in placeholders(record)]
    if header is not None:
        out.append(f"{HEADER} is still in the record: delete it once the record is filled")
        record = {k: v for k, v in record.items() if k != HEADER}
    if out:
        return out                      # an unfilled template has nothing further worth saying about it
    return check_core1a(record) if kind == "CORE1A_MICROTOPIC" else check_question(record, kind)


# ---------------------------------------------------------------- the real gates, on the record in place

COLLECTIONS = {"microtopics": "teaching_path", "questions": "stem", "representations": "rendered_asset_refs", "relations": "expression"}


def collection_of(record: dict) -> str:
    for name, marker in COLLECTIONS.items():
        if marker in record:
            return name
    raise ValueError(f"{record.get('id')}: not a microtopic, question, representation or relation")


def placed(package: dict, records: list[dict]) -> dict:
    """The package with each record added, or put in place of the one with its id."""
    out = copy.deepcopy(package)
    for record in records:
        rows = out.setdefault(collection_of(record), [])
        out[collection_of(record)] = [r for r in rows if r.get("id") != record.get("id")] + [record]
    return out


def library_findings(package: dict, subject_root: Path) -> set[str]:
    from Shared.library import depiction, intake
    found = {f"library schema: {e}" for e in intake.schema_errors(package)}
    found |= {f"library intake {f.get('point')}: {f.get('detail')}" for f in intake.check(package)["findings"]}
    records = {r["id"]: {**r, "_collection": name} for name in ("microtopics", "representations", "relations", "buckets", "questions")
               for r in package.get(name) or [] if isinstance(r, dict) and r.get("id")}
    found |= {f"depiction {f['point']} {f['record']}: {f['detail']}" for f in depiction.findings(records, depiction.declared_kinds(subject_root))}
    return found


_RENDERED: dict[tuple, tuple[set[str], list[dict]]] = {}


def renderer_gaps(manifest_path: Path) -> tuple[set[str], list[dict]]:
    """The renderer's gaps for a product at the reference depth (new authoring is held to the reference, not the floor).
    A committed product is rendered once per process; a staged one every time."""
    from Shared.tools import render_core
    manifest = load(manifest_path)
    inputs = [manifest_path] + [REPO / r for r in manifest.get("package_refs", []) + manifest.get("bank_refs", [])]
    key = (str(manifest_path), tuple(p.stat().st_mtime_ns for p in inputs if p.exists()))
    if SCRATCH in manifest_path.parents or key not in _RENDERED:
        _, gaps, _, _, waived = render_core.build_report(manifest_path, "PAGES", held_to="REFERENCE")
        result = ({f"renderer {g.get('core')} {g.get('duty')} {g.get('record')}: {g.get('detail')}" for g in gaps}, waived)
        if SCRATCH in manifest_path.parents:
            return result
        _RENDERED[key] = result
    return _RENDERED[key]


def role_of(question: dict) -> str:
    cores = {e.get("core") for e in question.get("exposure") or [] if isinstance(e, dict)}
    return "core2b" if "CORE2B" in cores else "core2" if "CORE2" in cores else "core2a"


def gate_findings(record: dict, package_path: Path, product_path: Path | None = None, extra: list[dict] = ()) -> dict:
    """What the record adds to what the real gates already say: the library intake and depiction on its package, and, with a
    product, the renderer at the reference depth. Returns {"new": [...], "closed": [...], "waived": [...]}."""
    package = load(package_path)
    after = placed(package, [*extra, record])
    subject_root = REPO / str(package.get("subject") or package_path.parts[len(REPO.parts)])
    before_set, after_set = library_findings(package, subject_root), library_findings(after, subject_root)
    waived: list[dict] = []
    if product_path is not None:
        import shutil
        import uuid
        manifest = load(product_path)
        stage = SCRATCH / uuid.uuid4().hex[:12]
        stage.mkdir(parents=True, exist_ok=True)
        try:
            staged_package = stage / package_path.name
            staged_package.write_text(dumps(after), encoding="utf-8")
            staged = copy.deepcopy(manifest)
            staged["package_refs"] = [rel(staged_package) if (REPO / ref).resolve() == package_path.resolve() else ref
                                      for ref in manifest["package_refs"]]
            if rel(staged_package) not in staged["package_refs"]:
                raise ValueError(f"{rel(package_path)} is not one of {rel(product_path)}'s package_refs")
            selection = staged.setdefault("selection", {})
            key = "microtopics" if collection_of(record) == "microtopics" else role_of(record) if collection_of(record) == "questions" else None
            if key and record["id"] not in selection.setdefault(key, []):
                selection[key].append(record["id"])
            staged_manifest = stage / "manifest.json"
            staged_manifest.write_text(dumps(staged), encoding="utf-8")
            gaps_before, _ = renderer_gaps(product_path)
            gaps_after, waived = renderer_gaps(staged_manifest)
            before_set, after_set = before_set | gaps_before, after_set | gaps_after
        finally:
            shutil.rmtree(stage, ignore_errors=True)
    ids = {record.get("id")} | {u.get("id") for u in record.get("construction_units") or []}
    seen = [w for w in waived if w.get("record") in ids]
    # every waiver the record declares goes to a reviewer, including one no page consults (Core2B has no components to waive)
    for component_id, reason in blueprints.waivers_of(record).items():
        if not any(w.get("component") == component_id for w in seen):
            seen.append({"component": component_id, "record": record.get("id"), "reason": reason, "core": None})
    return {"new": sorted(after_set - before_set), "closed": sorted(before_set - after_set), "waived": seen}


# ---------------------------------------------------------------- new: a template instantiated for one package

def package_of(path: Path) -> dict:
    data = load(path)
    if not isinstance(data, dict) or "microtopics" not in data:
        raise ValueError(f"{rel(path)} is not a subject package")
    return data


def new_question(band: str, package_path: Path, role: str) -> dict:
    package = package_of(package_path)
    record = question_template(band, "TRANSFER" if role == "CORE2B" else "LIBRARY")
    ids = [q["id"] for q in package.get("questions") or []]
    prefix = re.match(r"^([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-)", ids[0]).group(1) if ids and re.match(r"^([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-)", ids[0]) else "Q-"
    record["id"] = f"{prefix}{'2B' if role == 'CORE2B' else '2A'}-<<FILL: short name>>-01"
    record["primary_capability_ref"] = one_of([c["id"] for c in package.get("capabilities") or []])
    record["family_ref"] = one_of([f["id"] for f in package.get("question_families") or []])
    record["source_refs"] = [one_of([r["id"] for r in package.get("resources") or [] if r.get("id")])]
    record["origin_ref"] = one_of([r["id"] for r in package.get("resources") or [] if r.get("id")])
    record[HEADER]["package"] = rel(package_path)
    record[HEADER]["existing_ids"] = ids
    return record


def new_core1a(microtopic_id: str, package_path: Path) -> dict:
    package = package_of(package_path)
    existing = next((m for m in package["microtopics"] if m.get("id") == microtopic_id), None)
    if existing is None:
        raise ValueError(f"{microtopic_id} is not in {rel(package_path)}")
    template = core1a_template()
    header = template.pop(HEADER)
    record = copy.deepcopy(existing)
    record["construction_units"] = existing.get("construction_units") or template["construction_units"]
    if not existing.get("construction_units"):
        steps = [s.get("id") for s in existing.get("teaching_path") or []]
        for unit in record["construction_units"]:
            unit["id"] = unit["id"].replace("<<FILL: microtopic id without MIC->>", microtopic_id.removeprefix("MIC-"))
            unit["step_refs"] = [fill("a teaching_path step id; add a step to teaching_path when the unit needs one")
                                 for _ in unit["step_refs"]]
        header["existing_steps"] = steps
    kinds = sorted(load(REPO / package.get("subject", "") / "adapter/CoreContracts.json").get("representation_kinds", []) and
                   [k["id"] for k in load(REPO / package["subject"] / "adapter/CoreContracts.json")["representation_kinds"]])
    header.update({"package": rel(package_path), "representation_kinds": kinds,
                   "existing_representations": [r["id"] for r in package.get("representations") or []],
                   "existing_questions": [q["id"] for q in package.get("questions") or []]})
    return {HEADER: header, **record}




def library_packages(subject: str) -> list[tuple[Path, dict]]:
    rows = []
    for path in sorted((REPO / subject / "library").glob("*.json")):
        try:
            data = load(path)
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(data, dict) and data.get("microtopics") is not None:
            rows.append((path, data))
    return rows


def capability_owner(packages: list[tuple[Path, dict]]) -> dict[str, str]:
    return {m.get("primary_capability_ref"): m["id"] for _, p in packages for m in p.get("microtopics", []) if m.get("primary_capability_ref")}


def subject_questions(subject: str, packages: list[tuple[Path, dict]]) -> list[dict]:
    """The subject's questions: its packages' and its exam banks' (a Question Bank page shows both)."""
    found = [q for _, p in packages for q in p.get("questions") or []]
    for path in sorted((REPO / subject / "library" / "exam-bank").glob("*.json")):
        try:
            found += [q for q in load(path).get("questions") or [] if isinstance(q, dict)]
        except (ValueError, UnicodeDecodeError, AttributeError):
            continue
    return found


def bands_by_microtopic(subject: str, packages: list[tuple[Path, dict]]) -> dict[str, dict[str, int]]:
    owner = capability_owner(packages)
    out: dict[str, dict[str, int]] = {}
    for q in subject_questions(subject, packages):
        mic = owner.get(q.get("primary_capability_ref"))
        if mic:
            row = out.setdefault(mic, {b: 0 for b in (*BANDS, "none")})
            row[band_of_question(q) or "none"] += 1
    return out


def md_cell(value: Any) -> str:
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value)
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def rung_packet(matrix_path: Path) -> str:
    from Shared.tools import matrix_conformance
    board = load(matrix_path)
    found = matrix_conformance.board_findings(board)
    packages = library_packages(board.get("subject", ""))
    mics = {m["id"]: m for _, p in packages for m in p.get("microtopics", [])}
    bands = bands_by_microtopic(board.get("subject", ""), packages)
    rungs = board.get("rungs") or []
    flags = []
    positions = [r.get("ladder_position") for r in rungs]
    if positions != sorted(positions):
        flags.append("ladder positions are not in increasing order")
    for r in rungs:
        if r.get("provenance") != "SOURCE":
            flags.append(f"{r.get('rung')} is {r.get('provenance')}, not backed by a source: approve the authored step explicitly")
        if not r.get("microtopic_ref"):
            flags.append(f"{r.get('rung')} names no microtopic, so no record teaches it")
        elif r["microtopic_ref"] not in mics:
            flags.append(f"{r.get('rung')} names {r['microtopic_ref']}, which is in no {board.get('subject')} package")
        elif not sum(v for k, v in (bands.get(r["microtopic_ref"]) or {}).items() if k != "none"):
            flags.append(f"{r.get('rung')} ({r['microtopic_ref']}) has no banded question to practise it")
    lines = [
        f"# Rung ladder approval: {board.get('matrix_id')}",
        "",
        "Generated by `authoring_templates.py packet rungs`. The Owner approves the data below, identified by its digest; if the file",
        "changes after approval, the approval is reported stale.",
        "",
        "| | |", "|---|---|",
        f"| File | `{rel(matrix_path)}` |",
        f"| Digest | `{digest(matrix_path)}` |",
        f"| Subject / bucket | {md_cell(board.get('subject'))} / `{md_cell(board.get('bucket_id'))}` |",
        f"| Topic / subtopic | {md_cell(board.get('topic'))} / {md_cell(board.get('subtopic'))} |",
        f"| Axis | {md_cell(board.get('axis_note'))} |",
        f"| Matrix conformance | {'pass' if not found else f'{len(found)} finding(s)'} |",
        "",
        "A ladder rung (R1, R2, ...) is a position on this capability ladder: it sets where Core1A and Core1B start and the support",
        "level of practice. It is not a hint rung (the staged help on one question).",
        "",
        "## The ladder",
        "",
        "| Rung | Position | Provenance | Microtopic | Vocabulary ceiling | Must contain | Questions D1/D2/D3/D4 (no band) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rungs:
        b = bands.get(r.get("microtopic_ref") or "", {})
        counts = "/".join(str(b.get(k, 0)) for k in BANDS) + f" ({b.get('none', 0)})"
        lines.append(f"| {md_cell(r.get('rung'))} | {md_cell(r.get('ladder_position'))} | {md_cell(r.get('provenance'))} | "
                     f"`{md_cell(r.get('microtopic_ref'))}` | {md_cell(r.get('ceiling'))} | {md_cell(r.get('must_contain'))} | {counts} |")
    lines += ["", "### Controlled variation per rung", ""]
    for r in rungs:
        for phase in r.get("controlled_variation") or []:
            lines.append(f"- **{md_cell(r.get('rung'))}** phase {md_cell(phase.get('phase'))}: vary {md_cell(phase.get('vary'))}; "
                         f"hold {md_cell(phase.get('hold'))}; notice {md_cell(phase.get('notice'))}")
    family = board.get("family") or {}
    lines += ["", "## Family and transfer", "",
              f"- **Invariant demand:** {md_cell(family.get('invariant_demand'))}",
              f"- **Difficult move:** {md_cell(family.get('difficult_move'))}", ""]
    if board.get("transfer"):
        lines += ["| Dimension | Changed demand | Not handed over | Repair to |", "|---|---|---|---|"]
        lines += [f"| {md_cell(t.get('dimension'))} | {md_cell(t.get('changed_demand'))} | {md_cell(t.get('information_not_handed_over'))} | "
                  f"{md_cell(t.get('repair_to'))} |" for t in board["transfer"]]
    lines += ["", "## What needs your decision", ""]
    lines += [f"- {f}" for f in flags] or ["- Nothing flagged by the data; the ladder order and ceilings still need your judgement."]
    lines += [f"- Matrix conformance: {f.get('point')} at {f.get('where')}: {f.get('detail')}" for f in found]
    lines += ["", "## Your decision", "",
              "For each rung: APPROVED, or REVISE with a note. Then the whole ladder: APPROVED or REVISE.", "",
              "```json", dumps({**APPROVAL_RECORD, "approval_id": f"APPROVAL-RUNGS-{board.get('matrix_id')}", "kind": "RUNGS",
                                 "subject_ref": rel(matrix_path), "subject_digest": digest(matrix_path),
                                 "items": [{"ref": r.get("rung"), "decision": "PENDING", "note": ""} for r in rungs]}).rstrip(), "```", ""]
    return "\n".join(lines)


def atlas_rows(subject: str) -> list[dict]:
    packages = library_packages(subject)
    known = {item["id"] for s in ("Physics", "Chemistry", "Mathematics") for _, p in library_packages(s)
             for key in ("microtopics", "capabilities") for item in p.get(key) or [] if isinstance(item, dict) and item.get("id")}
    bands = bands_by_microtopic(subject, packages)
    rungs = {load(p).get("bucket_id"): rel(p) for p in sorted((REPO / subject / "matrices").glob("*.rungs.json"))}
    rows = []
    for path, p in packages:
        for bucket in p.get("buckets") or [{"id": None, "title": p.get("title")}]:
            mics = [m for m in p.get("microtopics", []) if bucket.get("id") in (None, m.get("bucket_id"))]
            totals = {b: sum((bands.get(m["id"]) or {}).get(b, 0) for m in mics) for b in (*BANDS, "none")}
            rows.append({
                "package": rel(path), "bucket": bucket.get("id"), "title": bucket.get("title") or p.get("title"),
                "microtopics": [{"id": m["id"], "title": m.get("title"), "badge": m.get("intrinsic_badge"),
                                 "core1a": bool(m.get("construction_units")),
                                 "prerequisites": m.get("prerequisite_refs") or [],
                                 "unresolved": [r for r in m.get("prerequisite_refs") or [] if r not in known]}
                                for m in mics],
                "questions": totals, "rungs": rungs.get(bucket.get("id")),
            })
    return rows


def atlas_digest(subject: str) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(atlas_rows(subject), sort_keys=True).encode("utf-8")).hexdigest()


def atlas_packet(subject: str) -> str:
    rows = atlas_rows(subject)
    lines = [
        f"# Atlas approval: {subject}",
        "",
        "Generated by `authoring_templates.py packet atlas`. It reads the subject's library packages and rung ladders; the digest",
        "covers exactly what is shown, so a change to scope, prerequisites, Core1A coverage or question bands makes an approval stale.",
        "",
        f"Digest: `{atlas_digest(subject)}`",
        "",
        "## Scope and coverage",
        "",
        "| Bucket | Title | Microtopics | With Core1A units | Questions D1/D2/D3/D4 (no band) | Rung ladder |",
        "|---|---|---|---|---|---|",
    ]
    flags = []
    for r in rows:
        q = r["questions"]
        lines.append(f"| `{md_cell(r['bucket'])}` | {md_cell(r['title'])} | {len(r['microtopics'])} | "
                     f"{sum(m['core1a'] for m in r['microtopics'])} | {'/'.join(str(q[b]) for b in BANDS)} ({q['none']}) | "
                     f"{md_cell(r['rungs'] and '`' + r['rungs'] + '`')} |")
        if not r["rungs"]:
            flags.append(f"`{r['bucket']}` has no rung ladder: where Core1A and Core1B start is undecided")
        missing = [b for b in BANDS if not q[b]]
        if missing:
            flags.append(f"`{r['bucket']}` has no question at {', '.join(missing)}")
        for m in r["microtopics"]:
            if m["unresolved"]:
                flags.append(f"`{m['id']}` names prerequisites that resolve to nothing: {m['unresolved']}")
    lines += ["", "## Prerequisites", ""]
    for r in rows:
        for m in r["microtopics"]:
            if m["prerequisites"]:
                lines.append(f"- `{m['id']}` ({md_cell(m['badge'])}) needs: " + ", ".join(f"`{p}`" for p in m["prerequisites"]))
    lines += ["", "## What needs your decision", ""]
    lines += [f"- {f}" for f in flags] or ["- Nothing flagged by the data."]
    lines += ["", "## Your decision", "",
              "Per bucket: in scope (APPROVED) or not yet (REVISE, with the reason), and the number of questions you want per band.",
              "Those targets become the denominator an agent's work is counted against.", "",
              "```json", dumps({**APPROVAL_RECORD, "approval_id": f"APPROVAL-ATLAS-{subject.upper()}", "kind": "ATLAS",
                                 "subject_ref": subject, "subject_digest": atlas_digest(subject),
                                 "items": [{"ref": r["bucket"], "decision": "PENDING", "note": ""} for r in rows],
                                 "band_targets": {r["bucket"]: {b: None for b in BANDS} for r in rows}}).rstrip(), "```", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- command line

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="regenerate template/v4/")
    w.add_argument("--check", action="store_true", help="exit 1 when template/v4/ is stale, writing nothing")
    n = sub.add_parser("new", help="a template instantiated for one package")
    n.add_argument("what", choices=("question", "core1a"))
    n.add_argument("--package", required=True)
    n.add_argument("--band", choices=BANDS)
    n.add_argument("--role", choices=("CORE2A", "CORE2B"), default="CORE2A")
    n.add_argument("--microtopic")
    n.add_argument("--out")
    c = sub.add_parser("check", help="a filled template or an approval record")
    c.add_argument("files", nargs="+")
    c.add_argument("--into", help="the subject package the record joins: run the library intake and depiction on it in place")
    c.add_argument("--product", help="the product manifest that shows it: also run the renderer at the reference depth")
    c.add_argument("--with", dest="extra", nargs="*", default=[], help="JSON files of records the record needs (representations, relations)")
    p = sub.add_parser("packet", help="an approval packet for the Owner")
    p.add_argument("what", choices=("rungs", "atlas"))
    p.add_argument("--matrix")
    p.add_argument("--subject")
    p.add_argument("--out", help="write the packet here instead of printing it")
    args = parser.parse_args(argv)
    path = lambda value: Path(value) if Path(value).is_absolute() else REPO / value      # noqa: E731

    if args.cmd == "write":
        return write(args.check)
    if args.cmd == "new":
        if args.what == "question":
            if not args.band:
                parser.error("new question needs --band")
            record = new_question(args.band, path(args.package), args.role)
        else:
            if not args.microtopic:
                parser.error("new core1a needs --microtopic")
            record = new_core1a(args.microtopic, path(args.package))
        text = dumps(record)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            sys.stdout.write(text)
        return 0
    if args.cmd == "check":
        extra = []
        for name in args.extra:
            data = load(path(name))
            extra += data if isinstance(data, list) else [data]
        failed = 0
        for name in args.files:
            report = check_report(Path(name), path(args.into) if args.into else None, path(args.product) if args.product else None, extra)
            problems = report["problems"]
            print(f"{name}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
            for problem in problems:
                print(f"  - {problem}")
            for closed in report["closed"]:
                print(f"  closes: {closed}")
            for waiver in report["waived"]:
                print(f"  WAIVED, for a reviewer to accept: {waiver.get('component')} on {waiver.get('record')}: {waiver.get('reason')}")
            failed += bool(problems)
        return 1 if failed else 0
    if args.what == "rungs":
        if not args.matrix:
            parser.error("packet rungs needs --matrix")
        text = rung_packet(path(args.matrix))
    else:
        if not args.subject:
            parser.error("packet atlas needs --subject")
        text = atlas_packet(args.subject)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
