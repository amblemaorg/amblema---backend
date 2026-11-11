# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_base.py
"""Base de las pruebas de administración de Vademécum (no es un archivo *_test)."""

import shutil
import tempfile
import unittest

from flask_jwt_extended import create_access_token

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_location


class VademecumAdminTestBase(unittest.TestCase):
    """Backoffice con almacenamiento temporal, semillas, permiso y un administrador."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.handler_seeds import create_standard_roles
        from app.helpers.vademecum_seeds import (
            ensure_vademecum_indexes, ensure_vademecum_permission, seed_vademecum)
        create_standard_roles()
        ensure_vademecum_permission()
        ensure_vademecum_indexes()
        seed_vademecum()
        self.client = self.app.test_client()
        self.storage = tempfile.mkdtemp()
        self.app.config["VADEMECUM_STORAGE_PATH"] = self.storage
        from app.models.vademecum import VademecumSheetType
        self.hora = VademecumSheetType.objects(codePrefix="HT").first()
        self.ingenio = VademecumSheetType.objects(codePrefix="IM").first()
        self.state, self.municipality = create_location()
        self.admin = self.create_user("admin@test.com", "10000001", "admin")
        self.adminHeaders = self.headers(self.admin)

    def tearDown(self):
        shutil.rmtree(self.storage, ignore_errors=True)
        drop_testing_database(self.db)
        self.context.pop()

    def create_user(self, email, cardId, roleName):
        from app.models.admin_user_model import AdminUser
        from app.models.role_model import Role
        user = AdminUser(
            firstName="Admin", lastName="AmbLeMa", cardType="1", cardId=cardId,
            function="Admin", email=email, password="12345678", userType="1",
            phone="02322322323", role=Role.objects(devName=roleName).first(),
            addressState=self.state, addressMunicipality=self.municipality)
        user.setHashPassword()
        user.save()
        return user

    def headers(self, user):
        token = create_access_token({"id": str(user.id), "email": user.email})
        return {"Authorization": "Bearer " + token}

    def assert_error(self, res, httpStatus, field, code):
        self.assertEqual(res.status_code, httpStatus, res.get_data(as_text=True))
        self.assertEqual(res.get_json()[field][0]["status"], code)
