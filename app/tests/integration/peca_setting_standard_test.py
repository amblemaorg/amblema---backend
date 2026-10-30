# app/tests/integration/peca_setting_standard_test.py


import unittest
import json

from app import create_app
from app.tests.base import drop_testing_database
from app.models.school_year_model import SchoolYear
from app.tests.fixtures import create_school_year


class PecaSettingStandardTest(unittest.TestCase):
    """Configuración de actividades estándar tal como la envía el backoffice."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        self.schoolYear = create_school_year()

    def tearDown(self):
        drop_testing_database(self.db)

    def test_first_setting_has_independent_lapses(self):
        schoolYear = SchoolYear(name="x")
        schoolYear.initFirstPecaSetting()
        schoolYear.pecaSetting.lapse1.mathOlympic.status = "1"
        self.assertEqual(schoolYear.pecaSetting.lapse2.mathOlympic.status, "2")
        self.assertIsNot(schoolYear.pecaSetting.lapse1, schoolYear.pecaSetting.lapse3)

    def test_lapse_planning_content_without_status_keeps_current(self):
        # El formulario de contenido (activity-form) no envía status ni devName
        self.schoolYear.pecaSetting.lapse2.lapsePlanning.status = "1"
        self.schoolYear.pecaSetting.lapse2.lapsePlanning.devName = "lapsePlanning"
        self.schoolYear.save()
        res = self.client().put(
            '/pecasetting/activities/lapseplanning/2',
            data={"proposalFundationDescription": "Propuesta", "meetingDescription": "Reunión"},
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        self.schoolYear.reload()
        lapsePlanning = self.schoolYear.pecaSetting.lapse2.lapsePlanning
        self.assertEqual(lapsePlanning.proposalFundationDescription, "Propuesta")
        self.assertEqual((lapsePlanning.status, lapsePlanning.devName), ("1", "lapsePlanning"))
        self.assertIsNone(self.schoolYear.pecaSetting.lapse1.lapsePlanning.proposalFundationDescription)

    def test_initial_workshop_content_without_status_keeps_current(self):
        res = self.client().put(
            '/pecasetting/activities/initialWorkshop/1',
            data={"description": "Taller", "agreementDescription": "Acuerdo",
                  "planningMeetingDescription": "Planificación", "teachersMeetingDescription": "Docentes"},
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        self.schoolYear.reload()
        initialWorkshop = self.schoolYear.pecaSetting.lapse1.initialWorkshop
        self.assertEqual(initialWorkshop.description, "Taller")
        self.assertEqual(initialWorkshop.status, "2")


if __name__ == "__main__":
    unittest.main()
