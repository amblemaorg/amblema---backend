# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_session_test.py
"""Login, sesión, recuperación de contraseña y /me del docente (API-04)."""

import json
import re
import unittest
from datetime import datetime, timedelta
from unittest import mock

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_school_year, enroll_vademecum_teacher

SEND_EMAIL = "app.services.vademecum.account_service.send_email"
PASSWORD = "clave-segura"


class VademecumSessionBase(unittest.TestCase):

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
        patcher = mock.patch(SEND_EMAIL, return_value=True)
        self.sendEmail = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    def create_account(self, email="maria.perez@gmail.com", status="1", password=PASSWORD):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=email, firstName="María", lastName="Pérez",
                                          status=status)
        if password:
            account.set_password(password)
            # Contraseña creada hace un rato: los tokens nuevos son posteriores
            account.passwordChangedAt = datetime.utcnow() - timedelta(minutes=5)
        if status == "1":
            account.emailVerifiedAt = datetime.utcnow()
        account.save()
        return account

    def request(self, method, path, data=None, token=None):
        headers = {"Authorization": "Bearer " + token} if token else {}
        return self.client.open(path, method=method, headers=headers,
                                data=json.dumps(data) if data is not None else None,
                                content_type="application/json")

    def login(self, email="maria.perez@gmail.com", password=PASSWORD):
        return self.request("POST", "/vademecum/auth/login",
                            {"email": email, "password": password})


class VademecumLoginTest(VademecumSessionBase):

    def test_login_returns_tokens_and_account(self):
        self.create_account()
        res = self.login(email=" Maria.Perez@Gmail.com ")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["account"]["email"], "maria.perez@gmail.com")
        me = self.request("GET", "/vademecum/me", token=body["accessToken"])
        self.assertEqual(me.status_code, 200)

    def test_wrong_password_or_unknown_email_answer_103(self):
        self.create_account()
        for res in (self.login(password="otra-clave"), self.login(email="nadie@gmail.com")):
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.get_json()["general"][0]["status"], "103")

    def test_pending_account_answers_102(self):
        self.create_account(status="pending", password=None)
        res = self.login()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["general"][0]["status"], "102")

    def test_blocked_account_answers_101(self):
        self.create_account(status="2")
        res = self.login()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["general"][0]["status"], "101")


class VademecumTokenTest(VademecumSessionBase):

    def tokens(self):
        self.create_account()
        return self.login().get_json()

    def test_access_token_is_required(self):
        for token in (None, "basura", "a.b.c"):
            res = self.request("GET", "/vademecum/me", token=token)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.get_json()["general"][0]["status"], "100")

    def test_refresh_token_is_not_an_access_token(self):
        tokens = self.tokens()
        self.assertEqual(
            self.request("GET", "/vademecum/me", token=tokens["refreshToken"]).status_code, 401)
        self.assertEqual(self.request("POST", "/vademecum/auth/refresh",
                                      token=tokens["accessToken"]).status_code, 401)

    def test_refresh_returns_new_access_token(self):
        tokens = self.tokens()
        res = self.request("POST", "/vademecum/auth/refresh", token=tokens["refreshToken"])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.request("GET", "/vademecum/me",
                                      token=res.get_json()["accessToken"]).status_code, 200)

    def test_expired_token_is_rejected(self):
        tokens = self.tokens()
        with mock.patch("app.services.vademecum.token_service.ACCESS_LIFETIME",
                        timedelta(seconds=-10)):
            from app.models.vademecum import VademecumTeacherAccount
            from app.services.vademecum.token_service import issue_access_token
            expired = issue_access_token(VademecumTeacherAccount.objects.first())
        self.assertEqual(self.request("GET", "/vademecum/me", token=expired).status_code, 401)
        self.assertEqual(self.request("GET", "/vademecum/me",
                                      token=tokens["accessToken"]).status_code, 200)

    def test_blocked_account_token_answers_101(self):
        tokens = self.tokens()
        from app.models.vademecum import VademecumTeacherAccount
        VademecumTeacherAccount.objects.update(status="2")
        res = self.request("GET", "/vademecum/me", token=tokens["accessToken"])
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["general"][0]["status"], "101")

    def test_deleted_account_token_is_rejected(self):
        tokens = self.tokens()
        from app.models.vademecum import VademecumTeacherAccount
        VademecumTeacherAccount.objects.update(isDeleted=True)
        self.assertEqual(self.request("GET", "/vademecum/me",
                                      token=tokens["accessToken"]).status_code, 401)

    def test_token_signed_with_backoffice_secret_is_rejected(self):
        import jwt
        account = self.create_account()
        now = int(datetime.utcnow().timestamp())
        forged = jwt.encode({"sub": str(account.id), "type": "vademecum_teacher",
                             "kind": "access", "iat": now, "exp": now + 600},
                            self.app.config["SECRET_KEY"] or "x", algorithm="HS256")
        if isinstance(forged, bytes):
            forged = forged.decode()
        self.assertEqual(self.request("GET", "/vademecum/me", token=forged).status_code, 401)

    def test_backoffice_token_is_rejected_by_vademecum(self):
        from flask_jwt_extended import create_access_token
        self.app.config["SECRET_KEY"] = "backoffice-secret"
        backoffice = create_access_token(identity=str(ObjectId()))
        self.assertEqual(self.request("GET", "/vademecum/me", token=backoffice).status_code, 401)

    def test_no_token_is_issued_without_own_secret(self):
        self.create_account()
        self.app.config["VADEMECUM_JWT_SECRET_KEY"] = None
        with self.assertRaises(RuntimeError):
            self.login()
        self.app.config["VADEMECUM_JWT_SECRET_KEY"] = self.app.config["SECRET_KEY"] = "igual"
        with self.assertRaises(RuntimeError):
            self.login()


