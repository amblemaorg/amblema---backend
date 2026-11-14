# -*- coding: utf-8 -*-
# app/tests/unitary/hqs_award_helper_test.py

import unittest

from app.helpers.hqs_award_helper import (
    cap_index, iaa_percentage, integral_index, final_index, get_award)


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

    def test_integral_index_complete(self):
        value, missing = integral_index({"iaa": 80.0, "wordsPerMin": 100.0,
                                         "multiplicationsPerMin": 70.0, "operationsPerMin": 50.0})
        self.assertEqual(value, 75.0)
        self.assertEqual(missing, [])

    def test_integral_index_missing(self):
        value, missing = integral_index({"iaa": None, "wordsPerMin": 100.0,
                                         "multiplicationsPerMin": None, "operationsPerMin": 50.0})
        self.assertIsNone(value)
        self.assertEqual(missing, ["iaa", "multiplicationsPerMin"])

    def test_final_index(self):
        self.assertIsNone(final_index(None, 80))
        self.assertIsNone(final_index(80, None))
        self.assertEqual(final_index(75.0, 84.0), 79.5)

    def test_award_boundaries(self):
        self.assertEqual(get_award(100)["code"], "gold")
        self.assertEqual(get_award(80.0)["code"], "gold")
        self.assertEqual(get_award(79.99)["code"], "silver")
        self.assertEqual(get_award(60.0)["code"], "silver")
        self.assertEqual(get_award(59.99)["code"], "bronze")
        self.assertEqual(get_award(40.0)["code"], "bronze")
        self.assertIsNone(get_award(39.99))
        self.assertIsNone(get_award(None))


if __name__ == "__main__":
    unittest.main()
