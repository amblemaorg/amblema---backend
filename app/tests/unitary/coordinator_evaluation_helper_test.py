# -*- coding: utf-8 -*-
# app/tests/unitary/coordinator_evaluation_helper_test.py

import unittest

from marshmallow import ValidationError

from app.helpers.coordinator_evaluation_helper import (
    N_QUESTIONS, MAX_QUESTION_SCORE, MAX_TOTAL, OPTIONS, QUESTIONS,
    get_coordinator_instrument, option_raw_score, get_option_label,
    compute_coordinator_results)
from app.schemas.coordinator_evaluation_schema import (
    CoordinatorAnswersSchema, answers_to_list)


def payload(options):
    return {"answers": [{"number": i + 1, "option": opt} for i, opt in enumerate(options)]}


class CoordinatorEvaluationHelperTest(unittest.TestCase):

    def test_instrument_has_4_questions_and_4_options(self):
        self.assertEqual(N_QUESTIONS, 4)
        self.assertEqual(MAX_QUESTION_SCORE, 25.0)
        self.assertEqual(MAX_TOTAL, 100.0)
        self.assertEqual([q["number"] for q in QUESTIONS], [1, 2, 3, 4])
        self.assertEqual([o["code"] for o in OPTIONS], ["never", "rarely", "frequently", "always"])
        instrument = get_coordinator_instrument()
        self.assertEqual(len(instrument["questions"]), 4)
        self.assertEqual(len(instrument["options"]), 4)
        self.assertEqual(instrument["maxTotal"], 100.0)

    def test_option_scores_and_labels(self):
        self.assertEqual(option_raw_score("never"), 25.0)
        self.assertAlmostEqual(option_raw_score("rarely"), 25.0 * 2 / 3)
        self.assertAlmostEqual(option_raw_score("frequently"), 25.0 * 1 / 3)
        self.assertEqual(option_raw_score("always"), 0.0)
        self.assertIsNone(option_raw_score("unknown"))
        self.assertEqual(get_option_label("never"), u"Nunca")
        self.assertIsNone(get_option_label("unknown"))

    def test_compute_results_matches_excel_example(self):
        # Excel Juan Jacinto Lara II: Pocas veces, Pocas veces, Con frecuencia, Nunca -> 66.67
        results = compute_coordinator_results(["rarely", "rarely", "frequently", "never"])
        self.assertEqual(results["scores"], [16.67, 16.67, 8.33, 25.0])
        self.assertEqual(results["totalScore"], 66.67)

    def test_compute_results_avoids_rounding_drift(self):
        # 3 * (25 * 2/3) + 0 = 50.0 exacto (no 50.01)
        results = compute_coordinator_results(["rarely", "rarely", "rarely", "always"])
        self.assertEqual(results["totalScore"], 50.0)
        # Extremos
        self.assertEqual(compute_coordinator_results(["never"] * 4)["totalScore"], 100.0)
        self.assertEqual(compute_coordinator_results(["always"] * 4)["totalScore"], 0.0)

    def test_compute_results_invalid_returns_none(self):
        self.assertIsNone(compute_coordinator_results(None))
        self.assertIsNone(compute_coordinator_results([]))
        self.assertIsNone(compute_coordinator_results(["never"] * 3))
        self.assertIsNone(compute_coordinator_results(["never", "bad", "never", "never"]))


class CoordinatorAnswersSchemaTest(unittest.TestCase):

    def test_valid_payload_is_ordered(self):
        expected = ["never", "rarely", "frequently", "always"]
        data = payload(expected)
        data["answers"].reverse()
        loaded = CoordinatorAnswersSchema().load(data)
        self.assertEqual(answers_to_list(loaded), expected)

    def test_rejects_missing_or_duplicated_questions(self):
        with self.assertRaises(ValidationError):
            CoordinatorAnswersSchema().load(payload(["never"] * 3))
        dup = payload(["never"] * 4)
        dup["answers"][3]["number"] = 1
        with self.assertRaises(ValidationError):
            CoordinatorAnswersSchema().load(dup)

    def test_rejects_invalid_option_or_missing_key(self):
        bad = payload(["never", "invalid", "always", "rarely"])
        with self.assertRaises(ValidationError):
            CoordinatorAnswersSchema().load(bad)
        with self.assertRaises(ValidationError):
            CoordinatorAnswersSchema().load({})
