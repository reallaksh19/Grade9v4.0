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

def question_template(band: str, kind: str) -> dict:
    """kind LIBRARY: a question in a subject package (authored, adapted, NCERT, exemplar); kind PYQ: an exam-bank question."""
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
                        else "questions[] of the subject package <Subject>/library/<slug>.v1.json"),
        "rules": [
            "Replace every <<FILL: ...>> and <<ONE OF: ...>>; delete this $template block; run `authoring_templates.py check FILE`.",
            "status stays CANDIDATE: promotion is a review with a receipt, never an edit.",
            "answer.verification_status is NOT_RUN or CHECKED_BY_AUTHOR: an author cannot check their own key independently.",
            f"The band is {band}: score {lo} to {hi}, the sum of the five components. A different score means a different template.",
            f"scaffolds: {blueprints.target_for(ladder, band)} rungs for {band}, in the order the learner meets them.",
            "adaptation is null unless origin is ADAPTED; then it names the parent and what changed.",
            "An EXPECTED component you leave empty needs a written reason in extensions['grade9v3:component_waivers'] {COMPONENT_ID: reason}.",
            "Never write HTML: the renderer makes the page from this record.",
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
                      include=("decision", "crux_question_refs", "crux_step_ref", "relation_refs", "worked_anchor_ref",
                               "representation_ref", "reveal_stage_refs", "misconception_indexes", "independent_checks"))
        cu["id"] = f"CU-<<FILL: microtopic id without MIC->>-{unit}"
        cu["decision"] = fill(f"UNIT_HEADER unit {unit}: the decision this unit teaches the learner to make")
        cu["step_refs"] = refs
        cu["crux_question_refs"] = [fill(f"QUESTION_BRIDGE unit {unit}: id of {crux} whose crux this unit builds")]
        cu["crux_step_ref"] = refs[-1]
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
            "One construction unit per decision the learner must make. The two units here show both depths: a unit that builds the "
            f"crux of a D1 or D2 question needs {blueprints.target_for(steps_c, 'D1')} steps, of a D3 or D4 question "
            f"{blueprints.target_for(steps_c, 'D3')}. Copy or delete units to match the microtopic.",
            "Every step_refs id is a teaching_path step; every crux question exists in a library or exam bank; every "
            "misconception index points into misconceptions.",
            f"QUICK_CHECK: {checks_c.get('target_items')} independent checks per unit, one per role ({', '.join(roles)}).",
            "Never write HTML: the renderer makes the page from this record.",
        ],
        "components": guide(bp, None),
    }, **record}
    return record


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
        "| `approvals/owner-approval.template.json` | the Owner's decision on a rung ladder or the atlas | `approvals/` beside what it approves |",
        "",
        "An owner-supplied question is not authored from a template: `owner_bank.py new` keeps the Owner's words verbatim.",
        "",
        "## The loop an agent follows",
        "",
        "1. Copy the template for the record and band. Choose the band from the score (vocabulary ranges), never the other way round.",
        "2. Fill it. The `$template.components` list says, per component, which fields it reads, how many items the band needs, and how to write them.",
        "3. `python3 Shared/tools/authoring_templates.py check FILE` until it prints nothing: no placeholder, schema-valid, blueprint depth met, no claim an author cannot make.",
        "4. Delete `$template` and add the record to its file. `render_core.py gaps` then shows what the product still needs.",
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
        out[f"question-bank/pyq-question.{band}.template.json"] = dumps(question_template(band, "PYQ"))
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
            q = questions.get(qid)
            if q is None:
                out.append(f"{where}: crux question {qid} is in no library or exam bank")
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


# ---------------------------------------------------------------- approval packets

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
    c = sub.add_parser("check", help="a filled template or an approval record")
    c.add_argument("files", nargs="+")
    p = sub.add_parser("packet", help="an approval packet for the Owner")
    p.add_argument("what", choices=("rungs", "atlas"))
    p.add_argument("--matrix")
    p.add_argument("--subject")
    p.add_argument("--out", help="write the packet here instead of printing it")
    args = parser.parse_args(argv)

    if args.cmd == "write":
        return write(args.check)
    if args.cmd == "check":
        failed = 0
        for name in args.files:
            problems = check_file(Path(name))
            print(f"{name}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
            for problem in problems:
                print(f"  - {problem}")
            failed += bool(problems)
        return 1 if failed else 0
    if args.what == "rungs":
        if not args.matrix:
            parser.error("packet rungs needs --matrix")
        text = rung_packet(Path(args.matrix) if Path(args.matrix).is_absolute() else REPO / args.matrix)
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
