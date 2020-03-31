# app/tests/section_peca_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.peca_project_model import PecaProject
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.helpers.handler_seeds import create_standard_roles


class SchoolPecaTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-02-14",
            endDate="2020-09-14")
        self.schoolYear.save()

        create_standard_roles()

        self.state = State(
            name="Lara"
        )
        self.state.save()

        self.municipality = Municipality(
            state=self.state,
            name="Iribarren"
        )
        self.municipality.save()

        self.coordinator = CoordinatorUser(
            firstName="Test",
            lastName="Test",
            cardType="1",
            cardId="20922842",
            birthdate=datetime.utcnow(),
            gender="1",
            homePhone="02343432323",
            addressHome="House 34A",
            email="testemail@test.com",
            password="12345678",
            userType="2",
            phone="02322322323",
            role=Role.objects(devName="coordinator").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
            isReferred=False
        )
        self.coordinator.save()

        self.sponsor = SponsorUser(
            name="Test",
            companyRif="303993833",
            companyType="2",
            companyPhone="02343432323",
            contactFirstName="Danel",
            contactLastName="Ortega",
            contactPhone="04244664646",
            addressHome="House 34A",
            email="testemail@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="sponsor").first(),
            addressState=self.state,
            addressMunicipality=self.municipality
        )
        self.sponsor.save()

        self.school = SchoolUser(
            name="School",
            code="0002",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Danel",
            principalLastName="Ortega",
            principalEmail="testemail@test.com",
            principalPhone="04244664646",
            nTeachers=20,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=20,
            nGrades=20,
            nSections=20,
            schoolShift="1",
            email="someschoolemail@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality
        )
        self.school.save()

        # create project
        self.project = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school
        )
        self.project.save()

        # create peca project
        self.pecaProject = PecaProject(
            schoolYear=self.schoolYear,
            schoolYearName=self.schoolYear.name,
            project={
                "id": str(self.project.id),
                "code": str(self.project.code),
                "coordinator": {
                    "id": str(self.project.coordinator.id),
                    "name": self.project.coordinator.firstName + " " + self.project.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project.sponsor.id),
                    "name": self.project.sponsor.name
                },
                "school": {
                    "id": str(self.project.school.id),
                    "name": self.project.school.name
                }
            },
            school={
                "name": self.school.name,
                "code": self.school.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school.principalFirstName,
                "principalLastName": self.school.principalLastName,
                "principalEmail": self.school.principalEmail,
                "principalPhone": self.school.principalPhone,
                "nTeachers": self.school.nTeachers,
                "nGrades": self.school.nGrades,
                "nStudents": self.school.nStudents,
                "nAdministrativeStaff": self.school.nAdministrativeStaff,
                "nLaborStaff": self.school.nLaborStaff
            }

        )
        self.pecaProject.save()

    def test_create_section(self):

        requestData = {
            "grade": "1",
            "name": "A"
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("A",
                         result['name'])

        # create B
        requestData = {
            "grade": "1",
            "name": "B"
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("B",
                         result['name'])

        # create duplicated
        requestData = {
            "grade": "1",
            "name": "A"
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_update_section(self):

        # create A
        requestData = {
            "grade": "1",
            "name": "A"
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        resultA = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("A",
                         resultA['name'])

        # create B
        requestData = {
            "grade": "1",
            "name": "B"
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        resultB = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("B",
                         resultB['name'])

        # update A -> B (duplicated)
        requestData = {
            "grade": "1",
            "name": "B"
        }
        res = self.client().put(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, resultA['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # update A -> C (new)
        requestData = {
            "grade": "1",
            "name": "C"
        }
        res = self.client().put(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, resultA['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("C",
                         result['name'])

    def test_delete_section(self):

        # create A
        requestData = {
            "grade": "1",
            "name": "A"
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        resultA = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("A",
                         resultA['name'])

        # delete A
        res = self.client().delete(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, resultA['id']))
        self.assertEqual(res.status_code, 200)

        # delete A (Again)
        res = self.client().delete(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, resultA['id']))
        self.assertEqual(res.status_code, 404)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
