# app/tests/integration/request_find_school_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.request_find_school_model import RequestFindSchool
from app.models.request_find_sponsor_model import RequestFindSponsor
from app.models.request_find_coordinator_model import RequestFindCoordinator
from app.helpers.handler_seeds import create_standard_roles, create_initial_steps


class ApprovalProcess(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        create_standard_roles()

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-02-14",
            endDate="2020-09-14")
        self.schoolYear.save()

        create_initial_steps()

        self.role = Role(name="test")
        self.role.save()

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
            role=self.role,
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

        self.project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        self.project.save()

    def test_endpoint_create_request_find_coordinator(self):

        requestData = {
            "project": str(self.project.pk),
            "user": str(self.sponsor.pk),
            "firstName": "Coordinator",
            "lastName": "Last Name",
            "name": "hola",
            "cardType": "1",
            "cardId": "20922842",
            "birthdate": str(datetime.utcnow()),
            "gender": "1",
            "addressState": str(self.state.pk),
            "addressMunicipality": str(self.municipality.pk),
            "addressCity": "Barquisimeto",
            "address": "calle 9 entre 1 y 2",
            "addressHome": "casa 20-2",
            "email": "coordinator@test.com",
            "phone": "04144433434",
            "homePhone": "02524433434",
            "profession": "Teacher"
        }
        res = self.client().post(
            '/requestsfindcoordinator',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_endpoint_create_request_find_sponsor(self):

        data = dict(
            project=str(self.project.pk),
            user=str(self.coordinator.pk),
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            companyPhone="02524433434",
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk),
            addressCity="Barquisimeto",
            address="calle 9 entre 1 y 2",
            contactFirstName="Contact FirstName",
            contactLastName="Contact Lastname",
            contactPhone="04242772727"
        )

        res = self.client().post(
            '/requestsfindsponsor',
            data=json.dumps(data),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_endpoint_create_request_find_school(self):

        data = dict(
            project=str(self.project.pk),
            user=str(self.sponsor.pk),
            name="U.E. Libertador",
            code="315",
            email="uelibertador@test.com",
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk),
            addressCity="Barquisimeto",
            address="calle 9 entre 1 y 2",
            phone="02524433434",
            schoolType="1",
            principalFirstName="Marlene",
            principalLastName="Mejia",
            principalEmail="mmejia@test.com",
            principalPhone="04242772727",
            subPrincipalFirstName="Nelly",
            subPrincipalLastName="Velazquez",
            subPrincipalEmail="nvelazquez@test.com",
            subPrincipalPhone="04244545454",
            nTeachers=22,
            nAdministrativeStaff=10,
            nLaborStaff=3,
            nStudents=500,
            nGrades=6,
            nSections=18,
            schoolShift="3"
        )

        res = self.client().post(
            '/requestsfindschool',
            data=json.dumps(data),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_create_school_user_on_approve_request(self):

        reciprocalFields = [
            'coordinatorFillSchoolForm',
            'sponsorFillSchoolForm'
        ]
        request = RequestFindSchool(
            project=self.project,
            user=self.sponsor,
            name="U.E. Libertador",
            code="315",
            email="uelibertador@test.com",
            addressState=self.state,
            addressMunicipality=self.municipality,
            addressCity="Barquisimeto",
            addressZoneType="2",
            addressZone="Barrio Bolivar",
            address="calle 9 entre 1 y 2",
            coordinate={
                "type": "Point",
                "coordinates": [
                    10.0118875,
                    -69.4665246
                ]
            },
            phone="02524433434",
            schoolType="1",
            principalFirstName="Marlene",
            principalLastName="Mejia",
            principalEmail="mmejia@test.com",
            principalPhone="04242772727",
            subPrincipalFirstName="Nelly",
            subPrincipalLastName="Velazquez",
            subPrincipalEmail="nvelazquez@test.com",
            subPrincipalPhone="04244545454",
            nTeachers=22,
            nAdministrativeStaff=10,
            nLaborStaff=3,
            nStudents=500,
            nGrades=6,
            nSections=18,
            schoolShift="3"
        )
        request.save()

        schoolUser = SchoolUser.objects(email=request.email).first()
        self.assertEqual(None, schoolUser)

        self.project = Project.objects.get(id=self.project.id)
        for step in self.project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                self.assertEqual("1", step.approvalHistory[0].status)
                self.assertEqual(
                    request.name, step.approvalHistory[0].data['name'])

        res = self.client().get(
            '/projects/{}'.format(self.project.id))
        result = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        for step in result['stepsProgress']['steps']:
            if step['devName'] in reciprocalFields:
                self.assertEqual("1", step['approvalHistory'][0]['status'])
                self.assertEqual(
                    request.name, step['approvalHistory'][0]['data']['name'])

        # once request is approved must create a schoolUser
        # and assign it to project
        request.status = "2"
        request.save()

        schoolUser = SchoolUser.objects(email=request.email).first()
        self.assertEqual(request.email, schoolUser.email)

        self.project = Project.objects.get(id=self.project.id)
        self.assertEqual(self.project.school, schoolUser)

        for step in self.project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                self.assertEqual("2", step.approvalHistory[0].status)

        # test request with duplicate school code
        reqData = dict(
            project=str(self.project.pk),
            user=str(self.sponsor.pk),
            name="U.E. Libertador",
            code="315",
            email="uelibertador@test.com",
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk),
            addressCity="Barquisimeto",
            addressZoneType="2",
            addressZone="Barrio Bolivar",
            address="calle 9 entre 1 y 2",
            phone="02524433434",
            schoolType="1",
            principalFirstName="Marlene",
            principalLastName="Mejia",
            principalEmail="mmejia@test.com",
            principalPhone="04242772727",
            subPrincipalFirstName="Nelly",
            subPrincipalLastName="Velazquez",
            subPrincipalEmail="nvelazquez@test.com",
            subPrincipalPhone="04244545454",
            nTeachers=22,
            nAdministrativeStaff=10,
            nLaborStaff=3,
            nStudents=500,
            nGrades=6,
            nSections=18,
            schoolShift="3"
        )
        res = self.client().post(
            '/requestsfindschool',
            data=json.dumps(reqData),
            content_type='application/json')
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            {'code': [{'msg': 'Duplicated school code', 'status': '5'}]}, json_res)

    def test_create_sponsor_user_on_approve_request(self):

        reciprocalFields = [
            'coordinatorFillSponsorForm',
            'schoolFillSponsorForm'
        ]

        request = RequestFindSponsor(
            project=self.project,
            user=self.coordinator,
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            companyPhone="02524433434",
            addressState=self.state,
            addressMunicipality=self.municipality,
            addressCity="Barquisimeto",
            address="calle 9 entre 1 y 2",
            contactFirstName="Contact",
            contactLastName="Name",
            contactPhone="04242772727"
        )
        request.save()

        sponsorUser = SponsorUser.objects(email=request.email).first()
        self.assertEqual(None, sponsorUser)

        self.project = Project.objects.get(id=self.project.id)
        for step in self.project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                self.assertEqual("1", step.approvalHistory[0].status)
                self.assertEqual(
                    request.name, step.approvalHistory[0].data['name'])

        # once request is approved must create a sponsorUser
        # and assign it to project
        request.status = "2"
        request.save()

        sponsorUser = SponsorUser.objects(email=request.email).first()
        self.assertEqual(request.email, sponsorUser.email)

        self.project = Project.objects.get(id=self.project.id)
        self.assertEqual(self.project.sponsor, sponsorUser)

        for step in self.project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                self.assertEqual("2", step.approvalHistory[0].status)

    def test_create_coordinator_user_on_approve_request(self):

        reciprocalFields = [
            'schoolFillCoordinatorForm',
            'sponsorFillCoordinatorForm'
        ]
        sponsor = SponsorUser(
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
            role=self.role,
            addressState=self.state,
            addressMunicipality=self.municipality
        )
        sponsor.save()

        project = Project(
            schoolYear=self.schoolYear,
            sponsor=sponsor
        )
        project.save()

        request = RequestFindCoordinator(
            project=project,
            user=sponsor,
            firstName="Coordinator",
            lastName="Last Name",
            cardType="1",
            cardId="20922842",
            birthdate=datetime.utcnow(),
            gender="1",
            addressState=self.state,
            addressMunicipality=self.municipality,
            addressCity="Barquisimeto",
            address="calle 9 entre 1 y 2",
            addressHome="casa 20-2",
            email="uelibertador@test.com",
            phone="04144433434",
            homePhone="02524433434",
            profession="Teacher"
        )
        request.save()

        coordinatorUser = CoordinatorUser.objects(email=request.email).first()
        self.assertEqual(None, coordinatorUser)

        project = Project.objects.get(id=project.id)
        for step in project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                self.assertEqual("1", step.approvalHistory[0].status)
                self.assertEqual(
                    request.email, step.approvalHistory[0].data['email'])

        # once request is approved must create a coordinatorUser
        # and assign it to project
        request.status = "2"
        request.save()

        coordinatorUser = CoordinatorUser.objects(email=request.email).first()
        self.assertEqual(request.email, coordinatorUser.email)

        project = Project.objects.get(id=project.id)
        self.assertEqual(project.coordinator.id, coordinatorUser.id)

        for step in project.stepsProgress.steps:
            if step.devName in reciprocalFields:
                self.assertEqual("2", step.approvalHistory[0].status)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
