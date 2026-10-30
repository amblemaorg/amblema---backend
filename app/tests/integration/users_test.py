# app/tests/integration/users_test.py


import unittest
import json
from datetime import datetime

from flask_jwt_extended import create_access_token

from app import create_app
from app.tests.base import drop_testing_database
from app.helpers.handler_seeds import create_standard_roles, create_initial_steps
from app.models.admin_user_model import AdminUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.sponsor_user_model import SponsorUser
from app.models.school_user_model import SchoolUser
from app.models.project_model import Project
from app.models.school_year_model import SchoolYear
from app.models.role_model import Role
from app.models.state_model import State, Municipality


class UsersTest(unittest.TestCase):
    """CRUD de usuarios (/users), autorización, reenvío de correos y opciones."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        create_standard_roles()
        self.state = State(name="Lara")
        self.state.save()
        self.municipality = Municipality(state=self.state, name="Iribarren")
        self.municipality.save()

        self.admin = self.createAdmin("admin@test.com", "10000001", "admin")
        self.superadmin = self.createAdmin("super@test.com", "10000002", "superadmin")
        self.coordinator = CoordinatorUser(
            firstName="Ana", lastName="Pérez", cardType="1", cardId="20000001",
            birthdate=datetime.utcnow(), gender="1", homePhone="02343432323",
            addressHome="Casa 1", email="coordinador@test.com", password="12345678",
            userType="2", phone="02322322323", role=self.role("coordinator"),
            addressState=self.state, addressMunicipality=self.municipality, isReferred=False)
        self.coordinator.setHashPassword()
        self.coordinator.save()

    def tearDown(self):
        self.app.config["TESTING"] = True
        drop_testing_database(self.db)

    # -- helpers --

    def role(self, devName):
        return Role.objects(devName=devName).first()

    def createAdmin(self, email, cardId, roleName):
        user = AdminUser(
            firstName="Test", lastName="Admin", cardType="1", cardId=cardId,
            function="Admin", email=email, password="12345678", userType="1",
            phone="02322322323", role=self.role(roleName),
            addressState=self.state, addressMunicipality=self.municipality)
        user.setHashPassword()
        user.save()
        return user

    def createActiveSchoolYear(self):
        create_initial_steps()
        schoolYear = SchoolYear(
            name="2025 - 2026", startDate=datetime(2025, 9, 1), endDate=datetime(2026, 7, 31))
        schoolYear.initFirstPecaSetting()
        schoolYear.save()
        return schoolYear

    def createSponsor(self):
        sponsor = SponsorUser(
            name="Empresa", companyRif="303993833", companyType="2",
            companyPhone="02343432323", contactFirstName="Luis", contactLastName="Gómez",
            contactPhone="04244664646", addressHome="Calle 1", email="padrino@test.com",
            password="12345678", userType="3", role=self.role("sponsor"),
            addressState=self.state, addressMunicipality=self.municipality)
        sponsor.save()
        return sponsor

    def createSchool(self):
        school = SchoolUser(
            name="Escuela 1", code="0002", phone="02343432323", schoolType="1",
            principalFirstName="Rosa", principalLastName="Díaz",
            principalEmail="directora@test.com", principalPhone="04244664646",
            nTeachers=20, nAdministrativeStaff=2, nLaborStaff=2, nStudents=200,
            nGrades=6, nSections=12, schoolShift="1", email="escuela@test.com",
            password="12345678", userType="4", role=self.role("school"),
            addressState=self.state, addressMunicipality=self.municipality)
        school.save()
        return school

    def headers(self, user):
        token = create_access_token({"id": str(user.id), "email": user.email})
        return {"Authorization": "Bearer " + token}

    def adminPayload(self, **overrides):
        data = dict(
            firstName="Nuevo", lastName="Admin", cardType="1", cardId="30000001",
            function="Admin", email="nuevo@test.com", password="12345678", userType="1",
            phone="02322322323", role=str(self.role("admin").pk),
            addressState=str(self.state.pk), addressMunicipality=str(self.municipality.pk))
        data.update(overrides)
        return data

    def put(self, userId, data, userType="1", headers=None):
        return self.client().put(
            '/users/{}?userType={}'.format(userId, userType), data=json.dumps(data),
            content_type='application/json', headers=headers or {})

    # -- Alta, consulta y unicidad --

    def test_create_and_get_admin(self):
        res = self.client().post('/users?userType=1', data=json.dumps(self.adminPayload()),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 201)
        created = json.loads(res.data)
        self.assertNotIn('password', created)

        res = self.client().get('/users/{}?userType=1'.format(created['id']))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['email'], "nuevo@test.com")

    def test_create_with_duplicated_email(self):
        res = self.client().post(
            '/users?userType=1', data=json.dumps(self.adminPayload(email="ADMIN@test.com")),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['email'][0]['status'], "5")

    def test_create_ignores_deleted_duplicates(self):
        self.admin.isDeleted = True
        self.admin.save()
        res = self.client().post(
            '/users?userType=1', data=json.dumps(self.adminPayload(email="admin@test.com", cardId="10000001")),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_list_filters_by_user_type(self):
        res = self.client().get('/users?userType=2')
        self.assertEqual(res.status_code, 200)
        emails = [u['email'] for u in json.loads(res.data)['records']]
        self.assertEqual(emails, ["coordinador@test.com"])

    def test_get_unknown_user(self):
        res = self.client().get('/users/5f0000000000000000000000?userType=1')
        self.assertEqual(res.status_code, 404)

    # -- Edición --

    def test_update_to_duplicated_email(self):
        res = self.put(self.admin.id, {"email": "super@test.com"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(json.loads(res.data)['email'][0]['status'], "5")

    def test_update_same_values_keeps_record(self):
        res = self.put(self.admin.id, {"email": "admin@test.com", "cardId": "10000001"})
        self.assertEqual(res.status_code, 200)

    def test_update_password_is_hashed(self):
        res = self.put(self.admin.id, {"password": "otraclave1"})
        self.assertEqual(res.status_code, 200)
        self.admin.reload()
        self.assertNotEqual(self.admin.password, "otraclave1")
        self.assertTrue(self.admin.password_is_valid("otraclave1"))

    def test_coordinator_name_change_reaches_projects(self):
        self.createActiveSchoolYear()
        school = self.createSchool()
        sponsor = self.createSponsor()
        project = Project(coordinator=self.coordinator, sponsor=sponsor, school=school)
        project.save()

        res = self.put(self.coordinator.id, {"firstName": "María"}, userType="2")
        self.assertEqual(res.status_code, 200)

        project.reload()
        school.reload()
        sponsor.reload()
        self.assertEqual(school.project.coordinator.name, "María Pérez")
        self.assertEqual(sponsor.projects[0].coordinator.name, "María Pérez")

    # -- Autorización (fuera del modo TESTING, con token real) --

    def test_non_admin_cannot_edit_other_user(self):
        self.app.config["TESTING"] = False
        res = self.put(self.admin.id, {"firstName": "X"}, headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 403)

    def test_non_admin_cannot_change_own_role(self):
        self.app.config["TESTING"] = False
        res = self.put(
            self.coordinator.id,
            {"firstName": "Ana María", "role": str(self.role("admin").pk), "status": "2"},
            userType="2", headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 200)
        self.coordinator.reload()
        self.assertEqual(self.coordinator.firstName, "Ana María")
        self.assertEqual(self.coordinator.role.devName, "coordinator")
        self.assertEqual(self.coordinator.status, "1")

    def test_admin_cannot_edit_superadmin(self):
        self.app.config["TESTING"] = False
        res = self.put(self.superadmin.id, {"firstName": "X"}, headers=self.headers(self.admin))
        self.assertEqual(res.status_code, 403)
        res = self.put(self.superadmin.id, {"firstName": "X"}, headers=self.headers(self.superadmin))
        self.assertEqual(res.status_code, 200)

    def test_create_and_delete_require_admin(self):
        self.app.config["TESTING"] = False
        res = self.client().post('/users?userType=1', data=json.dumps(self.adminPayload()),
                                 content_type='application/json', headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 403)
        res = self.client().delete('/users/{}?userType=1'.format(self.admin.id),
                                   headers=self.headers(self.coordinator))
        self.assertEqual(res.status_code, 403)
        res = self.client().get('/users?userType=1')
        self.assertEqual(res.status_code, 401)

    # -- Borrado --

    def test_delete_admin(self):
        res = self.client().delete('/users/{}?userType=1'.format(self.admin.id))
        self.assertEqual(res.status_code, 200)
        self.admin.reload()
        self.assertTrue(self.admin.isDeleted)

    def test_delete_coordinator_with_project_is_blocked(self):
        self.createActiveSchoolYear()
        project = Project(coordinator=self.coordinator)
        project.save()
        res = self.client().delete('/users/{}?userType=2'.format(self.coordinator.id))
        self.assertEqual(res.status_code, 419)
        self.assertEqual(json.loads(res.data)['entity'], "Project")

    # -- Reenvío de correo de registro --

    def test_resend_email_coordinator(self):
        previous = self.coordinator.password
        res = self.client().post('/resend/email/coordinator/{}'.format(self.coordinator.id))
        self.assertEqual(res.status_code, 200)
        self.coordinator.reload()
        self.assertNotEqual(self.coordinator.password, previous)

    def test_resend_email_unknown_coordinator(self):
        res = self.client().post('/resend/email/coordinator/5f0000000000000000000000')
        self.assertEqual(res.status_code, 400)

    def test_resend_email_sponsor(self):
        res = self.client().post('/resend/email/sponsor', data=json.dumps({}),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 400)
        res = self.client().post('/resend/email/sponsor', data=json.dumps({"email": "nadie@test.com"}),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.createSponsor()
        res = self.client().post('/resend/email/sponsor', data=json.dumps({"email": "padrino@test.com"}),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 200)

    # -- Opciones públicas --

    def test_sponsor_and_school_options(self):
        self.createActiveSchoolYear()
        sponsor = self.createSponsor()
        school = self.createSchool()
        Project(coordinator=self.coordinator, school=school).save()

        res = self.client().get('/sponsors')
        self.assertEqual(json.loads(res.data)['records'], [{"id": str(sponsor.id), "name": "Empresa"}])
        res = self.client().get('/schools')
        self.assertEqual(json.loads(res.data)['records'], [{"id": str(school.id), "name": "Escuela 1"}])


if __name__ == "__main__":
    unittest.main()
