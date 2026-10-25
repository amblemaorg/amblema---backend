# app/tests/integration/auth_views_test.py


import unittest
import json
from datetime import datetime

from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app
from app.tests.base import drop_testing_database
from app.models.admin_user_model import AdminUser
from app.models.role_model import Role
from app.models.state_model import State, Municipality


class AuthViewsTest(unittest.TestCase):
    """Login, refresh, /auth/me, recuperación y cambio de contraseña."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        self.role = Role(name="Administrador", devName="admin")
        self.role.save()
        self.state = State(name="Lara")
        self.state.save()
        self.municipality = Municipality(state=self.state, name="Iribarren")
        self.municipality.save()
        self.user = self.createAdmin("admin@test.com", "12345678")

    def tearDown(self):
        drop_testing_database(self.db)

    def createAdmin(self, email, password, role=None):
        user = AdminUser(
            firstName="Test",
            lastName="Admin",
            cardType="1",
            cardId=email.split("@")[0],
            function="Admin",
            email=email,
            password=password,
            userType="1",
            phone="02322322323",
            role=role or self.role,
            addressState=self.state,
            addressMunicipality=self.municipality)
        user.setHashPassword()
        user.save()
        return user

    def post(self, url, data, headers=None):
        return self.client().post(
            url, data=json.dumps(data), content_type='application/json', headers=headers or {})

    def tokens(self, user):
        identity = {"id": str(user.id), "email": user.email}
        return create_access_token(identity), create_refresh_token({"id": str(user.id)})

    # -- Login --

    def test_login_wrong_password(self):
        res = self.post('/auth/login', {"email": "admin@test.com", "password": "otraclave1"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['password'][0]['status'], "14")

    def test_login_invalid_payload(self):
        res = self.post('/auth/login', {"email": "no-es-correo", "password": "123"})
        self.assertEqual(res.status_code, 400)
        body = json.loads(res.data)
        self.assertIn('email', body)
        self.assertIn('password', body)

    def test_login_peca_site_nests_tokens(self):
        res = self.post('/auth/login?site=peca', {"email": "admin@test.com", "password": "12345678"})
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.data)
        self.assertTrue(body['token_access']['access_token'])
        self.assertTrue(body['token_access']['refresh_token'])
        self.assertNotIn('access_token', body)

    def test_login_deleted_user_not_found(self):
        self.user.isDeleted = True
        self.user.save()
        res = self.post('/auth/login', {"email": "admin@test.com", "password": "12345678"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['email'][0]['status'], "5")

    def test_logout_requires_token(self):
        access, _ = self.tokens(self.user)
        res = self.client().delete('/auth/login', headers={"Authorization": "Bearer " + access})
        self.assertEqual(res.status_code, 200)
        res = self.client().delete('/auth/login')
        self.assertEqual(res.status_code, 401)

    # -- Refresh --

    def test_refresh_returns_new_access_token(self):
        _, refresh = self.tokens(self.user)
        res = self.client().post('/auth/refresh', headers={"Authorization": "Bearer " + refresh})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(json.loads(res.data)['access_token'])

    def test_refresh_deleted_user_is_rejected(self):
        _, refresh = self.tokens(self.user)
        self.user.isDeleted = True
        self.user.save()
        res = self.client().post('/auth/refresh', headers={"Authorization": "Bearer " + refresh})
        self.assertEqual(res.status_code, 401)

    def test_refresh_with_access_token_is_rejected(self):
        access, _ = self.tokens(self.user)
        res = self.client().post('/auth/refresh', headers={"Authorization": "Bearer " + access})
        self.assertEqual(res.status_code, 422)

    def test_revoke_refresh_token(self):
        _, refresh = self.tokens(self.user)
        res = self.client().delete('/auth/refresh', headers={"Authorization": "Bearer " + refresh})
        self.assertEqual(res.status_code, 200)

    # -- /auth/me --

    def test_me_returns_user_data(self):
        access, _ = self.tokens(self.user)
        res = self.client().get('/auth/me', headers={"Authorization": "Bearer " + access})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)['data']
        self.assertEqual(data['email'], "admin@test.com")
        self.assertEqual(data['projects'], [])
        self.assertIsNone(data['activeSchoolYear'])
        self.assertIn('permissions', data)

    def test_me_deleted_user(self):
        access, _ = self.tokens(self.user)
        self.user.isDeleted = True
        self.user.save()
        res = self.client().get('/auth/me', headers={"Authorization": "Bearer " + access})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['email'][0]['status'], "5")

    def test_me_inactive_role(self):
        access, _ = self.tokens(self.user)
        self.role.status = "2"
        self.role.save()
        res = self.client().get('/auth/me', headers={"Authorization": "Bearer " + access})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['role'][0]['status'], "15")

    # -- Recuperación y cambio de contraseña --

    def test_password_recovery_unknown_email(self):
        res = self.post('/auth/passwordrecovery', {"email": "nadie@test.com"})
        self.assertEqual(res.status_code, 400)

    def test_password_recovery_changes_password(self):
        res = self.post('/auth/passwordrecovery', {"email": "admin@test.com"})
        self.assertEqual(res.status_code, 200)
        self.user.reload()
        self.assertFalse(self.user.password_is_valid("12345678"))

    def test_change_password_mismatch(self):
        res = self.post('/auth/changepassword', {
            "user": str(self.user.id), "password": "nuevaclave1", "confirmPassword": "nuevaclave2"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['password'][0]['status'], "14")

    def test_change_password_success(self):
        res = self.post('/auth/changepassword', {
            "user": str(self.user.id), "password": "nuevaclave1", "confirmPassword": "nuevaclave1"})
        self.assertEqual(res.status_code, 200)
        self.user.reload()
        self.assertTrue(self.user.password_is_valid("nuevaclave1"))


if __name__ == "__main__":
    unittest.main()
