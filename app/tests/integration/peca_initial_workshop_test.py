# app/test/integration/peca_initial_workshop_test.py


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


class PecaInitialWorkshopTest(unittest.TestCase):
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

    def test_initial_workshop_peca(self):
        """# enable initial workshop for lapse1
        requestData = dict(
            agreementFile=(io.BytesIO(b'hi everyone'), 'agreementFile.pdf'),
            agreementDescription="Some description",
            planningMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'planningMeetingFile.pdf'),
            planningMeetingDescription="Some description",
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description"
        )
        # lapse 1
        res = self.client().post(
            '/pecasetting/initialworkshop/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)"""

        requestData = {
            "id": 'initialWorkshop',
            "lapse": "1",
            "isStandard": True,
            "status": "1"
        }
        res = self.client().post(
            '/pecasetting/activities',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check initial workshop on peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertIsNotNone(
            result['lapse1']['initialWorkshop'])

        # update planning data initial workshop in peca
        requestData = {
            "workshopPlace": "Some place",
            "workshopDate": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ'),
        }
        res = self.client().post(
            '/pecaprojects/initialworkshop/{}/{}?userId={}'.format(
                self.pecaProject.id, 1, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        resultPeca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('Some place',
                         resultPeca['lapse1']['initialWorkshop']['workshopPlace'])

        # update data initial workshop in peca
        requestData = {
            "description": "new description",
            "images": [
                {
                    "image": test_image,
                    "description": "some image description",
                    "status": "1"
                },
                {
                    "image": test_image,
                    "description": "some image2 description",
                    "status": "1"
                }
            ]
        }
        res = self.client().post(
            '/pecaprojects/initialworkshop/{}/{}?userId={}'.format(
                self.pecaProject.id, 1, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        resultPeca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('some image2 description',
                         resultPeca['lapse1']['initialWorkshop']['approvalHistory'][0]['detail']['images'][1]['description'])

        # send with pending approval
        res = self.client().post(
            '/pecaprojects/initialworkshop/{}/{}?userId={}'.format(
                self.pecaProject.id, 1, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)

        """# edit initialWorkshop
        requestData = dict(
            agreementFile=(io.BytesIO(b'hi everyone'), 'agreementFile.pdf'),
            agreementDescription="Some edited description",
            planningMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'planningMeetingFile.pdf'),
            planningMeetingDescription="Some description",
            teachersMeetingFile=(io.BytesIO(b'hi everyone'),
                                 'teachersMeetingFile.pdf'),
            teachersMeetingDescription="Some description"
        )

        res = self.client().post(
            '/pecasetting/initialworkshop/1',
            data=requestData,
            content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)

        # check peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        resultPeca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual('Some edited description',
                         resultPeca['lapse1']['initialWorkshop']['agreementDescription'])
        self.assertEqual(None, resultPeca['lapse1']
                         ['initialWorkshop']['description'])
        """

        # approve request
        requestData = {
            "status": "2"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(
                resultPeca['lapse1']['initialWorkshop']['approvalHistory'][0]['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        resultPeca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            "new description", resultPeca['lapse1']['initialWorkshop']['description'])

        # cancel request
        requestData = {
            "description": "new description",
            "images": [
                {
                    "image": test_image,
                    "description": "some image description",
                    "status": "1"
                },
                {
                    "image": test_image,
                    "description": "some image2 description",
                    "status": "1"
                }
            ]
        }
        res = self.client().post(
            '/pecaprojects/initialworkshop/{}/{}?userId={}'.format(
                self.pecaProject.id, 1, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        resultPeca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(True,
                         resultPeca['lapse1']['initialWorkshop']['isInApproval'])

        # cancel
        requestData = {
            "status": "4"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(
                resultPeca['lapse1']['initialWorkshop']['approvalHistory'][1]['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        resultPeca = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(False,
                         resultPeca['lapse1']['initialWorkshop']['isInApproval'])
        self.assertEqual("4",
                         resultPeca['lapse1']['initialWorkshop']['approvalHistory'][1]['status'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
