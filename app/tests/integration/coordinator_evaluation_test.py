# -*- coding: utf-8 -*-
# app/tests/integration/coordinator_evaluation_test.py

import json
import unittest
from types import SimpleNamespace

try:
    from unittest import mock
except ImportError:  # Python 2.7
    import mock

from flask_jwt_extended import create_access_token
from mongoengine.errors import NotUniqueError

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year, role)
from app.helpers.handler_seeds import create_entities
from app.models.admin_user_model import AdminUser
from app.models.coordinator_evaluation_model import CoordinatorEvaluation
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.services.coordinator_evaluation_service import CoordinatorEvaluationService


NO_ID = '5f0000000000000000000000'


def answers_payload(options):
    return {"answers": [{"number": i + 1, "option": opt} for i, opt in enumerate(options)]}


class CoordinatorEvaluationTest(unittest.TestCase):

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

        self.peca = PecaProject(
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
            school={"name": self.school.name, "code": self.school.code, "sections": []})
        self.peca.save()

    def tearDown(self):
        drop_testing_database(self.db)

    def url(self, pecaId=None):
        return '/pecaprojects/{}/coordinator-evaluation'.format(pecaId or self.peca.id)

    def headers(self, user):
        token = create_access_token({"id": str(user.id), "email": user.email})
        return {"Authorization": "Bearer " + token}

    def post(self, data=None, pecaId=None, headers=None):
        return self.client().post(
            self.url(pecaId), data=json.dumps(data or {}),
            content_type='application/json', headers=headers or {})

    def newAdmin(self):
        admin = AdminUser(
            firstName="Test", lastName="Admin", cardType="1", cardId="90000001",
            function="Admin", email="admin@test.com", password="12345678", userType="1",
            phone="02322322323", role=role("admin"),
            addressState=self.state, addressMunicipality=self.municipality)
        admin.setHashPassword()
        admin.save()
        return admin

    def test_get_initial_state(self):
        res = self.client().get(self.url())
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "not_started")
        self.assertTrue(data["canEvaluate"])
        self.assertIsNone(data["totalScore"])
        self.assertIsNone(data["submittedAt"])
        self.assertEqual(len(data["instrument"]["questions"]), 4)
        self.assertEqual(len(data["answers"]), 4)
        self.assertIsNone(data["answers"][0]["option"])

    def test_save_once_and_reject_duplicate(self):
        res = self.post(answers_payload(["rarely", "rarely", "frequently", "never"]))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "completed")
        self.assertFalse(data["canEvaluate"])
        self.assertEqual(data["totalScore"], 66.67)
        self.assertEqual([a["score"] for a in data["answers"]], [16.67, 16.67, 8.33, 25.0])
        self.assertEqual(data["answers"][3]["optionLabel"], u"Nunca")
        self.assertIsNotNone(data["submittedAt"])

        # Segundo envío bloqueado (409)
        res = self.post(answers_payload(["never"] * 4))
        self.assertEqual(res.status_code, 409)
        self.assertEqual(CoordinatorEvaluation.objects(pecaId=str(self.peca.id)).first().totalScore, 66.67)

    def test_invalid_payload_and_not_found(self):
        self.assertEqual(self.post(answers_payload(["never"] * 3)).status_code, 400)
        self.assertEqual(self.post(answers_payload(["never", "bad", "always", "rarely"])).status_code, 400)
        self.assertEqual(self.client().get(self.url(NO_ID)).status_code, 404)
        self.assertEqual(self.client().get(self.url("bad-id")).status_code, 404)
        self.assertEqual(self.post(answers_payload(["never"] * 4), pecaId=NO_ID).status_code, 404)

    def test_access_rules(self):
        other = create_coordinator(
            self.state, self.municipality, email="otro@test.com", cardId="20000002")
        admin = self.newAdmin()

        # Coordinador asignado: puede ver y responder, pero NO ve puntajes
        res = self.client().get(self.url(), headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 200)
        coordView = json.loads(res.data)
        self.assertTrue(coordView["canEvaluate"])
        self.assertFalse(coordView["showScores"])
        self.assertIsNone(coordView["instrument"]["maxTotal"])
        self.assertNotIn("score", coordView["instrument"]["options"][0])

        # Admin: puede ver puntajes, pero NO puede responder (canEvaluate=False y POST=403)
        res = self.client().get(self.url(), headers=self.headers(admin))
        self.assertEqual(res.status_code, 200)
        adminView = json.loads(res.data)
        self.assertFalse(adminView["canEvaluate"])
        self.assertTrue(adminView["showScores"])
        self.assertEqual(adminView["instrument"]["maxTotal"], 100.0)
        self.assertEqual(adminView["instrument"]["options"][0]["score"], 25.0)

        self.assertEqual(self.post(
            answers_payload(["never"] * 4), headers=self.headers(admin)).status_code, 403)

        # Otro coordinador o escuela: sin acceso
        self.assertEqual(self.client().get(
            self.url(), headers=self.headers(other)).status_code, 403)
        self.assertEqual(self.client().get(
            self.url(), headers=self.headers(self.school)).status_code, 403)
        self.assertEqual(self.post(
            answers_payload(["never"] * 4), headers=self.headers(other)).status_code, 403)

        # Coordinador asignado guarda: respuesta oculta puntajes, pero BD los calcula
        res = self.post(
            answers_payload(["rarely", "rarely", "frequently", "never"]),
            headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 200)
        coordSaved = json.loads(res.data)
        self.assertFalse(coordSaved["showScores"])
        self.assertIsNone(coordSaved["totalScore"])
        self.assertTrue(all(a["score"] is None for a in coordSaved["answers"]))

        saved = CoordinatorEvaluation.objects(pecaId=str(self.peca.id)).first()
        self.assertEqual(saved.submittedBy, str(self.coordinator.id))
        self.assertEqual(saved.totalScore, 66.67)

        # Admin consulta ya completada: ve puntajes completos
        adminCompleted = json.loads(
            self.client().get(self.url(), headers=self.headers(admin)).data)
        self.assertTrue(adminCompleted["showScores"])
        self.assertFalse(adminCompleted["canEvaluate"])
        self.assertEqual(adminCompleted["totalScore"], 66.67)
        self.assertEqual([a["score"] for a in adminCompleted["answers"]], [16.67, 16.67, 8.33, 25.0])

    def test_coordinator_without_permission_is_denied(self):
        coordinatorRole = role("coordinator")
        for permission in coordinatorRole.permissions:
            for action in permission.actions:
                if action.name == "teacher_coevaluation":
                    action.allowed = False
        coordinatorRole.save()
        res = self.client().get(self.url(), headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 403)

    def test_check_access_without_role_and_parallel_save_race(self):
        service = CoordinatorEvaluationService()
        _, status = service.check_access(SimpleNamespace(role=None), self.peca)
        self.assertEqual(status, 403)
        self.assertIsNone(service.check_access(None, self.peca))

        with mock.patch.object(CoordinatorEvaluation, 'save', side_effect=NotUniqueError()):
            res = self.post(answers_payload(["never"] * 4))
        self.assertEqual(res.status_code, 409)

    def test_clean_clears_results_when_answers_empty(self):
        ev = CoordinatorEvaluation(
            pecaId=str(self.peca.id), schoolYearId=str(self.schoolYear.id),
            schoolId=str(self.school.id), answers=[])
        ev.clean()
        self.assertEqual(ev.scores, [])
        self.assertIsNone(ev.totalScore)