class VademecumExistingEndpointsTest(VademecumSessionBase):
    """El token de docente no abre ningún endpoint existente de la API (criterio de API-04)."""

    def status(self, method, url, token=None):
        """Código HTTP; una excepción del endpoint cuenta como 500 (no lo abre)."""
        try:
            return self.request(method, url, token=token).status_code
        except Exception:
            return 500

    def fill(self, rule):
        path = re.sub(r"<int:[^>]+>", "1", rule)
        return re.sub(r"<[^>]+>", str(ObjectId()), path)

    def test_teacher_token_is_rejected_by_flask_jwt_extended(self):
        from flask_jwt_extended import verify_jwt_in_request
        self.app.config["SECRET_KEY"] = "backoffice-secret"
        self.create_account()
        token = self.login().get_json()["accessToken"]
        with self.app.test_request_context(headers={"Authorization": "Bearer " + token}):
            with self.assertRaises(Exception):
                verify_jwt_in_request()

    def test_teacher_token_opens_no_existing_get_endpoint(self):
        self.app.config["SECRET_KEY"] = "backoffice-secret"
        self.create_account()
        token = self.login().get_json()["accessToken"]
        self.app.config["TESTING"] = False  # jwt_required/admin_required se saltan en TESTING
        self.addCleanup(self.app.config.__setitem__, "TESTING", True)
        checked, opened, rejected = 0, [], 0
        with mock.patch("app.helpers.handler_emails.send_email_gmail", return_value=True), \
                mock.patch("app.helpers.handler_emails.send_email_smtp", return_value=True):
            for rule in self.app.url_map.iter_rules():
                path = str(rule)
                if path.startswith("/vademecum") or path.startswith("/static") \
                        or "GET" not in rule.methods:
                    continue
                url = self.fill(path)
                withTeacher = self.status("GET", url, token)
                if withTeacher in (401, 422):
                    rejected += 1
                if 200 <= withTeacher < 300:
                    anonymous = self.status("GET", url)
                    if not 200 <= anonymous < 300:
                        opened.append((path, withTeacher, anonymous))
                checked += 1
        self.assertGreater(checked, 50)
        self.assertGreater(rejected, 20)  # los protegidos rechazan el token de docente
        self.assertEqual(opened, [])


