# -*- coding: utf-8 -*-
# app/tests/unitary/hqs_award_helper_test.py

import unittest

from app.helpers.hqs_award_helper import (
    cap_index, iaa_percentage, adjusted_area_index, sections_area_index,
    integral_index, final_index, get_award)


class HqsAwardHelperTest(unittest.TestCase):

    def test_cap_index(self):
        self.assertIsNone(cap_index(None))
        self.assertEqual(cap_index(130), 100.0)
        self.assertEqual(cap_index(83.333), 83.33)
        self.assertEqual(cap_index(-5), 0.0)

    def test_iaa_percentage(self):
        self.assertIsNone(iaa_percentage(None))
        self.assertEqual(iaa_percentage(35), 100.0)
        self.assertEqual(iaa_percentage(28), 80.0)
        self.assertEqual(iaa_percentage(14), 40.0)  # 14 * 100 / 35 en Python 2.7 no debe truncar
        self.assertEqual(iaa_percentage(25.89), 73.97)  # Excel Juan Jacinto Lara II

    def test_adjusted_area_index_matches_excel(self):
        # Lectura (PPM) del Excel Juan Jacinto Lara II -> 56.08
        reading = [
            (5.23, 17), (22.92, 24), (36.18, 32),
            (53.0, 21), (78.57, 25), (92.27, 18),
        ]
        self.assertEqual(adjusted_area_index(reading), 56.08)

        # Multiplicación (M2M) del Excel -> 51.75
        mult = [
            (42.92, 24), (18.02, 32), (53.49, 21),
            (57.2, 25), (83.89, 18),
        ]
        self.assertEqual(adjusted_area_index(mult), 51.75)

        # Lógica (60LM) del Excel (ningún grado < 40) -> 60.56
        logic = [(46.25, 32), (79.37, 21), (53.87, 25), (73.33, 18)]
        self.assertEqual(adjusted_area_index(logic), 60.56)

        # Vacío o sin participantes
        self.assertIsNone(adjusted_area_index([]))
        self.assertIsNone(adjusted_area_index([(None, 10), (50.0, 0)]))

    def test_sections_area_index_groups_by_grade_and_skips_deleted(self):
        sections = [
            # 1er grado: 2 secciones (20*10 + 40*10)/20 = 30.0 (< 40 -> peso 0.5)
            {"grade": "1", "isDeleted": False,
             "diagnostics": {"lapse3": {"wordsPerMinIndex": 20.0, "wordsPerMinCount": 10}}},
            {"grade": "1", "isDeleted": False,
             "diagnostics": {"lapse3": {"wordsPerMinIndex": 40.0, "wordsPerMinCount": 10}}},
            # 2do grado: 80.0 con 20 participantes (peso 1.0)
            {"grade": "2", "isDeleted": False,
             "diagnostics": {"lapse3": {"wordsPerMinIndex": 80.0, "wordsPerMinCount": 20}}},
            # Borrada o sin datos: ignoradas
            {"grade": "3", "isDeleted": True,
             "diagnostics": {"lapse3": {"wordsPerMinIndex": 10.0, "wordsPerMinCount": 50}}},
            {"grade": "", "isDeleted": False,
             "diagnostics": {"lapse3": {"wordsPerMinIndex": 10.0, "wordsPerMinCount": 10}}},
            {"grade": "4", "isDeleted": False,
             "diagnostics": {"lapse3": {"wordsPerMinIndex": None, "wordsPerMinCount": 0}}},
        ]
        # (30*20*0.5 + 80*20*1) / (20*0.5 + 20*1) = (300 + 1600) / 30 = 63.33
        self.assertEqual(
            sections_area_index(sections, "wordsPerMinIndex", "wordsPerMinCount"),
            63.33)
        self.assertIsNone(sections_area_index([], "wordsPerMinIndex", "wordsPerMinCount"))

    def test_integral_index_complete(self):
        # Excel Juan Jacinto Lara II: (73.97 + 56.08 + 51.75 + 60.56) / 4 = 60.59
        value, missing = integral_index({
            "iaa": 73.97, "wordsPerMin": 56.08,
            "multiplicationsPerMin": 51.75, "operationsPerMin": 60.56})
        self.assertEqual(value, 60.59)
        self.assertEqual(missing, [])

    def test_integral_index_missing(self):
        value, missing = integral_index({"iaa": None, "wordsPerMin": 100.0,
                                         "multiplicationsPerMin": None, "operationsPerMin": 50.0})
        self.assertIsNone(value)
        self.assertEqual(missing, ["iaa", "multiplicationsPerMin"])

    def test_final_index_weighted_40_40_20(self):
        self.assertIsNone(final_index(None, 80, 70))
        self.assertIsNone(final_index(80, None, 70))
        self.assertIsNone(final_index(80, 70, None))
        # Excel Juan Jacinto Lara II: 60.59*0.4 + 76.38*0.4 + 66.67*0.2 = 68.12
        self.assertEqual(final_index(60.59, 76.38, 66.67), 68.12)

    def test_award_uses_global_score_and_requires_yearbook(self):
        self.assertEqual(get_award(100.0, True)["code"], "gold")
        self.assertEqual(get_award(80.0, True)["code"], "gold")
        self.assertEqual(get_award(79.99, True)["code"], "silver")
        self.assertEqual(get_award(60.0, True)["code"], "silver")
        self.assertEqual(get_award(59.99, True)["code"], "bronze")
        self.assertEqual(get_award(40.0, True)["code"], "bronze")
        self.assertIsNone(get_award(39.99, True))
        self.assertIsNone(get_award(None, True))
        # Sin AmbLeMario (sine qua non) nunca recibe premio
        self.assertIsNone(get_award(95.0, False))
        self.assertIsNone(get_award(68.12, False))


if __name__ == "__main__":
    unittest.main()
