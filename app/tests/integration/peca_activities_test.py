# app/test/integration/peca_activities_test.py


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


class PecaActivitiesTest(unittest.TestCase):
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
                ]
            }

        )
        self.pecaProject.save()

    def test_activities_peca(self):
        ################################
        # create activities for lapse 1
        ################################

        requestData = dict(
            name="Activity test 1",
            hasText="true",
            hasDate="true",
            hasFile="true",
            hasVideo="true",
            hasChecklist="true",
            hasUpload="false",
            text="some text",
            file=(io.BytesIO(
                b'hi everyone'), 'activityFile.pdf'),
            video=json.dumps(
                {"name": "somename", "url": "https://youtube.com"}),
            checklist=json.dumps([{"name": "objectve 1"}]),
            approvalType="3",
            status="1"
        )
        res = self.client().post(
            '/pecasetting/activities/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        activity1Id = result['id']

        requestData = dict(
            name="Activity test 2",
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
            '/pecasetting/activities/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        activity2Id = result['id']

        requestData = dict(
            name="Activity test 3",
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
            approvalType="1",
            status="1"
        )
        res = self.client().post(
            '/pecasetting/activities/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        activity3Id = result['id']

        # check activity on peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('Activity test 1',
                         peca['lapse1']['activities'][0]['name'])
        self.assertEqual('Activity test 2',
                         peca['lapse1']['activities'][1]['name'])
        self.assertEqual('Activity test 3',
                         peca['lapse1']['activities'][2]['name'])

        #####################################
        # test activity with approval request
        #####################################

        # send approval request for activity 1
        requestData = {
            "checklist": json.dumps([
                {
                    "id": peca['lapse1']['activities'][0]['id'],
                    "name": peca['lapse1']['activities'][0]['name'],
                    "checked": True
                }
            ]),
            "date": "2020-07-17T00:00:00.000Z",
            "uploadedFile": (io.BytesIO(
                b'hi everyone'), 'activityFile.pdf')
        }
        res = self.client().put(
            '/pecaprojects/activities/{}/{}/{}?userId={}'.format(
                self.pecaProject.id,
                1,
                activity1Id,
                self.coordinator.pk
            ),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        request1 = json.loads(res.data.decode('utf8').replace("'", '"'))
        request1 = request1['approvalHistory'][0]

        # check activity history in peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('2',
                         peca['lapse1']['activities'][0]['status'])
        self.assertEqual('1',
                         peca['lapse1']['activities'][0]['approvalHistory'][0]['status'])

        # reject request 1
        requestData = {
            "status": "3"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(request1['id']),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        # check activity history in peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('1',
                         peca['lapse1']['activities'][0]['status'])
        self.assertEqual('3',
                         peca['lapse1']['activities'][0]['approvalHistory'][0]['status'])

        # send approval request2 for activity 1
        requestData = {
            "checklist": json.dumps([
                {
                    "id": peca['lapse1']['activities'][0]['id'],
                    "name": peca['lapse1']['activities'][0]['name'],
                    "checked": True
                }
            ]),
            "date": "2020-07-17T00:00:00.000Z",
            "uploadedFile": (io.BytesIO(
                b'hi everyone'), 'activityFile2.pdf')
        }
        res = self.client().put(
            '/pecaprojects/activities/{}/{}/{}?userId={}'.format(
                self.pecaProject.id,
                1,
                activity1Id,
                self.coordinator.pk
            ),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        request2 = json.loads(res.data.decode('utf8').replace("'", '"'))
        request2 = request2['approvalHistory'][1]
        # check activity history in peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))

        self.assertEqual('2',
                         peca['lapse1']['activities'][0]['status'])
        self.assertEqual('1',
                         peca['lapse1']['activities'][0]['approvalHistory'][1]['status'])
        self.assertEqual('activityFile2.pdf',
                         peca['lapse1']['activities'][0]['approvalHistory'][1]['detail']['uploadedFile']['name'])

        # accept request 2
        requestData = {
            "status": "2"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(request2['id']),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        # check activity history in peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('3',
                         peca['lapse1']['activities'][0]['status'])
        self.assertEqual('2',
                         peca['lapse1']['activities'][0]['approvalHistory'][1]['status'])

        #####################################
        # test activity only admin
        #####################################

        requestData = {
            "status": "3",
        }
        res = self.client().put(
            '/pecaprojects/activities/{}/{}/{}?userId={}'.format(
                self.pecaProject.pk,
                1,
                activity3Id,
                self.coordinator.pk
            ),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        # check activity
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('3',
                         peca['lapse1']['activities'][2]['status'])

        #####################################
        # test activity fill all fields
        #####################################

        requestData = {
            "status": "3",
        }
        requestData = {
            "checklist": json.dumps([
                {
                    "id": peca['lapse1']['activities'][0]['id'],
                    "name": peca['lapse1']['activities'][0]['name'],
                    "checked": True
                }
            ]),
            "date": "2020-07-17T00:00:00.000Z",
            "uploadedFile": (io.BytesIO(
                b'hi everyone'), 'activityFile.pdf')
        }
        res = self.client().put(
            '/pecaprojects/activities/{}/{}/{}?userId={}'.format(
                self.pecaProject.pk,
                1,
                activity2Id,
                self.coordinator.pk
            ),
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        # check activity history in peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        peca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('3',
                         peca['lapse1']['activities'][1]['status'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
