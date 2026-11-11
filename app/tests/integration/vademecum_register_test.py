# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_register_test.py
"""Registro y verificación de email del docente (API-03). Correo y reCAPTCHA simulados."""

import json
import unittest
from datetime import datetime, timedelta
from unittest import mock

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_school_year, enroll_vademecum_teacher

SEND_EMAIL = "app.services.vademecum.account_service.send_email"


class VademecumRegisterTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes
        ensure_vademecum_indexes()
        self.client = self.app.test_client()
        self.year = create_school_year(name="2026 - 2027", start=datetime(2026, 10, 14),
                                       end=datetime(2027, 8, 31))
        enroll_vademecum_teacher(self.year, "Maria.Perez@Gmail.com", grades=("3",))
        patcher = mock.patch(SEND_EMAIL, return_value=True)
        self.sendEmail = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    def post(self, path, data):
        return self.client.post("/vademecum/auth/" + path, data=json.dumps(data),
                                content_type="application/json")

    def register(self, email="maria.perez@gmail.com", **extra):
        data = {"firstName": "María", "lastName": "Pérez", "email": email}
        data.update(extra)
        return self.post("register", data)

    def account(self, email="maria.perez@gmail.com"):
        from app.models.vademecum import VademecumTeacherAccount
        return VademecumTeacherAccount.objects(email=email).first()

    def link_token(self):
        """Token en claro tomado del último correo simulado."""
        html = self.sendEmail.call_args[0][0]
        return html.split("?token=")[1].split("\"")[0]

    # --- Registro ---

    def test_enrolled_email_creates_pending_account_and_sends_link(self):
        res = self.register(email="  MARIA.perez@gmail.com ")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"result": "verification_sent"})
        account = self.account()
        self.assertEqual(account.status, "pending")
        self.assertIsNone(account.password)
        self.assertIsNone(account.emailVerifiedAt)
        self.assertNotIn(self.link_token(), json.dumps(account.to_mongo().to_dict(), default=str))
        args = self.sendEmail.call_args[0]
        self.assertEqual(args[3], "maria.perez@gmail.com")
        self.assertIn("https://vademecum.test/verificar-email?token=", args[0])
        self.assertIn("48 horas", args[1])

    def test_not_enrolled_email_creates_no_account(self):
        res = self.register(email="otra@gmail.com")
        self.assertEqual(res.get_json(), {"result": "not_enrolled"})
        self.assertIsNone(self.account("otra@gmail.com"))
        self.sendEmail.assert_not_called()

    def test_pending_account_gets_a_new_link_without_duplicates(self):
        self.register()
        account = self.account()
        account.emailVerification.expiresAt = datetime.utcnow() + timedelta(hours=47)
        account.save()  # el primer enlace se emitió hace más de un minuto
        res = self.register()
        self.assertEqual(res.get_json(), {"result": "verification_sent"})
        self.assertEqual(self.sendEmail.call_count, 2)
        from app.models.vademecum import VademecumTeacherAccount
        self.assertEqual(VademecumTeacherAccount.objects.count(), 1)

    def test_link_is_not_resent_within_a_minute(self):
        self.register()
        self.register()
        self.assertEqual(self.sendEmail.call_count, 1)

    def test_active_account_answers_account_exists(self):
        self.register()
        self.post("verify-email", {"token": self.link_token(), "password": "clave-segura"})
        self.assertEqual(self.register().get_json(), {"result": "account_exists"})

    def test_missing_fields_use_current_error_format(self):
        res = self.post("register", {"email": "no-es-email"})
        self.assertEqual(res.status_code, 400)
        body = res.get_json()
        self.assertEqual(body["firstName"][0]["status"], "2")
        self.assertEqual(body["lastName"][0]["status"], "2")
        self.assertEqual(body["email"][0]["status"], "1")

    def test_without_current_school_year_answers_117(self):
        self.year.status = "2"
        self.year.save()
        res = self.register()
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.get_json()["general"][0]["status"], "117")

    def test_email_failure_does_not_break_registration(self):
        self.sendEmail.return_value = ({"msg": "Gmail down"}, 400)
        self.assertEqual(self.register().get_json(), {"result": "verification_sent"})
        self.assertEqual(self.account().status, "pending")

    # --- reCAPTCHA ---

    def test_recaptcha_is_checked_when_configured(self):
        self.app.config["RECAPTCHA_SECRET_KEY"] = "secret"
        with mock.patch("app.services.vademecum.recaptcha_service.requests.post") as post:
            post.return_value.json.return_value = {"success": False}
            res = self.register(recaptchaToken="malo")
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.get_json()["general"][0]["status"], "105")
            post.return_value.json.return_value = {"success": True}
            self.assertEqual(self.register(recaptchaToken="bueno").status_code, 200)

    def test_recaptcha_network_error_rejects(self):
        self.app.config["RECAPTCHA_SECRET_KEY"] = "secret"
        with mock.patch("app.services.vademecum.recaptcha_service.requests.post",
                        side_effect=IOError("timeout")):
            self.assertEqual(self.register(recaptchaToken="x").status_code, 400)

    # --- Verificación ---

    def test_verify_email_activates_account_and_returns_session(self):
        self.register()
        res = self.post("verify-email", {"token": self.link_token(), "password": "clave-segura"})
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["accessToken"] and body["refreshToken"])
        self.assertEqual(body["account"]["email"], "maria.perez@gmail.com")
        self.assertTrue(body["account"]["emailVerifiedAt"].endswith("Z"))
        account = self.account()
        self.assertEqual(account.status, "1")
        self.assertTrue(account.password_is_valid("clave-segura"))
        self.assertIsNotNone(account.emailVerification.usedAt)

    def test_verification_link_works_only_once(self):
        self.register()
        token = self.link_token()
        self.post("verify-email", {"token": token, "password": "clave-segura"})
        res = self.post("verify-email", {"token": token, "password": "otra-clave"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["token"][0]["status"], "104")
        self.assertTrue(self.account().password_is_valid("clave-segura"))

    def test_expired_or_unknown_link_is_rejected(self):
        self.register()
        token = self.link_token()
        account = self.account()
        account.emailVerification.expiresAt = datetime.utcnow() - timedelta(seconds=1)
        account.save()
        for value in (token, "inventado"):
            res = self.post("verify-email", {"token": value, "password": "clave-segura"})
            self.assertEqual(res.get_json()["token"][0]["status"], "104")
        self.assertEqual(self.account().status, "pending")

    def test_short_password_is_rejected(self):
        self.register()
        res = self.post("verify-email", {"token": self.link_token(), "password": "corta"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["password"][0]["status"], "13")

    # --- Reenvío ---

    def test_resend_always_answers_ok(self):
        res = self.post("resend-verification", {"email": "nadie@gmail.com"})
        self.assertEqual((res.status_code, res.get_json()), (200, {"msg": "ok"}))
        self.sendEmail.assert_not_called()

    def test_resend_sends_new_link_to_pending_account(self):
        self.register()
        account = self.account()
        account.emailVerification.expiresAt = datetime.utcnow() + timedelta(hours=47)
        account.save()
        firstToken = self.link_token()
        self.post("resend-verification", {"email": "Maria.Perez@gmail.com"})
        self.assertEqual(self.sendEmail.call_count, 2)
        self.assertNotEqual(self.link_token(), firstToken)
        res = self.post("verify-email", {"token": firstToken, "password": "clave-segura"})
        self.assertEqual(res.status_code, 400)  # el enlace anterior ya no vale


if __name__ == "__main__":
    unittest.main()
