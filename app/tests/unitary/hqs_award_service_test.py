# -*- coding: utf-8 -*-
# app/tests/unitary/hqs_award_service_test.py

import unittest

from app.services.hqs_award_service import sort_schools, count_schools


def _rows():
    return [
        {"name": "b", "finalIndex": 91.25, "award": "gold", "status": "awarded"},
        {"name": "C", "finalIndex": None, "award": None, "status": "incomplete"},
        {"name": "d", "finalIndex": 20.0, "award": None, "status": "none"},
        {"name": "A", "finalIndex": 91.25, "award": "gold", "status": "awarded"},
        {"name": "e", "finalIndex": 65.0, "award": "silver", "status": "awarded"},
        {"name": "a2", "finalIndex": None, "award": None, "status": "incomplete"},
    ]


class HqsAwardServiceTest(unittest.TestCase):

    def test_sort_schools(self):
        result = sort_schools(_rows())
        self.assertEqual(
            [s["name"] for s in result], ["A", "b", "e", "d", "a2", "C"])

    def test_count_schools(self):
        self.assertEqual(
            count_schools(_rows()),
            {"gold": 2, "silver": 1, "bronze": 0, "none": 1, "incomplete": 2})


if __name__ == "__main__":
    unittest.main()
