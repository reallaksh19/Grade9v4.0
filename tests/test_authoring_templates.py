"""The authoring templates are projections of the blueprint, and a filled one passes only when it is complete and claims nothing an
author cannot claim. Each shortcut an agent could take is tried here and must be refused."""
from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from Shared.tools import authoring_templates as at
from Shared.tools import web_blueprint_contract as blueprints

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "template/v4"


def template(name: str) -> dict:
    return json.loads((TEMPLATES / name).read_text(encoding="utf-8"))


def filled(value, ids: dict[str, str]):
    """Fill every placeholder the way an author would: the named ids where the template asks for them, the first choice of
    every choice, a sentence for every text, 1 for every number."""
    if isinstance(value, dict):
        return {k: filled(v, ids) for k, v in value.items() if k != at.HEADER}
    if isinstance(value, list):
        return [filled(v, ids) for v in value]
    if not isinstance(value, str) or not at.PLACEHOLDER.search(value):
        return value
    for marker, real in ids.items():
        value = value.replace(f"<<FILL: {marker}>>", real)
    choice = re.fullmatch(r"<<ONE OF: ([^|>]+?)(?: \|[^>]*)?>>", value)
    if choice:
        first = choice.group(1).strip()
        return {"True": True, "False": False}.get(first, first)
    if re.fullmatch(r"<<FILL: [^>]*\((integer|number)\)>>", value):
        return 1
    return at.PLACEHOLDER.sub("Authored text written for this record.", value)


def library_question_ids() -> dict[str, list[str]]:
    by_band: dict[str, list[str]] = {}
    for qid, q in sorted(at.library_questions().items()):
        if at.band_of_question(q):
            by_band.setdefault(at.band_of_question(q), []).append(qid)
    return by_band


class GeneratedFromTheBlueprint(unittest.TestCase):
    def test_committed_templates_are_what_the_sources_give(self):
        self.assertEqual(at.write(check_only=True), 0, "run: python3 Shared/tools/authoring_templates.py write")

    def test_each_band_gets_the_hint_ladder_and_score_range_the_sources_set(self):
        ladder = at.component(at.blueprint(at.CORE2), "HINT_LADDER")
        for band in at.BANDS:
            for kind in ("library", "pyq"):
                t = template(f"question-bank/{kind}-question.{band}.template.json")
                self.assertEqual(len(t["scaffolds"]), blueprints.target_for(ladder, band), f"{kind} {band}")
                self.assertEqual(t[at.HEADER]["score_range"], list(at.band_range(band)))
                self.assertEqual(t["status"], "CANDIDATE")

    def test_core1a_units_show_both_depths_the_blueprint_asks_for(self):
        steps = at.component(at.blueprint(at.CORE1A), "CONSTRUCTION_STEPS")
        units = template("core1a/microtopic.template.json")["construction_units"]
        self.assertEqual([len(u["step_refs"]) for u in units],
                         [blueprints.target_for(steps, "D1"), blueprints.target_for(steps, "D3")])

    def test_an_unfilled_template_fails_and_says_where(self):
        for path in sorted(TEMPLATES.rglob("*.template.json")):
            with self.subTest(path.name):
                problems = at.check_file(path)
                self.assertTrue(any(p.startswith("placeholder left") for p in problems), problems[:3])


