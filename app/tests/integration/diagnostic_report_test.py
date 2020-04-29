# app/tests/diagnostic_report_test.py


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
                        "name": "B",
                        "students": [
                            {
                                "firstName": "Danel",
                                "lastName": "Rodriguez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": 40,
                                    "multiplicationsPerMinIndex": 40/40,
                                    "operationsPerMin": 30,
                                    "operationsPerMinIndex": 30/30,
                                    "wordsPerMin": 70,
                                    "wordsPerMinIndex": 70/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": 45,
                                    "multiplicationsPerMinIndex": 45/40,
                                    "operationsPerMin": 35,
                                    "operationsPerMinIndex": 35/30,
                                    "wordsPerMin": 75,
                                    "wordsPerMinIndex": 75/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": 50,
                                    "multiplicationsPerMinIndex": 50/40,
                                    "operationsPerMin": 40,
                                    "operationsPerMinIndex": 40/30,
                                    "wordsPerMin": 80,
                                    "wordsPerMinIndex": 80/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                }
                            },
                            {
                                "firstName": "Eilen",
                                "lastName": "Rodriguez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": 40,
                                    "multiplicationsPerMinIndex": 40/40,
                                    "operationsPerMin": 30,
                                    "operationsPerMinIndex": 30/30,
                                    "wordsPerMin": 70,
                                    "wordsPerMinIndex": 70/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": 60,
                                    "multiplicationsPerMinIndex": 60/40,
                                    "operationsPerMin": 50,
                                    "operationsPerMinIndex": 50/30,
                                    "wordsPerMin": 90,
                                    "wordsPerMinIndex": 90/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": 80,
                                    "multiplicationsPerMinIndex": 80/40,
                                    "operationsPerMin": 70,
                                    "operationsPerMinIndex": 70/30,
                                    "wordsPerMin": 110,
                                    "wordsPerMinIndex": 110/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                }
                            }
                        ],
                        "teacher": {
                            "firstName": "Maria",
                            "lastName": "Teran"
                        }
                    },
                    {
                        "grade": "1",
                        "name": "A",
                        "students": [
                            {
                                "firstName": "Ariannys",
                                "lastName": "Rodriguez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": 80,
                                    "multiplicationsPerMinIndex": 80/40,
                                    "operationsPerMin": 80,
                                    "operationsPerMinIndex": 80/30,
                                    "wordsPerMin": 80,
                                    "wordsPerMinIndex": 80/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": 80,
                                    "multiplicationsPerMinIndex": 80/40,
                                    "operationsPerMin": 80,
                                    "operationsPerMinIndex": 80/30,
                                    "wordsPerMin": 80,
                                    "wordsPerMinIndex": 80/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": 80,
                                    "multiplicationsPerMinIndex": 80/40,
                                    "operationsPerMin": 80,
                                    "operationsPerMinIndex": 80/30,
                                    "wordsPerMin": 80,
                                    "wordsPerMinIndex": 80/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                }
                            },
                            {
                                "firstName": "Elvis",
                                "lastName": "Presley",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": 20,
                                    "multiplicationsPerMinIndex": 20/40,
                                    "operationsPerMin": 20,
                                    "operationsPerMinIndex": 20/30,
                                    "wordsPerMin": 20,
                                    "wordsPerMinIndex": 20/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": 20,
                                    "multiplicationsPerMinIndex": 20/40,
                                    "operationsPerMin": 20,
                                    "operationsPerMinIndex": 20/30,
                                    "wordsPerMin": 20,
                                    "wordsPerMinIndex": 20/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": 25,
                                    "multiplicationsPerMinIndex": 25/40,
                                    "operationsPerMin": 25,
                                    "operationsPerMinIndex": 25/30,
                                    "wordsPerMin": 25,
                                    "wordsPerMinIndex": 25/70,
                                    "readingDate": datetime.utcnow(),
                                    "mathDate": datetime.utcnow()
                                }
                            }
                        ],
                        "teacher": {
                            "firstName": "Maria",
                            "lastName": "Fernandez"
                        }
                    }
                ]
            }

        )
        self.pecaProject.save()

    def test_diagnostic_report(self):

        res = self.client().get(
            '/statistics/diagnosticsreport/{}/{}?diagnostics=math,reading,logic'.format(
                self.schoolYear.id,
                self.pecaProject.project.school.id))
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('A', result['sections'][0]['name'])
        self.assertEqual(True, result['sections']
                         [0]['sectionSummaryAvailable'])
        self.assertEqual(True, result['sections']
                         [0]['sectionSummaryAvailable'])
        self.assertEqual(2, result['sections']
                         [0]['enrollment'])
        self.assertEqual(50, result['sections']
                         [0]['lapse1']['reading']['overGoalAverage'])
        self.assertEqual(0, result['sections']
                         [1]['lapse1']['reading']['overGoalAverage'])
        self.assertEqual(round((100/70)/2, 2),
                         round(result['sections']
                               [0]['lapse1']['reading']['indexAverage'], 2))
        self.assertEqual(50,
                         round(result['sections']
                               [0]['lapse1']['reading']['resultAverage'], 2))
        self.assertEqual(66.67,
                         round(result['yearSummary']
                               ['reading']['totalResultAverage'], 2))
        self.assertEqual(15.54,
                         round(result['yearSummary']
                               ['reading']['improvementPercentageAverage'], 2))
        self.assertEqual(1,
                         result['yearSummary']
                               ['reading']['sections'][0]['lapse3']['overGoalStudents'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
