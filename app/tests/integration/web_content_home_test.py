# app/tests/integration/web_content_home_test.py


import unittest
import json
from datetime import datetime

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.blueprints.web_content.models.web_content import WebContent
from app.models.olympics_history_model import OlympicsHistory
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.school_year_model import SchoolYear
from app.models.shared_embedded_documents import Approval
from app.models.yearbook_approval_model import YearbookApproval


class WebContentHomeTest(unittest.TestCase):
    """Home pública, historial de olimpíadas, resumen de usuarios y ficha de escuela."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        seed_base()
        WebContent._get_collection().insert_one({"homePage": {
            "slider": [], "aboutUsText": "Sobre AmbLeMa", "environmentText": "Ambiente",
            "readingText": "Lectura", "mathText": "Matemática", "testimonials": []}})

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    def home(self):
        res = self.client().get('/webcontent?page=homePage')
        self.assertEqual(res.status_code, 200)
        return self.json(res)['homePage']

    # -- Home --

    def test_home_counts_and_diagnostics(self):
        schoolYear = create_school_year()
        schoolYear.nSchools, schoolYear.nStudents, schoolYear.nTeachers = 3, 300, 30
        schoolYear.nSponsors, schoolYear.nCoordinators = 2, 1
        schoolYear.diagnostics.lapse1.wordsPerMinIndex = 85.5
        schoolYear.save()

        home = self.home()
        self.assertEqual((home['nSchools'], home['nStudents'], home['nTeachers'],
                          home['nSponsors'], home['nCoordinators']), (3, 300, 30, 2, 1))
        self.assertEqual(home['aboutUsText'], "Sobre AmbLeMa")
        series = home['diagnostics']['wordsPerMinIndex']
        self.assertEqual([(s['label'], s['serie']) for s in series],
                         [("2025 - 2026", "Lapso 1"), ("2025 - 2026", "Lapso 2"), ("2025 - 2026", "Lapso 3")])
        self.assertEqual(series[0]['value'], 85.5)
        self.assertEqual(home['diagnostics']['operationsPerMinIndex'], [])

    def test_home_without_active_school_year(self):
        home = self.home()
        self.assertEqual(home['nSchools'], 0)
        self.assertIsNone(home['currentOlympics'])

    def test_current_olympics_falls_back_to_previous_year_with_data(self):
        previous = create_school_year(name="2024 - 2025", start=datetime(2024, 9, 1),
                                      end=datetime(2025, 7, 31), status="2")
        previous.olympicsSummary.mathEnrolledCount = 10
        previous.olympicsSummary.mathParticipantRegional = 8
        previous.olympicsSummary.mathMedalsGold = 2
        previous.save()
        create_school_year()

        olympics = self.home()['currentOlympics']
        self.assertEqual(olympics['schoolYearName'], "2024 - 2025")
        self.assertEqual(olympics['mathOlympics']['participantRegional'], 8)
        self.assertEqual(olympics['mathOlympics']['goldMedal'], 2)

    def test_home_tolerates_school_year_without_olympics_summary(self):
        schoolYear = create_school_year()
        SchoolYear._get_collection().update_one({'_id': schoolYear.id}, {'$unset': {'olympicsSummary': 1}})
        olympics = self.home()['currentOlympics']
        self.assertEqual(olympics['schoolYearName'], "2025 - 2026")

    # -- Historial de olimpíadas --

    def test_olympics_history(self):
        res = self.client().get('/pecasetting/olympicshistory')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.json(res)['mathOlympics']['regionalGold'], 0)
        self.assertEqual(OlympicsHistory.objects.count(), 1)

        res = self.client().post('/pecasetting/olympicshistory', data=json.dumps(
            {"mathOlympics": {"regionalGold": 5}, "readingOlympics": {"nationalSilver": 2}}),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        history = OlympicsHistory.objects.first()
        self.assertEqual((history.mathOlympics.regionalGold, history.mathOlympics.regionalSilver,
                          history.readingOlympics.nationalSilver), (5, 0, 2))
        self.assertEqual(self.home()['olympicsHistory']['mathOlympics']['regionalGold'], 5)

        res = self.client().post('/pecasetting/olympicshistory', data=json.dumps(
            {"mathOlympics": {"regionalGold": "muchas"}}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    # -- Resumen de usuarios --

    def test_user_summary_counts_only_active(self):
        state, municipality = create_location()
        create_coordinator(state, municipality)
        sponsor = create_sponsor(state, municipality)
        sponsor.isDeleted = True
        sponsor.save()
        create_school(state, municipality)
        res = self.client().get('/statistics/usersummary')
        self.assertEqual(self.json(res), {"coordinators": 1, "sponsors": 0, "schools": 1, "teachers": 0})

    # -- Ficha pública de la escuela --

    def test_school_page_shows_activities_with_approved_images(self):
        schoolYear = create_school_year()
        schoolYear.pecaSetting.lapse1.mathOlympic.status = "1"
        schoolYear.pecaSetting.lapse1.mathOlympic.webDescription = "Olimpíada para la web"
        schoolYear.pecaSetting.lapse1.ambleCoins.status = "1"
        schoolYear.save()
        state, municipality = create_location()
        school = create_school(state, municipality, code="OD0009", name="Escuela Sol")
        school.coordinate = [-69.32, 10.06]
        school.save()
        project = Project(coordinator=create_coordinator(state, municipality),
                          sponsor=create_sponsor(state, municipality), school=school, phase="2")
        project.save()
        project.createPeca()
        peca = PecaProject.objects(isDeleted=False).first()
        YearbookApproval(pecaId=str(peca.id), approval=Approval(status="2", detail={
            "lapse1": {"activities": [
                {"id": "olympics", "images": ["a.png", "b.png"]},
                {"id": "ambleCoins", "images": []}]}})).save()

        res = self.client().get('/schoolspage/OD0009_Escuela Sol')
        self.assertEqual(res.status_code, 200)
        activities = self.json(res)['activities']
        # AmbLeMonedas no tiene imágenes aprobadas: no se muestra
        self.assertEqual([a['name'] for a in activities], ["Olimpíadas Recreativas de Matemática"])
        self.assertEqual(activities[0]['description'], "Olimpíada para la web")
        self.assertEqual(len(activities[0]['slider']), 2)

        res = self.client().get('/schoolspage/OD9999_Nada')
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
