# app/tests/integration/admin_user_test.py


import unittest
import json
from copy import deepcopy

from app import create_app, db

from app.models.step_model import Step, Check
from app.models.admin_user_model import AdminUser
from app.models.role_model import Role
from app.models.state_model import State, Municipality


class AdminUserTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        self.role = Role(name="test")
        self.role.save()

        self.state = State(
            name="Lara"
        )
        self.state.save()

        self.municipality = Municipality(
            state=self.state,
            name="Iribarren"
        )
        self.municipality.save()

    def test_endpoint_admin_duplicated_cardId(self):

        adminData = dict(
            firstName="Test",
            lastName="Test",
            cardType="1",
            cardId="20922842",
            function="Admin",
            email="testemail@test.com",
            password="12345678",
            userType="1",
            phone="02322322323",
            role=str(self.role.pk),
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk)
        )
        res = self.client().post(
            '/users/?userType=1',
            data=json.dumps(adminData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

        adminDuplicatedCardId = dict(
            firstName="Test",
            lastName="Test",
            cardType="1",
            cardId="20922842",
            function="Admin",
            email="testduplicated@test.com",
            password="12345678",
            userType="1",
            phone="02322322323",
            role=str(self.role.pk),
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk)
        )
        res = self.client().post(
            '/users/?userType=1',
            data=json.dumps(adminDuplicatedCardId),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)
        result_json = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual({'cardId': [
                         {'status': '5', 'msg': 'Duplicated record found: 20922842'}]}, result_json)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