class AFilledQuestion(unittest.TestCase):
    def setUp(self):
        self.record = filled(template("question-bank/library-question.D2.template.json"),
                             {"question id": "Q-TEST-TEMPLATE-D2-01", "id": "Q-TEST-TEMPLATE-D2-01"})
        self.record["adaptation"] = None
        self.record["primary_capability_ref"] = "CAP-NLM-SECOND-LAW"
        self.record["options"] = ["(A) 1 N", "(B) 2 N", "(C) 3 N", "(D) 4 N"]
        self.record["conditions"] = ["The surface is frictionless."]
        self.record["extensions"]["grade9v3:analysis"]["expected_time_seconds"] = 120
        self.record["extensions"]["grade9v3:component_waivers"] = {"REPRESENTATION": "The stem gives every quantity; no figure is needed."}
        self.record["answer"]["crux_move_ref"] = "Q-TEST-TEMPLATE-D2-01-MOVE-3"
        self.record["difficulty"] = {"band": "D2", "score": 4, "basis": "Two connected relations, one representation step.",
                                     "components": {"concept_model_selection": 1, "representation_translation": 1,
                                                    "reasoning_chain_length": 1, "algebra_computational_load": 1,
                                                    "trap_exception_sensitivity": 0}}

    def problems(self, record=None):
        return at.check_question(record or self.record, "LIBRARY_QUESTION")

    def test_a_complete_record_passes(self):
        self.assertEqual(self.problems(), [])

    def test_promoting_itself_is_refused(self):
        for status in ("PUBLISHED", "REVIEWED"):      # one the schema does not know, one it does but only a review may set
            bad = dict(self.record, status=status)
            self.assertTrue(any(p.startswith("status") for p in self.problems(bad)), status)

    def test_claiming_a_verification_nobody_ran_is_refused(self):
        for claim in ("VERIFIED_CANONICAL", "INDEPENDENTLY_CHECKED"):
            bad = copy.deepcopy(self.record)
            bad["answer"]["verification_status"] = claim
            self.assertTrue(any("verification_status" in p for p in self.problems(bad)), claim)

    def test_a_band_that_its_score_does_not_support_is_refused(self):
        bad = copy.deepcopy(self.record)
        bad["difficulty"]["band"] = "D4"
        self.assertTrue(any("does not match score" in p for p in self.problems(bad)))
        bad = copy.deepcopy(self.record)
        bad["difficulty"]["score"] = 5
        self.assertTrue(any("not the sum" in p for p in self.problems(bad)))

    def test_a_short_hint_ladder_is_refused_at_the_bands_depth(self):
        bad = copy.deepcopy(self.record)
        bad["scaffolds"] = bad["scaffolds"][:2]
        self.assertTrue(any("HINT_LADDER" in p for p in self.problems(bad)))
        harder = copy.deepcopy(self.record)                    # the same three rungs are too few once the band is D3
        harder["difficulty"].update(band="D3", score=6, components={**harder["difficulty"]["components"], "trap_exception_sensitivity": 2})
        self.assertTrue(any("HINT_LADDER" in p for p in self.problems(harder)))

    def test_an_expected_component_left_out_needs_a_reason(self):
        bad = copy.deepcopy(self.record)
        del bad["extensions"]["grade9v3:component_waivers"]
        self.assertTrue(any("REPRESENTATION" in p for p in self.problems(bad)))

    def test_a_placeholder_left_anywhere_stops_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = copy.deepcopy(self.record)
            bad["conditions"].append("<<FILL: CONDITIONS conditions[]>>")
            path = Path(tmp) / "q.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            self.assertEqual(at.check_file(path), ["placeholder left: conditions[1]: <<FILL: CONDITIONS conditions[]>>"])


class AnExamBankQuestion(unittest.TestCase):
    def setUp(self):
        bank = json.loads((REPO / "Physics/library/exam-bank/competitive-exam-question-bank.v2.json").read_text(encoding="utf-8"))
        self.question = next(q for q in bank["questions"] if q["answer"].get("verification_status") == "INDEPENDENTLY_CHECKED")

    def verification(self, q):
        return [p for p in at.check_question(q, "PYQ_QUESTION") if "verification_status" in p]

    def test_an_official_key_lets_it_say_independently_checked(self):
        q = copy.deepcopy(self.question)
        q["extensions"]["grade9v3:source_custody"]["answer_authority"] = "OFFICIAL_FINAL_KEY"
        self.assertEqual(self.verification(q), [])

    def test_without_an_official_key_it_cannot(self):
        q = copy.deepcopy(self.question)
        q["extensions"]["grade9v3:source_custody"]["answer_authority"] = "NOT_AN_OFFICIAL_KEY"
        self.assertTrue(self.verification(q))


