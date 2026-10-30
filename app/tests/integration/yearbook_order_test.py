# app/tests/integration/yearbook_order_test.py


import unittest
import json

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project

DIAGNOSTICS = ['diagnosticEnvironmental', 'diagnosticReading', 'diagnosticMath', 'diagnosticLogic']


class YearbookOrderTest(unittest.TestCase):
    """Orden configurable de diagnósticos y actividades en el AmbLeMario."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        seed_base()
        self.schoolYear = create_school_year()
        lapse1 = self.schoolYear.pecaSetting.lapse1
        lapse1.ambleCoins.status = "1"
        lapse1.ambleCoins.order = 2
        lapse1.mathOlympic.status = "1"
        lapse1.mathOlympic.order = 1
        self.schoolYear.save()

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    def keys(self, items):
        return [item['key'] for item in items]

    def put(self, lapse, items):
        return self.client().put('/pecasetting/yearbookorder/{}'.format(lapse),
                                 data=json.dumps({"items": items}), content_type='application/json')

    def test_default_order_diagnostics_then_menu_order(self):
        res = self.client().get('/pecasetting/yearbookorder')
        self.assertEqual(res.status_code, 200)
        lapse1 = self.json(res)['lapse1']
        self.assertEqual(self.keys(lapse1), DIAGNOSTICS + ['olympics', 'ambleCoins'])
        self.assertEqual([i['order'] for i in lapse1], [1, 2, 3, 4, 5, 6])
        self.assertFalse(any(i['isCustom'] for i in lapse1))
        self.assertEqual(self.keys(self.json(res)['lapse2']), DIAGNOSTICS)

    def test_saved_order_and_unconfigured_items_go_last(self):
        res = self.put('1', [{"key": "ambleCoins", "order": 1}, {"key": "diagnosticMath", "order": 2}])
        self.assertEqual(res.status_code, 200)
        lapse1 = self.json(res)['lapse1']
        self.assertEqual(self.keys(lapse1)[:2], ['ambleCoins', 'diagnosticMath'])
        # Lo no configurado conserva su orden relativo por defecto
        self.assertEqual(self.keys(lapse1)[2:],
                         ['diagnosticEnvironmental', 'diagnosticReading', 'diagnosticLogic', 'olympics'])
        self.assertEqual([i['isCustom'] for i in lapse1[:3]], [True, True, False])

        res = self.put('1', [])
        self.assertEqual(self.keys(self.json(res)['lapse1']), DIAGNOSTICS + ['olympics', 'ambleCoins'])

    def test_save_validations(self):
        self.assertEqual(self.put('4', []).status_code, 400)
        res = self.client().put('/pecasetting/yearbookorder/1', data=json.dumps({}),
                                content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(self.put('1', [{"key": "inexistente", "order": 1}]).status_code, 400)
        self.assertEqual(self.put('1', [{"key": "olympics", "order": 1},
                                        {"key": "olympics", "order": 2}]).status_code, 400)
        self.assertEqual(self.put('1', [{"key": "olympics", "order": -1}]).status_code, 400)
        self.assertEqual(self.put('1', [{"key": "olympics", "order": "x"}]).status_code, 400)

    def test_peca_order_uses_its_school_year_setting(self):
        state, municipality = create_location()
        project = Project(
            coordinator=create_coordinator(state, municipality),
            sponsor=create_sponsor(state, municipality),
            school=create_school(state, municipality), phase="2")
        project.save()
        project.createPeca()
        peca = PecaProject.objects(isDeleted=False).first()
        self.put('1', [{"key": "olympics", "order": 1}])

        res = self.client().get('/pecaprojects/yearbook/order/{}'.format(peca.id))
        self.assertEqual(res.status_code, 200)
        lapse1 = self.json(res)['lapse1']
        self.assertEqual(lapse1[0], 'olympics')
        self.assertEqual(set(lapse1), set(DIAGNOSTICS + ['olympics', 'ambleCoins']))

        res = self.client().get('/pecaprojects/yearbook/order/5f0000000000000000000000')
        self.assertEqual(res.status_code, 404)

    def test_requires_active_school_year(self):
        self.schoolYear.status = "2"
        self.schoolYear.save()
        self.assertEqual(self.client().get('/pecasetting/yearbookorder').status_code, 404)
        self.assertEqual(self.put('1', []).status_code, 404)


if __name__ == "__main__":
    unittest.main()
