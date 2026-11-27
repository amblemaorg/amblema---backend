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
from app.models.coordinator_evaluation_model import CoordinatorEvaluation
from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.state_model import State
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

    def newPeca(self, lapse3=None, deleted=False, yearbookDownloadEnabled=True,
                addressState=None, sections=None):
        peca = PecaProject(
            yearbookDownloadEnabled=yearbookDownloadEnabled,
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
                "sections": sections or [],
                "addressState": addressState,
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
        scores = score if isinstance(score, list) else [score] * 15
        coevaluation = TeacherCoevaluation(
            pecaId=str(peca.id), schoolYearId=str(self.schoolYear.id),
            schoolId=str(self.school.id), teacherId=teacherId,
            teacherScores=scores, coordinatorScores=scores,
            teacherSubmittedAt=datetime.utcnow(),
            coordinatorSubmittedAt=datetime.utcnow() if complete else None)
        coevaluation.save()
        return coevaluation

    def addCoordinatorEvaluation(self, peca, options=None):
        evaluation = CoordinatorEvaluation(
            pecaId=str(peca.id), schoolYearId=str(self.schoolYear.id),
            schoolId=str(self.school.id),
            answers=options or ["never", "never", "never", "never"],
            submittedAt=datetime.utcnow())
        evaluation.save()
        return evaluation

    def get(self, schoolId=None, stateId=None):
        url = '/statistics/hqsawardsreport/{}'.format(self.schoolYear.id)
        if schoolId:
            url += '?schoolId={}'.format(schoolId)
        if stateId:
            url += '{}stateId={}'.format('&' if schoolId else '?', stateId)
        res = self.client().get(url)
        return res.status_code, json.loads(res.data)

    # ------------------------------------------------------------- pruebas

    def test_report_caps_and_awards_gold(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 130.0, "multiplicationsPerMinIndex": 90.0,
                                    "operationsPerMinIndex": 80.0})
        self.addEvaluator(peca, 35)                        # IAA 100 %
        self.addCoevaluation(peca, "t1", 7)                # 100 %
        self.addCoevaluation(peca, "t2", [6] * 9 + [5] * 6)  # 80 % -> promedio 90 %
        self.addCoordinatorEvaluation(peca, ["never"] * 4)  # 100 %
        status, data = self.get()
        self.assertEqual(status, 200)
        s = data["schools"][0]
        self.assertEqual(s["components"], {"iaa": 100.0, "wordsPerMin": 100.0,
                                           "multiplicationsPerMin": 90.0, "operationsPerMin": 80.0})
        self.assertEqual(s["integralIndex"], 92.5)
        self.assertEqual(s["teacherIndex"], 90.0)
        self.assertEqual(s["coordinatorIndex"], 100.0)
        self.assertEqual(s["nCompletedCoevaluations"], 2)
        # 92.5 * 0.4 + 90.0 * 0.4 + 100.0 * 0.2 = 37 + 36 + 20 = 93.0
        self.assertEqual(s["finalIndex"], 93.0)
        self.assertEqual(s["status"], "awarded")
        self.assertEqual(s["award"], "gold")
        self.assertEqual(s["awardLabel"], u"Escuela HQS – Nivel ORO")
        self.assertEqual(data["counts"]["gold"], 1)

    def test_grade_adjustment_under_40_from_sections(self):
        sections = [
            {"grade": "1", "name": "A", "diagnostics": {"lapse3": {
                "wordsPerMinIndex": 20.0, "wordsPerMinCount": 10,
                "multiplicationsPerMinIndex": 80.0, "multiplicationsPerMinCount": 10,
                "operationsPerMinIndex": 80.0, "operationsPerMinCount": 10,
            }}},
            {"grade": "2", "name": "A", "diagnostics": {"lapse3": {
                "wordsPerMinIndex": 80.0, "wordsPerMinCount": 10,
                "multiplicationsPerMinIndex": 80.0, "multiplicationsPerMinCount": 10,
                "operationsPerMinIndex": 80.0, "operationsPerMinCount": 10,
            }}},
        ]
        peca = self.newPeca(sections=sections)
        self.addEvaluator(peca, 35)  # IAA 100
        self.addCoevaluation(peca, "t1", [6] * 9 + [5] * 6)  # 80 %
        self.addCoordinatorEvaluation(peca, ["rarely", "rarely", "frequently", "never"])  # 66.67 %
        s = self.get()[1]["schools"][0]
        # PPM: (20*10*0.5 + 80*10*1) / (10*0.5 + 10*1) = 900 / 15 = 60.0 (sin ajuste sería 50.0)
        self.assertEqual(s["components"]["wordsPerMin"], 60.0)
        self.assertEqual(s["integralIndex"], 80.0)  # (100+60+80+80)/4
        # 80*0.4 + 80*0.4 + 66.67*0.2 = 32 + 32 + 13.334 = 77.33 -> PLATA
        self.assertEqual(s["finalIndex"], 77.33)
        self.assertEqual(s["award"], "silver")

    def test_iaa_uses_only_valid_lapse3_evaluators(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 50.0, "multiplicationsPerMinIndex": 50.0,
                                    "operationsPerMinIndex": 50.0})
        self.addEvaluator(peca, 21)                   # válido
        self.addEvaluator(peca, 7)                    # válido -> promedio 14 -> 40 %
        self.addEvaluator(peca, 35, lapse="2")        # otro lapso
        self.addEvaluator(peca, 35, evaluated=False)  # sin evaluar
        self.addEvaluator(peca, 35, deleted=True)     # borrado
        self.addEvaluator(peca, None)                 # sin índice
        self.addCoevaluation(peca, "t1", [3] * 12 + [2] * 3)   # 40 %
        self.addCoordinatorEvaluation(peca, ["rarely", "rarely", "rarely", "always"])  # 50 %
        s = self.get()[1]["schools"][0]
        self.assertEqual(s["iaaRaw"], 14.0)
        self.assertEqual(s["components"]["iaa"], 40.0)
        # integral 47.5*0.4 + docentes 40*0.4 + coord 50*0.2 = 19 + 16 + 10 = 45.0
        self.assertEqual(s["finalIndex"], 45.0)
        self.assertEqual(s["award"], "bronze")

    def test_missing_yearbook_blocks_award(self):
        peca = self.newPeca(
            lapse3={"wordsPerMinIndex": 100.0, "multiplicationsPerMinIndex": 100.0,
                    "operationsPerMinIndex": 100.0},
            yearbookDownloadEnabled=False)
        self.addEvaluator(peca, 35)
        self.addCoevaluation(peca, "t1", 7)
        self.addCoordinatorEvaluation(peca, ["never"] * 4)
        s = self.get()[1]["schools"][0]
        self.assertEqual(s["finalIndex"], 100.0)
        self.assertEqual(s["status"], "incomplete")
        self.assertEqual(s["missing"], ["yearbook"])
        self.assertEqual(s["missingLabels"], [u"AmbLeMario"])
        self.assertIsNone(s["award"])

    def test_missing_coordinator_evaluation_is_incomplete(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 90.0, "multiplicationsPerMinIndex": 90.0,
                                    "operationsPerMinIndex": 90.0})
        self.addEvaluator(peca, 35)
        self.addCoevaluation(peca, "t1", 7)
        s = self.get()[1]["schools"][0]
        self.assertIsNone(s["coordinatorIndex"])
        self.assertIsNone(s["finalIndex"])
        self.assertEqual(s["missing"], ["coordinatorIndex"])
        self.assertEqual(s["missingLabels"], [u"Valoración Coord."])
        self.assertEqual(s["status"], "incomplete")

    def test_missing_lapse3_is_incomplete(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 90.0})
        self.addEvaluator(peca, 30)
        self.addCoevaluation(peca, "t1", 7)
        self.addCoordinatorEvaluation(peca)
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
        self.addCoevaluation(peca, "t1", 7, complete=False)
        self.addCoordinatorEvaluation(peca)
        s = self.get()[1]["schools"][0]
        self.assertIsNone(s["teacherIndex"])
        self.assertEqual(s["nCompletedCoevaluations"], 0)
        self.assertEqual(s["missing"], ["teacherIndex"])
        self.assertEqual(s["status"], "incomplete")

    def test_low_score_has_no_award(self):
        peca = self.newPeca(lapse3={"wordsPerMinIndex": 20.0, "multiplicationsPerMinIndex": 20.0,
                                    "operationsPerMinIndex": 20.0})
        self.addEvaluator(peca, 7)                           # 20 %
        self.addCoevaluation(peca, "t1", [2] * 6 + [1] * 9)  # 20 %
        self.addCoordinatorEvaluation(peca, ["always"] * 4)  # 0 %
        s = self.get()[1]["schools"][0]
        # 20*0.4 + 20*0.4 + 0*0.2 = 16.0
        self.assertEqual(s["finalIndex"], 16.0)
        self.assertEqual(s["status"], "none")
        self.assertEqual(s["awardLabel"], u"Sin premio")
        self.assertIs(s["yearbookDownloadEnabled"], True)

    def test_row_reports_yearbook_download_flag(self):
        self.newPeca(yearbookDownloadEnabled=False)
        s = self.get()[1]["schools"][0]
        self.assertIs(s["yearbookDownloadEnabled"], False)

    def test_errors_deleted_peca_and_school_filter(self):
        self.newPeca(deleted=True)
        self.assertEqual(self.get()[1]["schools"], [])
        self.assertEqual(self.client().get('/statistics/hqsawardsreport/abc').status_code, 404)
        self.assertEqual(self.client().get(
            '/statistics/hqsawardsreport/{}'.format("0" * 24)).status_code, 404)
        self.newPeca()
        self.assertEqual(len(self.get(schoolId=str(self.school.id))[1]["schools"]), 1)
        self.assertEqual(self.get(schoolId="0" * 24)[1]["schools"], [])

    def test_state_field_and_state_filter(self):
        self.newPeca(addressState=self.state)
        other = State(name="Zulia")
        other.save()

        s = self.get()[1]["schools"][0]
        self.assertEqual(s["state"], {"id": str(self.state.id), "name": "Lara"})

        status, data = self.get(stateId=str(self.state.id))
        self.assertEqual(status, 200)
        self.assertEqual(len(data["schools"]), 1)
        self.assertEqual(self.get(stateId=str(other.id))[1]["schools"], [])
        # El filtro de estado se combina con el de escuela.
        self.assertEqual(len(self.get(schoolId=str(self.school.id),
                                      stateId=str(self.state.id))[1]["schools"]), 1)

        status, data = self.get(stateId="abc")
        self.assertEqual(status, 404)
        self.assertEqual(data["message"], "State not found")

    def test_peca_without_state_has_null_state(self):
        self.assertIsNone(self.get()[1]["schools"][0]["state"] if self.newPeca() else None)


if __name__ == '__main__':
    unittest.main()
