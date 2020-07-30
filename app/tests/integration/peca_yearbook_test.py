# app/test/integration/peca_yearbook_test.py


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
from resources.images import test_image
from app.models.peca_yearbook_model import Entity


class PecaYearbookTest(unittest.TestCase):
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
        self.schoolYear.initFirstPecaSetting()
        self.schoolYear.pecaSetting.goalSetting.grade1.multiplicationsPerMin = 20
        self.schoolYear.pecaSetting.goalSetting.grade1.operationsPerMin = 30
        self.schoolYear.pecaSetting.goalSetting.grade1.wordsPerMin = 40

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
            addressMunicipality=self.municipality,
            yearbook=Entity(
                name="School",
                image="https://someimage.jpg",
                content="this is my yearbook content"
            )
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
                            "multiplicationsPerMin": 20,
                            "operationsPerMin": 30,
                            "wordsPerMin": 40
                        },
                        "students": [
                            {
                                "firstName": "Victoria",
                                "lastName": "Gonzalez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": 20,
                                    "multiplicationsPerMinIndex": 1,
                                    "operationsPerMin": 30,
                                    "operationsPerMinIndex": 1,
                                    "wordsPerMin": 40,
                                    "wordsPerMinIndex": 1
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
                                "firstName": "Alejandra",
                                "lastName": "Gonzalez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": 10,
                                    "multiplicationsPerMinIndex": 0.5,
                                    "operationsPerMin": 20,
                                    "operationsPerMinIndex": 0.6667,
                                    "wordsPerMin": 30,
                                    "wordsPerMinIndex": 0.75
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
        for section in self.pecaProject.school.sections:
            section.refreshDiagnosticsSummary()
        self.pecaProject.save()

    def test_yearbook_peca(self):

        # lapse planning
        requestData = dict(
            proposalFundationFile=(io.BytesIO(
                b'hi everyone'), 'proposalFundationFile.pdf'),
            proposalFundationDescription="Some description",
            meetingDescription="Some description"
        )
        res = self.client().post(
            '/pecasetting/lapseplanning/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        requestData = {
            "id": 'lapsePlanning',
            "lapse": "1",
            "isStandard": True,
            "status": "1"
        }
        res = self.client().post(
            '/pecasetting/activities',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # amblecoins
        requestData = dict(
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description",
            piggyBankDescription="Some description",
            piggyBankSlider=json.dumps(
                [{"image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                  "description": "some description"}]
            )
        )
        res = self.client().post(
            '/pecasetting/amblecoins/2',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        requestData = {
            "id": 'ambleCoins',
            "lapse": "2",
            "isStandard": True,
            "status": "1"
        }
        res = self.client().post(
            '/pecasetting/activities',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # annual convention
        requestData = dict(
            checklist='[{"name": "some description1"},{"name": "some description2"}]'
        )
        res = self.client().post(
            '/pecasetting/annualconvention/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        requestData = {
            "id": 'annualConvention',
            "lapse": "1",
            "isStandard": True,
            "status": "1"
        }
        res = self.client().post(
            '/pecasetting/activities',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # math olympics
        requestData = dict(
            file=(io.BytesIO(b'hi everyone'),
                  'olympicsFile.pdf'),
            description="Some description"
        )
        res = self.client().put(
            '/pecasetting/activities/matholympic/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        requestData = {
            "id": 'mathOlympic',
            "lapse": "1",
            "isStandard": True,
            "status": "1"
        }
        res = self.client().post(
            '/pecasetting/activities',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # custom activity
        requestData = dict(
            name="some name",
            hasText="true",
            hasDate="true",
            hasFile="true",
            hasVideo="true",
            hasChecklist="true",
            hasUpload="true",
            text="some text",
            file=(io.BytesIO(
                b'hi everyone'), 'activityFile.pdf'),
            video=json.dumps(
                {"name": "somename", "url": "https://youtube.com"}),
            checklist=json.dumps([{"name": "objectve 1"}]),
            approvalType="2",
            status="1"
        )
        res = self.client().post(
            '/pecasetting/activities/3',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        customActivity = json.loads(res.data.decode('utf8').replace("'", '"'))

        # check yearbook on peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            {
                "name": None,
                "content": None,
                "image": None
            }, result['yearbook']['historicalReview'])
        self.assertEqual(
            {
                "name": "Test",
                "content": None,
                "image": None
            }, result['yearbook']['sponsor'])
        self.assertEqual(
            {
                "name": "Test Test",
                "content": None,
                "image": None
            }, result['yearbook']['coordinator'])
        self.assertEqual(
            {
                "name": "School",
                "content": "this is my yearbook content",
                "image": None
            }, result['yearbook']['school'])
        self.assertEqual(
            result['yearbook']['lapse1']['diagnosticSummary'],
            [{
                "grade": "1",
                "name": "A",
                "multiplicationsPerMin": 15,
                "multiplicationsPerMinIndex": 0.75,
                "operationsPerMin": 25,
                "operationsPerMinIndex": 0.835,
                "wordsPerMin": 35,
                "wordsPerMinIndex": 0.875
            }])
        self.assertEqual(
            result['yearbook']['lapse1']['activities'],
            [
                {
                    "id": "lapsePlanning",
                    "name": "Planificación de lapso",
                    "description": None,
                    "images": []
                },
                {
                    "id": "annualConvention",
                    "name": "Convención anual",
                    "description": None,
                    "images": []
                },
                {
                    "id": "olympics",
                    "name": "Olimpiadas matemáticas",
                    "description": None,
                    "images": [
                    ]
                }
            ]
        )
        self.assertEqual(
            result['yearbook']['lapse2']['diagnosticSummary'],
            [
                {
                    "grade": "1",
                    "name": "A",
                    "multiplicationsPerMin": 0,
                    "multiplicationsPerMinIndex": 0,
                    "operationsPerMin": 0,
                    "operationsPerMinIndex": 0,
                    "wordsPerMin": 0,
                    "wordsPerMinIndex": 0
                }
            ])
        self.assertEqual(
            result['yearbook']['lapse2']['activities'],
            [
                {
                    "id": "ambleCoins",
                    "name": "AmbLeMonedas",
                    "description": None,
                    "images": []
                }
            ]
        )
        self.assertEqual(
            result['yearbook']['lapse3']['diagnosticSummary'],
            [
                {
                    "grade": "1",
                    "name": "A",
                    "multiplicationsPerMin": 0,
                    "multiplicationsPerMinIndex": 0.0,
                    "operationsPerMin": 0,
                    "operationsPerMinIndex": 0.0,
                    "wordsPerMin": 0,
                    "wordsPerMinIndex": 0.0
                }
            ])
        self.assertEqual(
            result['yearbook']['lapse3']['activities'],
            [
                {
                    "id": customActivity['id'],
                    "name": "some name",
                    "description": None,
                    "images": []
                }
            ]
        )

        # send yearbook request approval
        requestData = {
            "historicalReview": {
                "content": "historical review content",
                "image": test_image
            },
            "sponsor": {
                "name": "Test",
                "content": "sponsor content",
                "image": test_image
            },
            "coordinator": {
                "name": "Test Test",
                "content": "coordinator content",
                "image": test_image
            },
            "school": {
                "name": "School",
                "content": "school content",
                "image": test_image
            },
            "lapse1": {
                "activities": [
                    {
                        "id": "lapsePlanning",
                        "name": "Planificación de lapso",
                        "description": "some description",
                        "images": [test_image]
                    },
                    {
                        "id": "annualConvention",
                        "name": "Convención anual",
                        "description": "",
                        "images": [test_image]
                    },
                    {
                        "id": "mathOlympic",
                        "name": "Olimpiadas matemáticas",
                        "description": "",
                        "images": [test_image]
                    }
                ],
                "diagnosticAnalysis": "some resume"
            },
            "lapse2": {
                "activities": [
                    {
                        "id": "ambleCoins",
                        "name": "AmbLeMonedas",
                        "description": "",
                        "images": [test_image]
                    }
                ]
            },
            "lapse3": {
                "activities": [
                    {
                        "id": customActivity['id'],
                        "name": "some name",
                        "description": "",
                        "images": [test_image]
                    }
                ]
            },
            "sections": [
                {'id': str(section.id), 'image': test_image} for section in self.pecaProject.school.sections
            ]
        }

        res = self.client().post(
            '/pecaprojects/yearbook/{}?userId={}'.format(
                self.pecaProject.id, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(str(self.coordinator.id),
                         result['approvalHistory'][0]['user']['id'])

        # send with pending approval
        res = self.client().post(
            '/pecaprojects/yearbook/{}?userId={}'.format(
                self.pecaProject.id, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # check yearbook on approval history peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            "historical review content",
            result['yearbook']['approvalHistory'][0]['detail']['historicalReview']['content'])
        self.assertEqual(
            "sponsor content",
            result['yearbook']['approvalHistory'][0]['detail']['sponsor']['content'])
        self.assertEqual(
            "coordinator content",
            result['yearbook']['approvalHistory'][0]['detail']['coordinator']['content'])
        self.assertEqual(
            "school content",
            result['yearbook']['approvalHistory'][0]['detail']['school']['content'])
        self.assertEqual(
            'some description',
            result['yearbook']['approvalHistory'][0]['detail']['lapse1']['activities'][0]['description'])
        self.assertEqual(
            'some resume', result['yearbook']['approvalHistory'][0]['detail']['lapse1']['diagnosticAnalysis'])
        self.assertEqual(
            'A', result['yearbook']['approvalHistory'][0]['detail']['sections'][0]['name'])

        # approve request
        requestData = {
            "status": "2"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(
                result['yearbook']['approvalHistory'][0]['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check yearbook on peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            "historical review content",
            result['yearbook']['historicalReview']['content'])
        self.assertEqual(
            "sponsor content",
            result['yearbook']['sponsor']['content'])
        self.assertEqual(
            "coordinator content",
            result['yearbook']['coordinator']['content'])
        self.assertEqual(
            "school content",
            result['yearbook']['school']['content'])
        self.assertEqual(
            'some description',
            result['yearbook']['lapse1']['activities'][0]['description'])

        school = SchoolUser.objects(id=self.school.id).first()
        self.assertEqual(
            'school content',
            school.yearbook.content)

        self.pecaProject.reload()
        self.assertIsNotNone(self.pecaProject.school.sections[0].image)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
