import unittest
from unittest.mock import MagicMock, patch

class EnvironmentalDiagnosticServiceUnitTest(unittest.TestCase):

    @patch('app.services.environmental_diagnostic_service.EnvironmentalDiagnosticEvaluator')
    def test_submit_evaluation_calculations(self, mock_evaluator_cls):
        mock_evaluator = MagicMock()
        mock_evaluator.hasEvaluated = False
        mock_evaluator_cls.objects.return_value.first.return_value = mock_evaluator

        from app.services.environmental_diagnostic_service import EnvironmentalDiagnosticService
        service = EnvironmentalDiagnosticService()

        payload = {
            "results": {
                "cleanlinessAndCareOfSpaces": {
                    "subcriteria": {
                        "1.1": {"value": 7, "observation": "Excelente"},
                        "1.2": {"value": 6, "observation": ""},
                        "1.3": {"value": 5, "observation": ""}
                    }
                },
                "wasteManagement": {
                    "subcriteria": {
                        "2.1": {"value": 6, "observation": ""},
                        "2.2": {"value": 6, "observation": ""},
                        "2.3": {"value": 6, "observation": ""}
                    }
                },
                "biodiversityConservation": {
                    "subcriteria": {
                        "3.1": {"value": 4, "observation": ""},
                        "3.2": {"value": 5, "observation": ""},
                        "3.3": {"value": 6, "observation": ""}
                    }
                },
                "waterUse": {
                    "subcriteria": {
                        "4.1": {"value": 7, "observation": ""},
                        "4.2": {"value": 7, "observation": ""},
                        "4.3": {"value": 7, "observation": ""}
                    }
                },
                "communityRelations": {
                    "subcriteria": {
                        "5.1": {"value": 5, "observation": ""},
                        "5.2": {"value": 5, "observation": ""}
                    }
                }
            }
        }

        res, code = service.submit_evaluation("dummy_token", payload)
        self.assertEqual(code, 200)
        self.assertTrue(mock_evaluator.hasEvaluated)

        # Verify indicator 1 average: (7+6+5)/3 = 6.0
        self.assertEqual(mock_evaluator.results['cleanlinessAndCareOfSpaces']['average'], 6.0)
        self.assertEqual(mock_evaluator.results['cleanlinessAndCareOfSpaces']['subtotal'], 18.0)

        # Verify indicator 2 average: (6+6+6)/3 = 6.0
        self.assertEqual(mock_evaluator.results['wasteManagement']['average'], 6.0)

        # Verify indicator 3 average: (4+5+6)/3 = 5.0
        self.assertEqual(mock_evaluator.results['biodiversityConservation']['average'], 5.0)

        # Verify indicator 4 average: (7+7+7)/3 = 7.0
        self.assertEqual(mock_evaluator.results['waterUse']['average'], 7.0)

        # Verify indicator 5 average: (5+5)/2 = 5.0
        self.assertEqual(mock_evaluator.results['communityRelations']['average'], 5.0)

        # Verify Total Index: 6.0 + 6.0 + 5.0 + 7.0 + 5.0 = 29.0 (Satisfactorio)
        self.assertEqual(mock_evaluator.index, 29.0)

    @patch('app.services.environmental_diagnostic_service.EnvironmentalDiagnosticEvaluator')
    def test_submit_evaluation_with_zero_no_aplica(self, mock_evaluator_cls):
        mock_evaluator = MagicMock()
        mock_evaluator.hasEvaluated = False
        mock_evaluator_cls.objects.return_value.first.return_value = mock_evaluator

        from app.services.environmental_diagnostic_service import EnvironmentalDiagnosticService
        service = EnvironmentalDiagnosticService()

        payload = {
            "results": {
                "cleanlinessAndCareOfSpaces": {
                    "subcriteria": {
                        "1.1": {"value": 7, "observation": ""},
                        "1.2": {"value": 5, "observation": ""},
                        "1.3": {"value": 0, "observation": "No aplica papelera"}
                    }
                },
                "wasteManagement": {"subcriteria": {"2.1": {"value": 6}, "2.2": {"value": 6}, "2.3": {"value": 6}}},
                "biodiversityConservation": {"subcriteria": {"3.1": {"value": 5}, "3.2": {"value": 5}, "3.3": {"value": 5}}},
                "waterUse": {"subcriteria": {"4.1": {"value": 7}, "4.2": {"value": 7}, "4.3": {"value": 0}}},
                "communityRelations": {"subcriteria": {"5.1": {"value": 6}, "5.2": {"value": 6}}}
            }
        }

        res, code = service.submit_evaluation("dummy_token", payload)
        self.assertEqual(code, 200)

        # Indicator 1: 1.1=7, 1.2=5, 1.3=0. Subtotal=12. Applied count=2. Average = 12/2 = 6.0
        self.assertEqual(mock_evaluator.results['cleanlinessAndCareOfSpaces']['subtotal'], 12.0)
        self.assertEqual(mock_evaluator.results['cleanlinessAndCareOfSpaces']['average'], 6.0)
        self.assertFalse(mock_evaluator.results['cleanlinessAndCareOfSpaces']['subcriteria']['1.3']['applies'])

        # Indicator 4: 4.1=7, 4.2=7, 4.3=0. Subtotal=14. Applied count=2. Average = 14/2 = 7.0
        self.assertEqual(mock_evaluator.results['waterUse']['average'], 7.0)

if __name__ == '__main__':
    unittest.main()
