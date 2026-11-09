# -*- coding: utf-8 -*-
# app/tests/unitary/coevaluation_helper_test.py

import unittest
from collections import namedtuple

from app.helpers.coevaluation_helper import (
    ITEMS, N_ITEMS, MAX_TOTAL, compute_results, get_level, school_index,
    sections_label, generate_token, hash_token, get_instrument)
from app.schemas.teacher_coevaluation_schema import (
    CoevaluationScoresSchema, scores_to_list)
from marshmallow import ValidationError


TeacherLink = namedtuple("TeacherLink", "id")
Section = namedtuple("Section", "grade name teacher isDeleted")


def payload(scores):
    return {"scores": [{"number": i + 1, "score": s} for i, s in enumerate(scores)]}


class CoevaluationHelperTest(unittest.TestCase):

    def test_instrument_has_15_items_and_max_75(self):
        self.assertEqual(N_ITEMS, 15)
        self.assertEqual(MAX_TOTAL, 75)
        self.assertEqual([item["number"] for item in ITEMS], list(range(1, 16)))
        instrument = get_instrument()
        self.assertEqual(len(instrument["scale"]), 6)
        self.assertEqual([d["code"] for d in instrument["dimensions"]], ["A", "B", "C"])

    def test_averages_keep_decimals(self):
        results = compute_results([4] * 15, [3] * 15)
        self.assertEqual(results["averages"], [3.5] * 15)
        self.assertEqual(results["totalScore"], 52.5)
        self.assertEqual(results["percentage"], 70.0)
        self.assertEqual(results["level"], "commitment")

    def test_missing_side_returns_none(self):
        self.assertIsNone(compute_results([], [3] * 15))
        self.assertIsNone(compute_results([3] * 15, None))
        self.assertIsNone(compute_results([3] * 14, [3] * 15))

    def test_level_boundaries(self):
        cases = [
            (75, "excellence"), (60, "excellence"), (59.5, "commitment"),
            (45, "commitment"), (44.5, "progress"), (30, "progress"),
            (29.5, "beginning"), (0, "beginning"),
        ]
        for total, code in cases:
            self.assertEqual(get_level(total)["code"], code, total)
        self.assertIsNone(get_level(None))

    def test_percentage_of_boundary_case(self):
        # 44.5 pts = 59.33 % -> En avance (no Compromiso)
        teacher = [3] * 14 + [0]
        coordinator = [3] * 14 + [1]
        results = compute_results(teacher, coordinator)
        self.assertEqual(results["totalScore"], 42.5)
        results = compute_results([3] * 15, [3] * 14 + [2])
        self.assertEqual(results["totalScore"], 44.5)
        self.assertEqual(results["percentage"], 59.33)
        self.assertEqual(results["level"], "progress")

    def test_school_index_ignores_none(self):
        self.assertEqual(school_index([80.0, 60.0, None]), 70.0)
        self.assertIsNone(school_index([]))
        self.assertIsNone(school_index([None]))

    def test_sections_label(self):
        sections = [
            Section("4", "B", TeacherLink("t1"), False),
            Section("3", "A", TeacherLink("t1"), False),
            Section("3", "B", TeacherLink("t2"), False),
            Section("5", "A", TeacherLink("t1"), True),
            Section("6", "A", None, False),
        ]
        self.assertEqual(sections_label(sections, "t1"), u"3er Grado A, 4to Grado B")
        self.assertEqual(sections_label(sections, "t9"), u"")

    def test_token_is_random_and_hash_is_stable(self):
        a, b = generate_token(), generate_token()
        self.assertNotEqual(a, b)
        self.assertEqual(len(a), 64)
        self.assertEqual(hash_token(a), hash_token(a))
        self.assertNotEqual(hash_token(a), a)
        self.assertIsNone(hash_token(None))


class CoevaluationScoresSchemaTest(unittest.TestCase):

    def test_valid_payload_is_ordered(self):
        data = payload(list(range(5)) * 3)
        data["scores"].reverse()
        loaded = CoevaluationScoresSchema().load(data)
        self.assertEqual(scores_to_list(loaded), list(range(5)) * 3)

    def test_rejects_missing_or_duplicated_items(self):
        data = payload([3] * 14)
        with self.assertRaises(ValidationError):
            CoevaluationScoresSchema().load(data)
        data = payload([3] * 15)
        data["scores"][14]["number"] = 1
        with self.assertRaises(ValidationError):
            CoevaluationScoresSchema().load(data)

    def test_rejects_out_of_range_and_non_integer(self):
        for bad in (6, -1, 3.5, "3"):
            data = payload([3] * 15)
            data["scores"][0]["score"] = bad
            with self.assertRaises(ValidationError, msg=repr(bad)):
                CoevaluationScoresSchema().load(data)

    def test_rejects_missing_scores_key(self):
        with self.assertRaises(ValidationError):
            CoevaluationScoresSchema().load({})
