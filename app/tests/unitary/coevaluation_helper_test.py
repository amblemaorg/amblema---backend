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

    def test_instrument_has_15_items_and_max_105(self):
        self.assertEqual(N_ITEMS, 15)
        self.assertEqual(MAX_TOTAL, 105)
        self.assertEqual([item["number"] for item in ITEMS], list(range(1, 16)))
        self.assertEqual(ITEMS[10]["title"], u"Asistencia")
        self.assertEqual(ITEMS[14]["title"], u"Feria AmbLeMa")
        instrument = get_instrument()
        self.assertEqual(len(instrument["scale"]), 8)
        self.assertEqual([d["code"] for d in instrument["dimensions"]], ["A", "B", "C"])

    def test_averages_take_integer_part(self):
        # (6 + 5) / 2 = 5.5 -> 5 por ítem; total 75 / 105 = 71.43 %
        results = compute_results([6] * 15, [5] * 15)
        self.assertEqual(results["averages"], [5] * 15)
        self.assertEqual(results["totalScore"], 75)
        self.assertEqual(results["percentage"], 71.43)
        self.assertEqual(results["level"], "commitment")

    def test_averages_are_integers_per_item(self):
        teacher = [7, 1, 0, 7, 2] + [0] * 10
        coordinator = [6, 0, 0, 7, 5] + [1] * 10
        results = compute_results(teacher, coordinator)
        self.assertEqual(results["averages"][:5], [6, 0, 0, 7, 3])
        self.assertEqual(results["averages"][5:], [0] * 10)
        self.assertTrue(all(isinstance(a, int) for a in results["averages"]))
        self.assertEqual(results["totalScore"], 16)
        self.assertIsInstance(results["totalScore"], int)

    def test_missing_side_returns_none(self):
        self.assertIsNone(compute_results([], [3] * 15))
        self.assertIsNone(compute_results([3] * 15, None))
        self.assertIsNone(compute_results([3] * 14, [3] * 15))

    def test_level_boundaries(self):
        cases = [
            (105, "excellence"), (84, "excellence"), (83.5, "commitment"),
            (63, "commitment"), (62.5, "progress"), (42, "progress"),
            (41.5, "beginning"), (0, "beginning"),
        ]
        for total, code in cases:
            self.assertEqual(get_level(total)["code"], code, total)
        self.assertIsNone(get_level(None))

    def test_percentage_of_boundary_case(self):
        # 62 pts = 59.05 % -> En avance (no Compromiso)
        results = compute_results([5] * 2 + [4] * 13, [5] * 2 + [4] * 13)
        self.assertEqual(results["totalScore"], 62)
        self.assertEqual(results["percentage"], 59.05)
        self.assertEqual(results["level"], "progress")
        # 63 pts justos = 60.0 % -> Compromiso
        results = compute_results([5] * 3 + [4] * 12, [5] * 3 + [4] * 12)
        self.assertEqual(results["totalScore"], 63)
        self.assertEqual(results["percentage"], 60.0)
        self.assertEqual(results["level"], "commitment")

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
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6]
        data = payload(expected)
        data["scores"].reverse()
        loaded = CoevaluationScoresSchema().load(data)
        self.assertEqual(scores_to_list(loaded), expected)

    def test_rejects_missing_or_duplicated_items(self):
        data = payload([3] * 14)
        with self.assertRaises(ValidationError):
            CoevaluationScoresSchema().load(data)
        data = payload([3] * 15)
        data["scores"][14]["number"] = 1
        with self.assertRaises(ValidationError):
            CoevaluationScoresSchema().load(data)

    def test_rejects_out_of_range_and_non_integer(self):
        for bad in (8, -1, 3.5, "3"):
            data = payload([3] * 15)
            data["scores"][0]["score"] = bad
            with self.assertRaises(ValidationError, msg=repr(bad)):
                CoevaluationScoresSchema().load(data)

    def test_rejects_missing_scores_key(self):
        with self.assertRaises(ValidationError):
            CoevaluationScoresSchema().load({})

    def test_get_level_below_minimum_falls_back_to_last_level(self):
        self.assertEqual(get_level(-1)["code"], "beginning")
