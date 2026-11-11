# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_access_request_test.py
"""Solicitudes de acceso y autorizaciones por año escolar (API-05)."""

import json
import unittest
from datetime import datetime
from unittest import mock

from app.tests.fixtures import create_school_year, enroll_vademecum_teacher
from app.tests.integration.vademecum_upload_test import VademecumUploadBase

SEND_VERIFICATION = "app.services.vademecum.account_service.send_email"
SEND_NOTICE = "app.services.vademecum.access_request_service.send_email"
EMAIL = "luis.gomez@gmail.com"


class VademecumAccessRequestTest(VademecumUploadBase):

    def setUp(self):
        super(VademecumAccessRequestTest, self).setUp()
        self.year = create_school_year(name="2026 - 2027", start=datetime(2026, 10, 14),
                                       end=datetime(2027, 8, 31))
        for target in (SEND_VERIFICATION, SEND_NOTICE):
            patcher = mock.patch(target, return_value=True)
            setattr(self, "mail_" + target.split(".")[-2], patcher.start())
            self.addCleanup(patcher.stop)

    def payload(self, **extra):
        data = {"firstName": "Luis", "lastName": u"Gómez", "email": "Luis.Gomez@gmail.com ",
                "cardId": "V-12345678", "phone": "04141234567",
                "institution": u"U.E. Los Robles"}
        data.update(extra)
        return data

    def request_access(self, **extra):
        return self.client.post("/vademecum/access-requests",
                                data=json.dumps(self.payload(**extra)),
                                content_type="application/json")

    def bo(self, method, path, data=None, headers=None):
        return self.client.open("/vademecum/admin" + path, method=method,
                                headers=self.adminHeaders if headers is None else headers,
                                data=json.dumps(data) if data is not None else None,
                                content_type="application/json")

    def assert_error(self, res, httpStatus, field, code):
        self.assertEqual(res.status_code, httpStatus, res.get_data(as_text=True))
        self.assertEqual(res.get_json()[field][0]["status"], code)

    # --- Solicitud pública ---

    def test_request_is_stored_without_school(self):
        res = self.request_access()
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        self.assertEqual(res.get_json()["status"], "pending")
        from app.models.vademecum import VademecumAccessRequest, VademecumTeacherAccount
        stored = VademecumAccessRequest.objects.get(id=res.get_json()["id"])
        self.assertEqual((stored.email, stored.institution, stored.schoolYear.id),
                         (EMAIL, u"U.E. Los Robles", self.year.id))
        self.assertIsNone(stored.account)
        self.assertEqual(VademecumTeacherAccount.objects.count(), 0)

    def test_request_validation(self):
        res = self.request_access(firstName="", institution="", email="x")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(set(res.get_json()), {"firstName", "institution", "email"})

    def test_enrolled_email_does_not_need_a_request(self):
        enroll_vademecum_teacher(self.year, EMAIL)
        self.assert_error(self.request_access(), 409, "email", "106")

    def test_only_one_pending_request_or_authorization_per_year(self):
        self.request_access()
        self.assert_error(self.request_access(), 409, "email", "107")
        requestId = self.bo("GET", "/access-requests").get_json()["records"][0]["id"]
        self.bo("POST", "/access-requests/{}/approve".format(requestId))
        self.assert_error(self.request_access(), 409, "email", "107")

    def test_without_current_year_answers_117(self):
        self.year.status = "2"
        self.year.save()
        self.assert_error(self.request_access(), 409, "general", "117")

    # --- Revisión ---

    def first_request_id(self):
        self.request_access()
        return self.bo("GET", "/access-requests?status=pending").get_json()["records"][0]["id"]

    def test_list_filters_and_searches(self):
        self.request_access()
        self.request_access(email="ana@test.com", firstName="Ana", cardId="V-999")
        body = self.bo("GET", "/access-requests?status=pending").get_json()
        self.assertEqual([r["email"] for r in body["records"]], [EMAIL, "ana@test.com"])
        self.assertEqual(body["records"][0]["schoolYear"]["name"], "2026 - 2027")
        found = self.bo("GET", "/access-requests?q=v-999").get_json()["records"]
        self.assertEqual([r["email"] for r in found], ["ana@test.com"])
        self.assertEqual(self.bo("GET", "/access-requests?status=x").status_code, 400)

    def test_approve_creates_pending_account_authorization_and_emails_the_link(self):
        requestId = self.first_request_id()
        res = self.bo("POST", "/access-requests/{}/approve".format(requestId))
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual((body["status"], body["reviewedBy"]["id"]),
                         ("approved", str(self.admin.id)))
        from app.models.vademecum import VademecumAuthorization, VademecumTeacherAccount
        account = VademecumTeacherAccount.objects.get(email=EMAIL)
        self.assertEqual((account.status, account.firstName), ("pending", "Luis"))
        authorization = VademecumAuthorization.objects.get(account=account.id)
        self.assertEqual(authorization.schoolYear.id, self.year.id)
        self.assertEqual(self.mail_account_service.call_count, 1)
        self.assertIn("/verificar-email?token=", self.mail_account_service.call_args[0][0])
        self.assert_error(self.bo("POST", "/access-requests/{}/approve".format(requestId)),
                          409, "general", "118")

    def test_approve_reuses_an_active_account_and_notifies(self):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=EMAIL, firstName="Luis", lastName="G",
                                          status="1", emailVerifiedAt=datetime.utcnow())
        account.set_password("clave-segura")
        account.save()
        requestId = self.first_request_id()
        self.bo("POST", "/access-requests/{}/approve".format(requestId))
        account.reload()
        self.assertEqual(account.status, "1")
        self.assertEqual(self.mail_account_service.call_count, 0)
        self.assertIn("aprobado", self.mail_access_request_service.call_args[0][2])

    def test_reject_requires_reason_and_emails_it(self):
        requestId = self.first_request_id()
        self.assert_error(self.bo("POST", "/access-requests/{}/reject".format(requestId),
                                     {"reason": ""}), 400, "reason", "2")
        res = self.bo("POST", "/access-requests/{}/reject".format(requestId),
                         {"reason": u"No es docente"})
        self.assertEqual((res.get_json()["status"], res.get_json()["rejectionReason"]),
                         ("rejected", u"No es docente"))
        self.assertIn(u"No es docente", self.mail_access_request_service.call_args[0][1])
        from app.models.vademecum import VademecumTeacherAccount
        self.assertEqual(VademecumTeacherAccount.objects.count(), 0)
        # Rechazada no bloquea una nueva solicitud
        self.assertEqual(self.request_access().status_code, 201)

    def test_email_failure_does_not_undo_the_review(self):
        self.mail_access_request_service.return_value = ({"msg": "Gmail down"}, 400)
        requestId = self.first_request_id()
        res = self.bo("POST", "/access-requests/{}/reject".format(requestId),
                         {"reason": "x"})
        self.assertEqual(res.status_code, 200)

    def test_review_requires_admin(self):
        requestId = self.first_request_id()
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        for path in ("/access-requests", "/authorizations"):
            self.assertEqual(self.bo("GET", path, headers=self.headers(coordinator))
                             .status_code, 403)
        self.assertEqual(self.bo("POST", "/access-requests/{}/approve".format(requestId),
                                    headers={}).status_code, 401)

    # --- Autorización: externo y vencimiento ---

    def activate(self):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount.objects.get(email=EMAIL)
        account.set_password("clave-segura")
        account.status = "1"
        account.emailVerifiedAt = datetime.utcnow()
        account.save()
        from app.services.vademecum.token_service import issue_access_token
        return issue_access_token(account)

    def me(self, token):
        return self.client.get("/vademecum/me",
                               headers={"Authorization": "Bearer " + token}).get_json()

    def test_authorized_teacher_appears_as_external_until_the_year_changes(self):
        requestId = self.first_request_id()
        self.bo("POST", "/access-requests/{}/approve".format(requestId))
        token = self.activate()
        self.assertEqual(self.me(token)["access"]["origin"], "external")
        records = self.bo("GET", "/authorizations").get_json()["records"]
        self.assertEqual([r["account"]["email"] for r in records], [EMAIL])
        self.assertEqual(records[0]["accessRequestId"], requestId)

        # Nuevo año vigente: la autorización anterior ya no da acceso
        self.year.status = "2"
        self.year.save()
        create_school_year(name="2027 - 2028", start=datetime(2027, 9, 15),
                           end=datetime(2028, 7, 31))
        self.assertEqual(self.me(token)["access"]["origin"], "none")
        self.assertEqual(self.bo("GET", "/authorizations").get_json()["records"], [])
        old = self.bo("GET", "/authorizations?schoolYearId={}".format(self.year.id))
        self.assertEqual(len(old.get_json()["records"]), 1)

    def test_revoke_keeps_the_record_and_removes_access(self):
        requestId = self.first_request_id()
        self.bo("POST", "/access-requests/{}/approve".format(requestId))
        token = self.activate()
        authorizationId = self.bo("GET", "/authorizations").get_json()["records"][0]["id"]
        res = self.bo("POST", "/authorizations/{}/revoke".format(authorizationId))
        self.assertIsNotNone(res.get_json()["revokedAt"])
        self.assertEqual(self.me(token)["access"]["origin"], "none")
        # Una nueva solicitud aprobada renueva la misma autorización del año
        requestId = self.first_request_id()
        self.bo("POST", "/access-requests/{}/approve".format(requestId))
        self.assertEqual(self.me(token)["access"]["origin"], "external")
        from app.models.vademecum import VademecumAuthorization
        self.assertEqual(VademecumAuthorization.objects.count(), 1)


if __name__ == "__main__":
    unittest.main()