class AFilledCore1A(unittest.TestCase):
    def setUp(self):
        bands = library_question_ids()
        self.easy, self.hard = (bands.get("D2") or bands["D1"])[0], (bands.get("D3") or bands["D4"])[0]
        record = filled(template("core1a/microtopic.template.json"), {"microtopic id": "MIC-TEST-TEMPLATE", "microtopic id without MIC-": "TEST-TEMPLATE"})
        record.update({"id": "MIC-TEST-TEMPLATE", "bucket_id": "BUCKET-PHY-NLM-FIRST-LAW", "primary_capability_ref": "CAP-TEST-TEMPLATE"})
        record["exit_task"]["answer"]["verification_status"] = "CHECKED_BY_AUTHOR"
        for unit, crux in zip(record["construction_units"], (self.easy, self.hard)):
            unit["crux_question_refs"] = [crux]
            unit["worked_anchor_ref"] = crux
            unit["representation_ref"] = "REP-TEST-TEMPLATE"
            unit["relation_refs"] = ["REL-TEST-TEMPLATE"]
        self.record = record

    def test_a_complete_record_passes(self):
        self.assertEqual(at.check_core1a(self.record), [])

    def test_a_step_that_is_not_on_the_teaching_path_is_refused(self):
        bad = copy.deepcopy(self.record)
        bad["construction_units"][0]["step_refs"].append("MIC-TEST-TEMPLATE-S99")
        self.assertTrue(any("not in teaching_path" in p for p in at.check_core1a(bad)))

    def test_a_hard_crux_built_in_too_few_steps_is_refused(self):
        bad = copy.deepcopy(self.record)
        bad["construction_units"][1]["step_refs"] = bad["construction_units"][1]["step_refs"][:3]
        self.assertTrue(any("CONSTRUCTION_STEPS" in p for p in at.check_core1a(bad)))

    def test_a_crux_question_that_does_not_exist_is_refused(self):
        bad = copy.deepcopy(self.record)
        bad["construction_units"][0]["crux_question_refs"] = ["Q-DOES-NOT-EXIST"]
        self.assertTrue(any("in no library" in p for p in at.check_core1a(bad)))

    def test_two_quick_checks_and_a_dangling_misconception_are_refused(self):
        bad = copy.deepcopy(self.record)
        bad["construction_units"][0]["independent_checks"] = bad["construction_units"][0]["independent_checks"][:2]
        bad["construction_units"][0]["misconception_indexes"] = [3]
        problems = at.check_core1a(bad)
        self.assertTrue(any("QUICK_CHECK" in p for p in problems))
        self.assertTrue(any("misconception_indexes" in p for p in problems))


class OwnerApprovals(unittest.TestCase):
    MATRIX = "Physics/matrices/phy-kin-2d-motion.rungs.json"

    def test_the_rung_packet_names_the_digest_and_every_rung(self):
        packet = at.rung_packet(REPO / self.MATRIX)
        self.assertIn(at.digest(REPO / self.MATRIX), packet)
        for rung in json.loads((REPO / self.MATRIX).read_text(encoding="utf-8"))["rungs"]:
            self.assertIn(f"| {rung['rung']} |", packet)

    def test_an_approval_goes_stale_when_the_ladder_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_path = Path(tmp) / self.MATRIX
            copy_path.parent.mkdir(parents=True)
            shutil.copy(REPO / self.MATRIX, copy_path)
            record = {"approval_id": "APPROVAL-RUNGS-TEST", "kind": "RUNGS", "subject_ref": self.MATRIX,
                      "subject_digest": at.digest(copy_path), "decision": "APPROVED", "items": []}
            self.assertEqual(at.check_approval(record, Path(tmp)), [])
            board = json.loads(copy_path.read_text(encoding="utf-8"))
            board["rungs"][0]["ceiling"].append("calculus")
            copy_path.write_text(json.dumps(board), encoding="utf-8")
            self.assertTrue(any(p.startswith("STALE") for p in at.check_approval(record, Path(tmp))))

    def test_the_atlas_packet_is_deterministic_and_carries_its_digest(self):
        first, second = at.atlas_packet("Physics"), at.atlas_packet("Physics")
        self.assertEqual(first, second)
        self.assertIn(at.atlas_digest("Physics"), first)


if __name__ == "__main__":
    unittest.main()
