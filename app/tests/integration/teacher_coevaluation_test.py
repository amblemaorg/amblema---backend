# -*- coding: utf-8 -*-
# app/tests/integration/teacher_coevaluation_test.py

import json
import re
import unittest
from datetime import datetime

try:
    from unittest import mock
except ImportError:  # Python 2.7
    import mock

from flask_jwt_extended import create_access_token

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year, role)
from app.helpers.handler_seeds import create_entities
from app.helpers.coevaluation_helper import hash_token
from app.helpers.utilities_helpers import add_teacher_coevaluation_permission
from app.models.admin_user_model import AdminUser
from app.models.entity_model import Entity
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.teacher_model import Teacher
from app.models.teacher_coevaluation_model import TeacherCoevaluation

SEND_EMAIL = 'app.services.teacher_coevaluation_service.send_email'


def scores_payload(value):
    values = value if isinstance(value, list) else [value] * 15
    return {"scores": [{"number": i + 1, "score": s} for i, s in enumerate(values)]}


class TeacherCoevaluationTest(unittest.TestCase):

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

        self.teacher = self.newTeacher("Luisa", "Mora", "11111111", "luisa@test.com")
        self.teacher2 = self.newTeacher("Marta", "Rivas", "22222222", "marta@test.com")
        self.inactive = self.newTeacher("Pedro", "Paz", "33333333", "pedro@test.com", status="2")
        self.noEmail = self.newTeacher("Rosa", "Luna", "44444444", "")
        self.school.teachers = [self.teacher, self.teacher2, self.inactive, self.noEmail]
        self.school.save()

        self.project = Project(
            coordinator=self.coordinator, sponsor=self.sponsor, school=self.school)
        self.project.save()
        self.peca = self.newPeca(self.schoolYear)

    def tearDown(self):
        drop_testing_database(self.db)

    # ------------------------------------------------------------- helpers

    def newTeacher(self, firstName, lastName, cardId, email, status="1"):
        return Teacher(firstName=firstName, lastName=lastName, cardType="1", cardId=cardId,
                       gender="1", email=email, phone="04141234567", status=status)

    def newPeca(self, schoolYear):
        link = {"id": str(self.teacher.id), "firstName": "Luisa", "lastName": "Mora"}
        peca = PecaProject(
            schoolYear=schoolYear,
            schoolYearName=schoolYear.name,
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
                "sections": [
                    {"grade": "4", "name": "B", "teacher": link},
                    {"grade": "3", "name": "A", "teacher": link},
                ],
            })
        peca.save()
        return peca

    def url(self, teacher=None, suffix=""):
        teacher = teacher or self.teacher
        return '/pecaprojects/coevaluations/{}/{}{}'.format(self.peca.id, teacher.id, suffix)

    def headers(self, user):
        token = create_access_token({"id": str(user.id), "email": user.email})
        return {"Authorization": "Bearer " + token}

    def post(self, url, data=None, headers=None):
        return self.client().post(url, data=json.dumps(data or {}),
                                  content_type='application/json', headers=headers or {})

    def send(self, teacher=None, result=True):
        with mock.patch(SEND_EMAIL, return_value=result) as sendMock:
            res = self.post(self.url(teacher, "/send"))
        token = None
        if sendMock.called:
            plain = sendMock.call_args[0][1]
            token = re.search(r'/coevaluacion/([0-9a-f]+)', plain).group(1)
        return res, token, sendMock

    def coevaluation(self, teacher=None):
        return TeacherCoevaluation.objects(
            pecaId=str(self.peca.id), teacherId=str((teacher or self.teacher).id)).first()

    def complete(self, teacher, teacherScores, coordinatorScores):
        res, token, _ = self.send(teacher)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.post('/coevaluations/public/' + token,
                                   scores_payload(teacherScores)).status_code, 200)
        self.assertEqual(self.post(self.url(teacher, "/coordinator"),
                                   scores_payload(coordinatorScores)).status_code, 200)

    # ------------------------------------------------------------- detalle

    def test_detail_without_coevaluation(self):
        res = self.client().get(self.url())
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "not_started")
        self.assertEqual(data["sections"], u"3er Grado A, 4to Grado B")
        self.assertEqual(data["coordinator"]["name"], u"Ana Pérez")
        self.assertEqual(len(data["instrument"]["items"]), 15)
        self.assertEqual(len(data["items"]), 15)
        self.assertTrue(data["canSendLink"])
        self.assertTrue(data["canEvaluate"])
        self.assertIsNone(data["level"])

    def test_detail_not_found(self):
        res = self.client().get('/pecaprojects/coevaluations/{}/{}'.format(
            self.peca.id, "5f0000000000000000000000"))
        self.assertEqual(res.status_code, 404)
        res = self.client().get('/pecaprojects/coevaluations/bad-id/bad-id')
        self.assertEqual(res.status_code, 404)

    # --------------------------------------------------------- coordinador

    def test_coordinator_saves_only_once(self):
        res = self.post(self.url(suffix="/coordinator"), scores_payload(4))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "pending_teacher")
        self.assertEqual([i["coordinator"] for i in data["items"]], [4] * 15)
        self.assertIsNone(data["items"][0]["teacher"])
        self.assertFalse(data["canEvaluate"])

        res = self.post(self.url(suffix="/coordinator"), scores_payload(1))
        self.assertEqual(res.status_code, 409)
        self.assertEqual(self.coevaluation().coordinatorScores, [4] * 15)

    def test_coordinator_invalid_scores(self):
        res = self.post(self.url(suffix="/coordinator"), scores_payload([3] * 14))
        self.assertEqual(res.status_code, 400)
        res = self.post(self.url(suffix="/coordinator"), scores_payload([6] + [3] * 14))
        self.assertEqual(res.status_code, 400)
        self.assertIsNone(self.coevaluation())

    def test_inactive_or_without_email_teacher(self):
        self.assertEqual(self.post(self.url(self.inactive, "/coordinator"),
                                   scores_payload(3)).status_code, 400)
        res, _, sendMock = self.send(self.inactive)
        self.assertEqual(res.status_code, 400)
        res, _, sendMock = self.send(self.noEmail)
        self.assertEqual(res.status_code, 400)
        self.assertFalse(sendMock.called)

    # ------------------------------------------------------ enlace docente

    def test_full_flow_and_public_link_hides_coordinator_scores(self):
        self.post(self.url(suffix="/coordinator"), scores_payload(4))
        res, token, sendMock = self.send()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(sendMock.call_args[0][3], "luisa@test.com")
        self.assertIn(token, sendMock.call_args[0][0])

        # Solo se guarda el hash, nunca el token
        coevaluation = self.coevaluation()
        self.assertEqual(coevaluation.tokenHash, hash_token(token))
        self.assertNotEqual(coevaluation.tokenHash, token)

        res = self.client().get('/coevaluations/public/' + token)
        self.assertEqual(res.status_code, 200)
        public = json.loads(res.data)
        self.assertEqual(public["teacher"]["firstName"], "Luisa")
        self.assertEqual(public["coordinator"]["name"], u"Ana Pérez")
        self.assertNotIn("items", public)
        self.assertNotIn("coordinatorScores", json.dumps(public))

        res = self.post('/coevaluations/public/' + token, scores_payload(3))
        self.assertEqual(res.status_code, 200)

        coevaluation = self.coevaluation()
        self.assertEqual(coevaluation.status, "completed")
        self.assertIsNone(coevaluation.tokenHash)
        self.assertEqual(coevaluation.averages, [3.5] * 15)
        self.assertEqual(coevaluation.totalScore, 52.5)
        self.assertEqual(coevaluation.percentage, 70.0)
        self.assertEqual(coevaluation.level, "commitment")

        # Token de un solo uso
        self.assertEqual(self.client().get('/coevaluations/public/' + token).status_code, 404)
        self.assertEqual(self.post('/coevaluations/public/' + token,
                                   scores_payload(5)).status_code, 404)
        self.assertEqual(self.coevaluation().teacherScores, [3] * 15)

        detail = json.loads(self.client().get(self.url()).data)
        self.assertEqual(detail["levelLabel"], u"Docente HQS con Compromiso")
        self.assertEqual(detail["items"][0], {"number": 1, "teacher": 3,
                                              "coordinator": 4, "average": 3.5})
        self.assertFalse(detail["canSendLink"])

        # No se puede reenviar después de que el docente guardó
        res, _, sendMock = self.send()
        self.assertEqual(res.status_code, 409)
        self.assertFalse(sendMock.called)

    def test_teacher_first_then_coordinator(self):
        res, token, _ = self.send()
        self.post('/coevaluations/public/' + token, scores_payload(5))
        self.assertEqual(self.coevaluation().status, "pending_coordinator")
        res = self.post(self.url(suffix="/coordinator"), scores_payload(5))
        data = json.loads(res.data)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["totalScore"], 75)
        self.assertEqual(data["level"], "excellence")

    def test_resend_generates_new_token_and_invalidates_previous(self):
        _, first, _ = self.send()
        _, second, _ = self.send()
        self.assertNotEqual(first, second)
        self.assertEqual(self.client().get('/coevaluations/public/' + first).status_code, 404)
        self.assertEqual(self.client().get('/coevaluations/public/' + second).status_code, 200)
        self.assertEqual(self.coevaluation().emailSentCount, 2)

    def test_resend_uses_current_teacher_email(self):
        self.send()
        self.school.teachers.filter(id=self.teacher.id).first().email = "nuevo@test.com"
        self.school.save()
        _, _, sendMock = self.send()
        self.assertEqual(sendMock.call_args[0][3], "nuevo@test.com")
        self.assertEqual(self.coevaluation().emailSentTo, "nuevo@test.com")

    def test_failed_email_keeps_previous_link(self):
        _, first, _ = self.send()
        res, _, _ = self.send(result=({"status": "0"}, 500))
        self.assertEqual(res.status_code, 502)
        self.assertEqual(self.client().get('/coevaluations/public/' + first).status_code, 200)
        self.assertEqual(self.coevaluation().emailSentCount, 1)

    def test_public_invalid_token_and_payload(self):
        self.assertEqual(self.client().get('/coevaluations/public/abc').status_code, 404)
        _, token, _ = self.send()
        res = self.post('/coevaluations/public/' + token, scores_payload([3] * 14))
        self.assertEqual(res.status_code, 400)
        # Un payload inválido no consume el token
        self.assertEqual(self.client().get('/coevaluations/public/' + token).status_code, 200)

    def test_statuses_list(self):
        self.post(self.url(suffix="/coordinator"), scores_payload(4))
        res = self.client().get('/pecaprojects/coevaluations/{}'.format(self.peca.id))
        self.assertEqual(res.status_code, 200)
        records = json.loads(res.data)["records"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["teacherId"], str(self.teacher.id))
        self.assertEqual(records[0]["status"], "pending_teacher")

    # ------------------------------------------------------------ permisos

    def newAdmin(self):
        admin = AdminUser(
            firstName="Test", lastName="Admin", cardType="1", cardId="90000001",
            function="Admin", email="admin@test.com", password="12345678", userType="1",
            phone="02322322323", role=role("admin"),
            addressState=self.state, addressMunicipality=self.municipality)
        admin.setHashPassword()
        admin.save()
        return admin

    def test_access_rules_with_token(self):
        other = create_coordinator(self.state, self.municipality, email="otro@test.com",
                                   cardId="20000002")
        admin = self.newAdmin()

        self.assertEqual(self.client().get(
            self.url(), headers=self.headers(self.coordinator)).status_code, 200)
        self.assertEqual(self.client().get(
            self.url(), headers=self.headers(admin)).status_code, 200)
        self.assertEqual(self.client().get(
            self.url(), headers=self.headers(other)).status_code, 403)
        self.assertEqual(self.client().get(
            self.url(), headers=self.headers(self.school)).status_code, 403)

        res = self.post(self.url(suffix="/coordinator"), scores_payload(4),
                        headers=self.headers(other))
        self.assertEqual(res.status_code, 403)
        self.assertIsNone(self.coevaluation())

        res = self.post(self.url(suffix="/coordinator"), scores_payload(4),
                        headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.coevaluation().coordinatorSubmittedBy, str(self.coordinator.id))

    def test_coordinator_without_permission_is_denied(self):
        coordinatorRole = role("coordinator")
        for permission in coordinatorRole.permissions:
            for action in permission.actions:
                if action.name == "teacher_coevaluation":
                    action.allowed = False
        coordinatorRole.save()
        res = self.client().get(self.url(), headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 403)

    # ------------------------------------------------------------- reporte

    def test_report_by_school_and_by_level(self):
        self.complete(self.teacher, 5, 4)  # 67.5 pts, 90 % -> excelencia
        self.post(self.url(self.teacher2, "/coordinator"), scores_payload(2))  # pendiente docente

        res = self.client().get('/statistics/coevaluationsreport/{}'.format(self.schoolYear.id))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertEqual(len(data["bySchool"]), 1)
        school = data["bySchool"][0]
        # Activos: Luisa, Marta y Rosa (sin correo); Pedro inactivo queda fuera.
        self.assertEqual(school["nTeachers"], 3)
        self.assertEqual(school["nCompleted"], 1)
        self.assertEqual(school["index"], 90.0)
        self.assertEqual(school["indexLevel"], "excellence")
        self.assertEqual(school["statusCounts"]["completed"], 1)
        self.assertEqual(school["statusCounts"]["pending_teacher"], 1)
        self.assertEqual(school["statusCounts"]["not_started"], 1)
        self.assertEqual(school["levelCounts"]["excellence"], 1)
        self.assertEqual(school["teachers"][0]["firstName"], "Luisa")
        self.assertEqual(school["teachers"][0]["items"][0]["average"], 4.5)

        levels = dict((lvl["code"], lvl) for lvl in data["byLevel"])
        self.assertEqual([lvl["code"] for lvl in data["byLevel"]],
                         ["excellence", "commitment", "progress", "beginning"])
        self.assertEqual(levels["excellence"]["count"], 1)
        teacher = levels["excellence"]["teachers"][0]
        self.assertEqual(teacher["cardId"], "11111111")
        self.assertEqual(teacher["sections"], u"3er Grado A, 4to Grado B")
        self.assertEqual(teacher["school"]["name"], self.school.name)
        self.assertEqual(levels["commitment"]["count"], 0)

    def test_report_level_filter(self):
        self.complete(self.teacher, 5, 4)
        res = self.client().get('/statistics/coevaluationsreport/{}?level=beginning'.format(
            self.schoolYear.id))
        data = json.loads(res.data)
        self.assertEqual(data["bySchool"], [])
        self.assertEqual([lvl["code"] for lvl in data["byLevel"]], ["beginning"])

        res = self.client().get('/statistics/coevaluationsreport/{}?level=excellence'.format(
            self.schoolYear.id))
        school = json.loads(res.data)["bySchool"][0]
        self.assertEqual(len(school["teachers"]), 1)
        self.assertEqual(school["nTeachers"], 3)

    def test_report_school_filter_and_errors(self):
        res = self.client().get('/statistics/coevaluationsreport/{}?schoolId={}'.format(
            self.schoolYear.id, "5f0000000000000000000000"))
        self.assertEqual(json.loads(res.data)["bySchool"], [])
        res = self.client().get('/statistics/coevaluationsreport/{}?schoolId={}'.format(
            self.schoolYear.id, self.school.id))
        self.assertEqual(len(json.loads(res.data)["bySchool"]), 1)

        self.assertEqual(self.client().get(
            '/statistics/coevaluationsreport/bad').status_code, 404)
        self.assertEqual(self.client().get('/statistics/coevaluationsreport/{}?level=x'.format(
            self.schoolYear.id)).status_code, 400)

    def test_report_past_school_year_lists_only_existing(self):
        self.complete(self.teacher, 3, 3)
        self.schoolYear.status = "2"
        self.schoolYear.save()
        data = json.loads(self.client().get(
            '/statistics/coevaluationsreport/{}'.format(self.schoolYear.id)).data)
        school = data["bySchool"][0]
        self.assertEqual(school["nTeachers"], 1)
        self.assertEqual(school["statusCounts"]["not_started"], 0)

    # ----------------------------------------------------------- migración

    def test_add_permission_command_is_idempotent(self):
        entity = Entity.objects(devName="Teacher").first()
        entity.actions = [a for a in entity.actions if a.name != "teacher_coevaluation"]
        entity.save()
        self.assertFalse(self.allowed("coordinator"))

        add_teacher_coevaluation_permission()
        add_teacher_coevaluation_permission()

        entity.reload()
        self.assertEqual(
            len([a for a in entity.actions if a.name == "teacher_coevaluation"]), 1)
        for devName in ("superadmin", "admin", "coordinator"):
            self.assertTrue(self.allowed(devName), devName)
        self.assertFalse(self.allowed("sponsor"))
        self.assertFalse(self.allowed("school"))

    def allowed(self, devName):
        roleDoc = Role.objects(devName=devName).first()
        actions = [a for p in roleDoc.permissions for a in p.actions
                   if a.name == "teacher_coevaluation"]
        return bool(actions) and all(a.allowed for a in actions)
