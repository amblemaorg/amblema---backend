# app/tests/diagnostic_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear, PecaSetting, GoalSetting, GradeSetting
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.peca_project_model import PecaProject
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.helpers.handler_seeds import create_standard_roles


class DiagnosticTest(unittest.TestCase):
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
            endDate="2020-09-14"
        )
        self.schoolYear.initFirstPecaSetting()
        self.schoolYear.pecaSetting.goalSetting.grade1.wordsPerMin = 70
        self.schoolYear.pecaSetting.goalSetting.grade1.operationsPerMin = 30
        self.schoolYear.pecaSetting.goalSetting.grade1.multiplicationsPerMin = 40
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
                "nLaborStaff": self.school.nLaborStaff,
                "sections": [
                    {
                        "grade": "1",
                        "name": "A",
                        "goals": {
                            "wordsPerMin": 70,
                            "operationsPerMin": 30,
                            "multiplicationsPerMin": 40
                        },
                        "students": [
                            {
                                "firstName": "Danel",
                                "lastName": "Rodriguez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                }
                            },
                            {
                                "firstName": "Eilen",
                                "lastName": "Rodriguez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                }
                            }
                        ],
                        "teacher": {
                            "firstName": "Maria",
                            "lastName": "Teran"
                        }
                    }
                ]
            }

        )
        self.pecaProject.save()

    def test_reading_diagnostics(self):

        requestData = {
            "wordsPerMin": 70
        }
        res = self.client().post(
            '/pecaprojects/diagnostics/reading/{}/{}/{}/{}'.format(
                "1",
                self.pecaProject.id,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[0].id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(70,
                         result['student']['wordsPerMin'])
        self.assertEqual('1.00',
                         result['student']['wordsPerMinIndex'])
        self.pecaProject.reload()
        self.assertEqual(
            70, self.pecaProject.school.sections[0].students[0].lapse1.wordsPerMin)
        self.assertEqual(
            1, self.pecaProject.school.sections[0].students[0].lapse1.wordsPerMinIndex)
        self.assertEqual(
            0, self.pecaProject.school.sections[0].diagnostics.lapse1.operationsPerMinIndex)

        self.schoolYear.reload()
        self.assertEqual(
            1, self.schoolYear.diagnostics.lapse1.wordsPerMinIndex)
        self.assertEqual(
            0, self.schoolYear.diagnostics.lapse1.operationsPerMinIndex)
        self.assertEqual(
            0, self.schoolYear.diagnostics.lapse1.multiplicationsPerMinIndex)

        # delete
        res = self.client().delete(
            '/pecaprojects/diagnostics/reading/{}/{}/{}/{}'.format(
                "1",
                self.pecaProject.id,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[0].id))
        self.assertEqual(res.status_code, 200)

        self.pecaProject = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(
            None, self.pecaProject.school.sections[0].students[0].lapse1.wordsPerMin)
        self.assertEqual(
            None, self.pecaProject.school.sections[0].students[0].lapse1.wordsPerMinIndex)
        self.schoolYear.reload()
        self.assertEqual(
            0, self.schoolYear.diagnostics.lapse1.wordsPerMinIndex)
        self.assertEqual(
            0, self.schoolYear.diagnostics.lapse1.operationsPerMinIndex)
        self.assertEqual(
            0, self.schoolYear.diagnostics.lapse1.multiplicationsPerMinIndex)

    def test_math_diagnostics(self):

        requestData = {
            "multiplicationsPerMin": 80,
            "operationsPerMin": 15
        }

        res = self.client().post(
            '/pecaprojects/diagnostics/math/{}/{}/{}/{}'.format(
                "1",
                self.pecaProject.id,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[1].id),
            data=json.dumps(requestData),
            content_type='application/json')

        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))

        self.assertEqual(15,
                         result['student']['operationsPerMin'])
        self.assertEqual('0.50',
                         result['student']['operationsPerMinIndex'])

        self.assertEqual(80,
                         result['student']['multiplicationsPerMin'])
        self.assertEqual('2.00',
                         result['student']['multiplicationsPerMinIndex'])
        self.pecaProject = PecaProject.objects.get(id=self.pecaProject.id)

        self.assertEqual(
            15, self.pecaProject.school.sections[0].students[1].lapse1.operationsPerMin)
        self.assertEqual(
            0.5, self.pecaProject.school.sections[0].students[1].lapse1.operationsPerMinIndex)
        self.assertEqual(
            80, self.pecaProject.school.sections[0].students[1].lapse1.multiplicationsPerMin)
        self.assertEqual(
            2, self.pecaProject.school.sections[0].students[1].lapse1.multiplicationsPerMinIndex)

        # delete
        res = self.client().delete(
            '/pecaprojects/diagnostics/math/{}/{}/{}/{}'.format(
                "1",
                self.pecaProject.id,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[1].id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        self.pecaProject = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(
            None, self.pecaProject.school.sections[0].students[1].lapse1.multiplicationsPerMin)
        self.assertEqual(
            None, self.pecaProject.school.sections[0].students[1].lapse1.multiplicationsPerMinIndex)
        self.assertEqual(
            None, self.pecaProject.school.sections[0].students[1].lapse1.operationsPerMin)
        self.assertEqual(
            None, self.pecaProject.school.sections[0].students[1].lapse1.operationsPerMinIndex)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
