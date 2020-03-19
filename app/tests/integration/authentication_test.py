# app/tests/integration/authentication.py

from datetime import datetime
import unittest
import json
from app import create_app, db
from app.models.role_model import Role
from app.models.user_model import User


class AuthTestCase(unittest.TestCase):
    """Test case for the authentication blueprint."""

    def setUp(self):
        """Set up test variables."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        # initialize the test client
        self.client = self.app.test_client
        # This is the user test json data with a predefined email and password
        role = Role(name='role test')
        role.save()
        self.user = User(
            firstName="Super",
            lastName="Admin",
            name="Super Admin",
            email='testemail@test.com',
            password='password',
            cardType="1",
            cardId="00000000",
            birthdate=datetime.utcnow(),
            homePhone="07000000000",
            userType="0",
            phone="02322322323",
            role=role)
        self.user.setHashPassword()
        self.user.save()

    def test_user_login(self):
        """Test user can do login."""
        data = {
            "email": "testemail@test.com",
            "password": "password"
        }
        res = self.client().post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps(data))

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(result['access_token'])

    def test_non_registered_user_login(self):
        """Test non registered users cannot login."""
        not_a_user = {
            "email": "notauser@test.com",
            "password": "password"
        }
        res = self.client().post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps(not_a_user))
        result = json.loads(res.data.decode())

        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            {'email': [{'msg': 'Record not found: notauser@test.com', 'status': '5'}]},
            result)

    def test_user_login_upper_or_lower(self):
        """Test registered user can login with lower o upper case email."""
        data = {
            "email": "Testemail@test.com",
            "password": "password"
        }
        login_res = self.client().post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps(data))

        result = json.loads(login_res.data.decode())
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access_token'])

    def test_recover_password(self):
        data = {
            "email": "Testemail@test.com",
        }
        res = self.client().post(
            '/auth/passwordrecovery',
            content_type='application/json',
            data=json.dumps(data))
        self.assertEqual(res.status_code, 200)

    def test_change_password(self):
        data = {
            "user": str(self.user.pk),
            "password": "mynewpassword",
            "confirmPassword": "mynewpassword"
        }
        res = self.client().post(
            '/auth/changepassword',
            content_type='application/json',
            data=json.dumps(data))
        self.assertEqual(res.status_code, 200)

        user = User.objects.get(id=self.user.pk)
        self.assertEqual(True, user.password_is_valid(data['password']))

    def test_inactive_rol(self):
        role = Role.objects.first()
        role.status = "2"
        role.save()
        data = {
            "email": "testemail@test.com",
            "password": "password"
        }
        res = self.client().post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps(data))

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            {'role': [{'msg': 'No authorized', 'status': '15'}]}, result)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
