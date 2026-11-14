# -*- coding: utf-8 -*-
# app/tests/integration/hqs_award_report_test.py

import json
import unittest
from datetime import datetime
from uuid import uuid4

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.helpers.handler_seeds import create_entities
from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.teacher_coevaluation_model import TeacherCoevaluation


class HqsAwardReportTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        create_entities()
        seed_base()
        self.state, self.municipality = create_location()
        self.schoolYear = create_school_year()
        self.coordinator = create_coordinator(self.state, self.municipality)
        self.sponsor = create_sponsor(self.state, self.municipality)
        self.school = create_school(self.state, self.municipality)

        self.project = Project(
            coordinator=self.coordinator, sponsor=self.sponsor, school=self.school)
        self.project.save()

    def tearDown(self):
        drop_testing_database(self.db)

    # ------------------------------------------------------------- helpers

    def newPeca(self, lapse3=None, deleted=False):
        peca = PecaProject(
            schoolYear=self.schoolYear,
            schoolYearName=self.schoolYear.name,
            project={
                "id": str(self.project.id),
                "code": str(self.project.code),
                "coordinator": {"id": str(self.coordinator.id), "name": u"Ana Pérez"},
                "sponsor": {"id": str(self.sponsor.id), "name": self.sponsor.name},
                "school": {"id": str(self.school.id), "name": self.school.name,
                           "code": self.school.code},
            },
            school={
                "name": self.school.name,
                "code": self.school.code,
                "diagnostics": {"lapse3": lapse3 or {}},
            },
            isDeleted=deleted)
        peca.save()
        return peca

    def addEvaluator(self, peca, index, lapse="3", evaluated=True, deleted=False):
        evaluator = EnvironmentalDiagnosticEvaluator(
            pecaId=str(peca.id), lapse=lapse, name="Eval", email="eval@test.com",
            phone="04140000000", token=uuid4().hex, hasEvaluated=evaluated,
            index=index, isDeleted=deleted)
        evaluator.save()
        return evaluator

    def addCoevaluation(self, peca, teacherId, score, complete=True):
        coevaluation = TeacherCoevaluation(
            pecaId=str(peca.id), schoolYearId=str(self.schoolYear.id),
            schoolId=str(self.school.id), teacherId=teacherId,
            teacherScores=[score] * 15, coordinatorScores=[score] * 15,
            teacherSubmittedAt=datetime.utcnow(),
            coordinatorSubmittedAt=datetime.utcnow() if complete else None)
        coevaluation.save()
        return coevaluation

    def get(self, schoolId=None):
        url = '/statistics/hqsawardsreport/{}'.format(self.schoolYear.id)
        if schoolId:
            url += '?schoolId={}'.format(schoolId)
        res = self.client().get(url)
        return res.status_code, json.loads(res.data)

    # ------------------------------------------------------------- pruebas

    def test_report_caps_and_awards_gold(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 130.0, "multiplicationsPerMinIndex": 90.0,
                                    "operationsPerMinIndex": 80.0})
        self.addEvaluator(peca, 35)          # IAA 100 %
        self.addCoevaluation(peca, "t1", 5)  # 100 %
        self.addCoevaluation(peca, "t2", 4)  # 80 %
        status, data = self.get()
        self.assertEqual(status, 200)
        s = data["schools"][0]
        self.assertEqual(s["components"], {"iaa": 100.0, "wordsPerMin": 100.0,
                                           "multiplicationsPerMin": 90.0, "operationsPerMin": 80.0})
        self.assertEqual(s["integralIndex"], 92.5)
        self.assertEqual(s["teacherIndex"], 90.0)
        self.assertEqual(s["nCompletedCoevaluations"], 2)
        self.assertEqual(s["finalIndex"], 91.25)
        self.assertEqual(s["status"], "awarded")
        self.assertEqual(s["award"], "gold")
        self.assertEqual(s["awardLabel"], u"Escuela HQS – Nivel ORO")
        self.assertEqual(data["counts"]["gold"], 1)

    def test_iaa_uses_only_valid_lapse3_evaluators(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 50.0, "multiplicationsPerMinIndex": 50.0,
                                    "operationsPerMinIndex": 50.0})
        self.addEvaluator(peca, 21)                   # válido
        self.addEvaluator(peca, 7)                    # válido -> promedio 14 -> 40 %
        self.addEvaluator(peca, 35, lapse="2")        # otro lapso
        self.addEvaluator(peca, 35, evaluated=False)  # sin evaluar
        self.addEvaluator(peca, 35, deleted=True)     # borrado
        self.addEvaluator(peca, None)                 # sin índice
        self.addCoevaluation(peca, "t1", 2)           # 40 %
        s = self.get()[1]["schools"][0]
        self.assertEqual(s["iaaRaw"], 14.0)
        self.assertEqual(s["components"]["iaa"], 40.0)
        self.assertEqual(s["finalIndex"], 43.75)  # integral (40+50+50+50)/4 = 47.5; docentes 40
        self.assertEqual(s["award"], "bronze")

    def test_missing_lapse3_is_incomplete(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 90.0})
        self.addEvaluator(peca, 30)
        self.addCoevaluation(peca, "t1", 5)
        s = self.get()[1]["schools"][0]
        self.assertIsNone(s["integralIndex"])
        self.assertIsNone(s["finalIndex"])
        self.assertEqual(s["missing"], ["multiplicationsPerMin", "operationsPerMin"])
        self.assertEqual(s["missingLabels"], [u"M2M", u"60LM"])
        self.assertEqual(s["status"], "incomplete")
        self.assertIsNone(s["award"])
        self.assertEqual(s["awardLabel"], u"Datos incompletos")

    def test_no_completed_coevaluation_is_incomplete(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 90.0, "multiplicationsPerMinIndex": 90.0,
                                    "operationsPerMinIndex": 90.0})
        self.addEvaluator(peca, 35)
        self.addCoevaluation(peca, "t1", 5, complete=False)
        s = self.get()[1]["schools"][0]
        self.assertIsNone(s["teacherIndex"])
        self.assertEqual(s["nCompletedCoevaluations"], 0)
        self.assertEqual(s["missing"], ["teacherIndex"])
        self.assertEqual(s["status"], "incomplete")

    def test_low_score_has_no_award(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 20.0, "multiplicationsPerMinIndex": 20.0,
                                    "operationsPerMinIndex": 20.0})
        self.addEvaluator(peca, 7)           # 20 %
        self.addCoevaluation(peca, "t1", 1)  # 20 %
        s = self.get()[1]["schools"][0]
        self.assertEqual(s["finalIndex"], 20.0)
        self.assertEqual(s["status"], "none")
        self.assertEqual(s["awardLabel"], u"Sin premio")

    def test_errors_deleted_peca_and_school_filter(self):
        self.newPeca(deleted=True)
        self.assertEqual(self.get()[1]["schools"], [])
        self.assertEqual(self.client().get('/statistics/hqsawardsreport/abc').status_code, 404)
        self.assertEqual(self.client().get(
            '/statistics/hqsawardsreport/{}'.format("0" * 24)).status_code, 404)
        self.newPeca()
        self.assertEqual(len(self.get(schoolId=str(self.school.id))[1]["schools"]), 1)
        self.assertEqual(self.get(schoolId="0" * 24)[1]["schools"], [])


if __name__ == '__main__':
    unittest.main()