class VademecumPasswordTest(VademecumSessionBase):

    def link_token(self):
        html = self.sendEmail.call_args[0][0]
        return html.split("?token=")[1].split("\"")[0]

    def forgot(self, email="maria.perez@gmail.com"):
        return self.request("POST", "/vademecum/auth/forgot-password", {"email": email})

    def test_forgot_password_always_answers_ok(self):
        res = self.forgot("nadie@gmail.com")
        self.assertEqual((res.status_code, res.get_json()), (200, {"msg": "ok"}))
        self.sendEmail.assert_not_called()

    def test_reset_password_changes_it_and_invalidates_old_tokens(self):
        self.create_account()
        oldTokens = self.login().get_json()
        self.forgot()
        self.assertIn("https://vademecum.test/restablecer-contrasena?token=",
                      self.sendEmail.call_args[0][0])
        token = self.link_token()
        res = self.request("POST", "/vademecum/auth/reset-password",
                           {"token": token, "password": "nueva-clave"})
        self.assertEqual(res.status_code, 200)
        newToken = res.get_json()["accessToken"]
        self.assertEqual(self.request("GET", "/vademecum/me",
                                      token=oldTokens["accessToken"]).status_code, 401)
        self.assertEqual(self.request("POST", "/vademecum/auth/refresh",
                                      token=oldTokens["refreshToken"]).status_code, 401)
        self.assertEqual(self.request("GET", "/vademecum/me", token=newToken).status_code, 200)
        self.assertEqual(self.login(password="nueva-clave").status_code, 200)
        again = self.request("POST", "/vademecum/auth/reset-password",
                             {"token": token, "password": "otra-clave"})
        self.assertEqual(again.get_json()["token"][0]["status"], "104")

    def test_expired_reset_link_is_rejected(self):
        account = self.create_account()
        self.forgot()
        account.reload()
        account.passwordReset.expiresAt = datetime.utcnow() - timedelta(seconds=1)
        account.save()
        res = self.request("POST", "/vademecum/auth/reset-password",
                           {"token": self.link_token(), "password": "nueva-clave"})
        self.assertEqual(res.get_json()["token"][0]["status"], "104")

    def test_forgot_password_on_pending_account_resends_activation(self):
        self.create_account(status="pending", password=None)
        self.forgot()
        self.assertIn("/verificar-email?token=", self.sendEmail.call_args[0][0])

    def test_change_password_with_session(self):
        self.create_account()
        token = self.login().get_json()["accessToken"]
        bad = self.request("PUT", "/vademecum/me/password",
                           {"currentPassword": "mala", "newPassword": "nueva-clave"}, token)
        self.assertEqual(bad.get_json()["currentPassword"][0]["status"], "103")
        res = self.request("PUT", "/vademecum/me/password",
                           {"currentPassword": PASSWORD, "newPassword": "nueva-clave"}, token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.request("GET", "/vademecum/me", token=token).status_code, 401)
        self.assertEqual(self.request("GET", "/vademecum/me",
                                      token=res.get_json()["accessToken"]).status_code, 200)


class VademecumMeTest(VademecumSessionBase):

    def token(self, email="maria.perez@gmail.com"):
        self.create_account(email=email)
        return self.login(email=email).get_json()["accessToken"]

    def test_me_shows_enrollment_schools_and_grades(self):
        schoolId = enroll_vademecum_teacher(self.year, "maria.perez@gmail.com", grades=("4", "3"))
        body = self.request("GET", "/vademecum/me", token=self.token()).get_json()
        self.assertEqual(body["account"]["email"], "maria.perez@gmail.com")
        access = body["access"]
        self.assertEqual(access["origin"], "enrollment")
        self.assertEqual(access["schoolYear"], {"id": str(self.year.id), "name": "2026 - 2027"})
        self.assertEqual(access["schools"][0]["id"], schoolId)
        self.assertEqual(access["grades"], ["3", "4"])

    def test_me_shows_external_with_authorization_of_the_year(self):
        from app.models.vademecum import VademecumAuthorization
        from app.models.vademecum import VademecumTeacherAccount
        token = self.token()
        VademecumAuthorization(account=VademecumTeacherAccount.objects.first(),
                               schoolYear=self.year, approvedBy=ObjectId()).save()
        access = self.request("GET", "/vademecum/me", token=token).get_json()["access"]
        self.assertEqual((access["origin"], access["schools"]), ("external", []))

    def test_enrollment_has_priority_over_authorization(self):
        from app.models.vademecum import VademecumAuthorization, VademecumTeacherAccount
        enroll_vademecum_teacher(self.year, "maria.perez@gmail.com")
        token = self.token()
        VademecumAuthorization(account=VademecumTeacherAccount.objects.first(),
                               schoolYear=self.year, approvedBy=ObjectId()).save()
        access = self.request("GET", "/vademecum/me", token=token).get_json()["access"]
        self.assertEqual(access["origin"], "enrollment")

    def test_me_without_access_answers_none(self):
        access = self.request("GET", "/vademecum/me", token=self.token()).get_json()["access"]
        self.assertEqual((access["origin"], access["schools"], access["grades"]),
                         ("none", [], []))

    def test_update_profile(self):
        token = self.token()
        res = self.request("PUT", "/vademecum/me", {"firstName": " Mariela ", "email": "x@x.com"},
                           token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["firstName"], "Mariela")
        self.assertEqual(res.get_json()["email"], "maria.perez@gmail.com")
        bad = self.request("PUT", "/vademecum/me", {"lastName": "x" * 61}, token)
        self.assertEqual(bad.get_json()["lastName"][0]["status"], "13")


if __name__ == "__main__":
    unittest.main()
