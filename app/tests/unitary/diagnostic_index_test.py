# app/tests/unitary/diagnostic_index_test.py

import unittest
from app.models.peca_student_model import Diagnostic
from app.models.goal_setting_model import GradeSetting


class DiagnosticIndexTest(unittest.TestCase):
    """calculateIndex no debe truncar bajo la meta (int / int en Python 2.7)."""

    def setUp(self):
        self.setting = GradeSetting(
            multiplicationsPerMin=60, operationsPerMin=40, wordsPerMin=80)

    def test_index_below_goal_keeps_decimals(self):
        diagnostic = Diagnostic(multiplicationsPerMin=50, operationsPerMin=10, wordsPerMin=60)
        diagnostic.calculateIndex(self.setting)
        self.assertAlmostEqual(float(diagnostic.multiplicationsPerMinIndex), 83.3333, places=3)
        self.assertEqual(float(diagnostic.operationsPerMinIndex), 25.0)
        self.assertEqual(float(diagnostic.wordsPerMinIndex), 75.0)

    def test_index_zero_and_empty(self):
        diagnostic = Diagnostic(multiplicationsPerMin=0, operationsPerMin=None, wordsPerMin=80)
        diagnostic.calculateIndex(self.setting)
        self.assertEqual(diagnostic.multiplicationsPerMinIndex, 0)
        self.assertIsNone(diagnostic.operationsPerMinIndex)
        self.assertEqual(float(diagnostic.wordsPerMinIndex), 100.0)


if __name__ == "__main__":
    unittest.main()
