# app/test/integration/peca_olympics_report_test.py


import unittest
import json
from datetime import datetime
import io

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.peca_project_model import PecaProject, Lapse
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.helpers.handler_seeds import create_standard_roles
from app.models.peca_olympics_model import Student, Section


class PecaOlympicsTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-09-14",
            endDate="2021-07-14")
        self.schoolYear.initFirstPecaSetting()
        self.schoolYear.pecaSetting.lapse1.mathOlympic.status = "1"
        self.schoolYear.save()

        self.schoolYear2 = SchoolYear(
            name="Test",
            startDate="2021-09-14",
            endDate="2022-07-14")
        self.schoolYear2.initFirstPecaSetting()
        self.schoolYear2.pecaSetting.lapse1.mathOlympic.status = "1"
        self.schoolYear2.save()

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
                        "students": [
                            {
                                "firstName": "Ary",
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
                                "firstName": "Jesus",
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

        ).save()

        self.pecaProject.lapse1.olympics.students.append(
            Student(
                section=Section(
                    id=str(self.pecaProject.school.sections[0].id),
                    name=self.pecaProject.school.sections[0].name,
                    grade=self.pecaProject.school.sections[0].grade
                ),
                id=str(self.pecaProject.school.sections[0].students[0].id),
                name=self.pecaProject.school.sections[0].students[0].firstName,
                status="2",
                result="1"
            )
        )
        self.pecaProject.lapse1.olympics.students.append(
            Student(
                section=Section(
                    id=str(self.pecaProject.school.sections[0].id),
                    name=self.pecaProject.school.sections[0].name,
                    grade=self.pecaProject.school.sections[0].grade
                ),
                id=str(self.pecaProject.school.sections[0].students[1].id),
                name=self.pecaProject.school.sections[0].students[1].firstName,
                status="1",
                result=None
            )
        )
        self.pecaProject.lapse1.olympics.students.append(
            Student(
                section=Section(
                    id=str(self.pecaProject.school.sections[0].id),
                    name=self.pecaProject.school.sections[0].name,
                    grade=self.pecaProject.school.sections[0].grade
                ),
                id=str(self.pecaProject.school.sections[0].students[2].id),
                name=self.pecaProject.school.sections[0].students[2].firstName,
                status="2",
                result="3"
            )
        )
        self.pecaProject.save()

        # create peca project2
        self.pecaProject2 = PecaProject(
            schoolYear=self.schoolYear2,
            schoolYearName=self.schoolYear2.name,
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
                        "students": [
                            {
                                "firstName": "Maria",
                                "lastName": "Atencio",
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
                    },
                    {
                        "grade": "2",
                        "name": "A",
                        "students": [
                            {
                                "firstName": "Alejandra",
                                "lastName": "Atencio",
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
        ).save()
        self.pecaProject2.lapse1.olympics.students.append(
            Student(
                section=Section(
                    id=str(self.pecaProject2.school.sections[0].id),
                    name=self.pecaProject2.school.sections[0].name,
                    grade=self.pecaProject2.school.sections[0].grade
                ),
                id=str(self.pecaProject2.school.sections[0].students[0].id),
                name=self.pecaProject2.school.sections[0].students[0].firstName,
                status="2",
                result="1"
            )
        )
        self.pecaProject2.lapse1.olympics.students.append(
            Student(
                section=Section(
                    id=str(self.pecaProject2.school.sections[1].id),
                    name=self.pecaProject2.school.sections[1].name,
                    grade=self.pecaProject2.school.sections[1].grade
                ),
                id=str(self.pecaProject2.school.sections[1].students[0].id),
                name=self.pecaProject2.school.sections[1].students[0].firstName,
                status="2",
                result="1"
            )
        )
        self.pecaProject2.save()

    def test_olympics_report_peca(self):

        # sponsor
        res = self.client().get(
            '/statistics/olympicsreport/{}/{}'.format(
                self.schoolYear.id,
                self.schoolYear2.id
            ))
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(2,
                         len(result['allPeriods']))
        self.assertEqual(['2020', '2021'],
                         result['allPeriods'][0]['academicPeriod'])
        self.assertEqual(1,
                         len(result['allPeriods'][0]['schools']))
        self.assertEqual(
            {
                'name': 'School',
                'sponsor': 'Test',
                'coordinator': 'Test Test'
            },
            result['allPeriods'][0]['schools'][0]['meta'])
        self.assertEqual(
            1,
            len(result['allPeriods'][0]['schools'][0]['grades']))
        self.assertEqual(
            "1",
            result['allPeriods'][0]['schools'][0]['grades'][0]['name'])
        self.assertEqual(
            1,
            len(result['allPeriods'][0]['schools'][0]['grades'][0]['sections']))
        self.assertEqual(
            {
                'name': 'A',
                'inscribed': 3,
                'classified': 2,
                'medalsGold': 1,
                'medalsSilver': 0,
                'medalsBronze': 1
            },
            result['allPeriods'][0]['schools'][0]['grades'][0]['sections'][0])
        self.assertEqual(
            {
                'name': 'A',
                'inscribed': 1,
                'classified': 1,
                'medalsGold': 1,
                'medalsSilver': 0,
                'medalsBronze': 0
            },
            result['allPeriods'][1]['schools'][0]['grades'][0]['sections'][0]
        )
        self.assertEqual(
            {

                'totalEnrolled': 3,
                'totalClassified': 2,
                'totalGoldMedals': 1,
                'totalSilverMedals': 0,
                'totalBronzeMedals': 1,

            },
            result['allPeriods'][0]['schools'][0]['total']
        )
        self.assertEqual(
            {

                'enrolledStudents': 5,
                'classifiedStudents': 4,
                'studentsGoldMedal': 3,
                'studentsSilverMedal': 0,
                'studentsBronzeMedal': 1

            },
            result['finalScore']
        )

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
