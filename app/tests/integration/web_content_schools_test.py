# app/test/integration/web_content_schools_test.py


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


class WebContentSchoolTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        self.schoolYear = SchoolYear(
            name="2020 - 2021",
            startDate="2020-09-14",
            endDate="2021-07-17")
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
            firstName="Coordinator 1",
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
            name="Sponsor 1",
            companyRif="303993833",
            companyType="2",
            companyPhone="02343432323",
            contactFirstName="Juan",
            contactLastName="Veriken",
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
            name="School 1",
            code="1",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Marlene",
            principalLastName="Mejia",
            principalEmail="testemail@test.com",
            principalPhone="04244664646",
            nTeachers=0,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=0,
            nGrades=0,
            nSections=0,
            schoolShift="1",
            email="someschoolemail@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
            coordinate={
                "type": "Point",
                "coordinates": [
                    8.60123,
                    -67.831185
                ]
            }
        )
        self.school.save()

        self.school2 = SchoolUser(
            name="School 2",
            code="2",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Marlene",
            principalLastName="Mejia",
            principalEmail="testemail@test.com",
            principalPhone="04244664646",
            nTeachers=0,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=0,
            nGrades=0,
            nSections=0,
            schoolShift="1",
            email="someschool2email@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
            coordinate={
                "type": "Point",
                "coordinates": [
                    8.68123,
                    -67.831185
                ]
            }
        )
        self.school2.save()

        self.school3 = SchoolUser(
            name="School 3",
            code="3",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Marlene",
            principalLastName="Mejia",
            principalEmail="testemail@test.com",
            principalPhone="04244664646",
            nTeachers=0,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=0,
            nGrades=0,
            nSections=0,
            schoolShift="1",
            email="someschool3email@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
            coordinate={
                "type": "Point",
                "coordinates": [
                    8.66123,
                    -67.831185
                ]
            }
        )
        self.school3.save()

        # create project
        self.project = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school,
            phase="2"
        )
        self.project.save()

        # create project 2
        self.project2 = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school2,
            phase="2"
        )
        self.project2.save()

        # create project 3
        self.project3 = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school3,
            phase="2"
        )
        self.project3.save()

    def test_web_content_school(self):

        # enroll school
        res = self.client().put(
            '/enrollment/{}'.format(self.project.id),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            '2020 - 2021', result['schoolYears'][0]['schoolYear']['name'])
        self.pecaProject = result['schoolYears'][0]['pecaId']

        # enroll school 2
        res = self.client().put(
            '/enrollment/{}'.format(self.project2.id),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # enroll school 3
        res = self.client().put(
            '/enrollment/{}'.format(self.project3.id),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # create teacher
        requestDataA = {
            "firstName": "Arelis",
            "lastName": "Crespo",
            "cardType": "1",
            "cardId": "20928888",
            "gender": "1",
            "email": "arelis@test.com",
            "phone": "04122222233",
            "addressState": str(self.state.pk),
            "addressMunicipality": str(self.municipality.pk),
            "address": "19th street",
            "addressCity": "Barquisimeto",
            "status": "1"
        }
        res = self.client().post(
            '/schools/teachers/{}'.format(self.school.pk),
            data=json.dumps(requestDataA),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        teacher = json.loads(res.data.decode('utf8').replace("'", '"'))

        # create section
        requestData = {
            "grade": "1",
            "name": "A",
            "teacher": teacher['id']
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        section = json.loads(res.data.decode('utf8').replace("'", '"'))

        # create student
        requestData = {
            "firstName": "Maria",
            "lastName": "Gonzalez",
            "birthdate": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ'),
            "gender": "1",
            "cardId": "20922842"
        }
        res = self.client().post(
            '/pecaprojects/students/{}/{}'.format(
                self.pecaProject, section['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        student = json.loads(res.data.decode('utf8').replace("'", '"'))

        # initial diagnostic
        requestData = {
            "wordsPerMin": 40
        }
        res = self.client().post(
            '/pecaprojects/diagnostics/reading/{}/{}/{}/{}'.format(
                "1",
                self.pecaProject,
                section['id'],
                student['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

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
            description="some description",
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

        # set data to ambleCoins in peca
        requestData = {
            "meetingDate": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ'),
            "elaborationDate": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
        }
        res = self.client().put(
            '/pecaprojects/amblecoins/{}/{}'.format(self.pecaProject, 2),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # annual convention
        requestData = dict(
            description="some description",
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

        # add student to olympics
        requestData = {
            "section": section['id'],
            "student": student['id'],
            "status": "2",  # classified
            "result": "1"  # gold medal
        }
        res = self.client().post(
            '/pecaprojects/olympics/{}/{}'.format(self.pecaProject, 1),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # custom activity
        requestData = dict(
            name="some name",
            description="some description",
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
        activity = json.loads(res.data.decode('utf8').replace("'", '"'))

        # update activity peca
        requestData = {
            "checklist": json.dumps([
                {
                    "id": activity['checklist'][0]['id'],
                    "name": activity['checklist'][0]['name'],
                    "checked": True
                }
            ]),
            "date": "2020-07-17T00:00:00.000Z",
            "uploadedFile": (io.BytesIO(
                b'hi everyone'), 'activityFile.pdf')
        }
        res = self.client().put(
            '/pecaprojects/activities/{}/{}/{}?userId={}'.format(
                self.pecaProject,
                3,
                activity['id'],
                self.coordinator.pk
            ),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        # environmental project
        requestData = {
            "name": "Some name",
            "description": "some description",
            "lapse1": {
                "generalObjective": "Some general objective",
                "topics": [
                    {
                        "name": "Some topic",
                        "objectives": [
                            "first one",
                            "second one"
                        ],
                        "strategies": [
                            "first one",
                            "second one"
                        ],
                        "contents": [
                            "first one",
                            "second one"
                        ],
                        "levels": [
                            {
                                "target": [
                                    {
                                        "label": "1",
                                        "value": True
                                    },
                                    {
                                        "label": "2",
                                        "value": True
                                    }
                                ],
                                "week": [
                                    "2020-04-20T18:45:33.108Z",
                                    "2020-04-25T18:45:33.108Z"
                                ],
                                "duration": "0100",
                                "techniques": [
                                    "first one",
                                    "second one"
                                ],
                                "activities": [
                                    {"name": "first one"},
                                    {"name": "second one"}
                                ],
                                "resources": [
                                    "first one",
                                    "second one"
                                ],
                                "evaluations": [
                                    "first one",
                                    "second one"
                                ],
                                "supportMaterial": [
                                    "https://somedomain.com/somefile",
                                    "https://somedomain.com/somefile"
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        res = self.client().post(
            '/pecasetting/environmentalproject',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # get available schools
        res = self.client().get(
            '/schoolspage'
        )
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(3, len(result['records']))

        # get web content
        res = self.client().get(
            '/schoolspage/{}_{}'.format(
                self.school.code, self.school.name.strip())
        )
        self.assertEqual(res.status_code, 200)
        school = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('Sponsor 1', school['sponsor'])
        self.assertEqual('Coordinator 1 Test', school['coordinator'])
        self.assertEqual('Iribarren, Lara, Venezuela', school['address'])
        self.assertEqual(1, school['nStudents'])

        self.assertEqual('2020 - 2021', school['diagnostics']['wordsPerMinIndex'][0]['label'])
        self.assertEqual(1, school['diagnostics']['wordsPerMinIndex'][0]['value'])
        self.assertEqual('Lapso 1', school['diagnostics']['wordsPerMinIndex'][0]['serie'])
        self.assertEqual([], school['diagnostics']['multiplicationsPerMinIndex'])
        self.assertEqual([], school['diagnostics']['operationsPerMinIndex'])

        self.assertEqual(1, school['olympicsSummary']['inscribed'])
        self.assertEqual(1, school['olympicsSummary']['classified'])
        self.assertEqual(1, school['olympicsSummary']['medalsGold'])
        self.assertEqual(0, school['olympicsSummary']['medalsSilver'])
        self.assertEqual(0, school['olympicsSummary']['medalsBronze'])

        self.assertEqual(5, len(school['activities']))

        self.assertEqual(2, len(school['nextActivities']))

        self.assertEqual(2, len(school['nearbySchools']))
        self.assertEqual('School 3', school['nearbySchools'][0]['name'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
