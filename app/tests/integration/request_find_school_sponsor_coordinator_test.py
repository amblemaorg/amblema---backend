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


class ApprovalProcess(unittest.TestCase):
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
            addressMunicipality=self.municipality
        )
        self.coordinator.save()

        self.project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        self.project.save()

    def test_endpoint_create_request_find_coordinator(self):

        requestData = {
            "project": str(self.project.pk),
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
            "addressStreet": "calle 9 entre 1 y 2",
            "addressHome": "casa 20-2",
            "email": "coordinator@test.com",
            "phone": "04144433434",
            "homePhone": "02524433434",
            "profession": "Teacher",
            "referredName": "Juan Veriken"
        }
        res = self.client().post(
            '/requestsfindcoordinator',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_endpoint_create_request_find_sponsor(self):

        data = dict(
            project=str(self.project.pk),
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            phone="02524433434",
            address="Urb Simon Bolivar",
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk),
            addressCity="Barquisimeto",
            addressStreet="calle 9 entre 1 y 2",
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
            name="U.E. Libertador",
            code="315",
            email="uelibertador@test.com",
            address="Urb Simon Bolivar",
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk),
            addressCity="Barquisimeto",
            addressStreet="calle 9 entre 1 y 2",
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

        request = RequestFindSchool(
            project=self.project,
            name="U.E. Libertador",
            code="315",
            email="uelibertador@test.com",
            address="Urb Simon Bolivar",
            addressState=self.state,
            addressMunicipality=self.municipality,
            addressCity="Barquisimeto",
            addressStreet="calle 9 entre 1 y 2",
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

        # once request is approved must create a schoolUser
        # and assign it to project
        request.status = "2"
        request.save()

        schoolUser = SchoolUser.objects(email=request.email).first()
        self.assertEqual(request.email, schoolUser.email)

        self.assertEqual(self.project.school, schoolUser)

    def test_create_sponsor_user_on_approve_request(self):

        request = RequestFindSponsor(
            project=self.project,
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            phone="02524433434",
            address="Urb Simon Bolivar",
            addressState=self.state,
            addressMunicipality=self.municipality,
            addressCity="Barquisimeto",
            addressStreet="calle 9 entre 1 y 2",
            contactFirstName="Contact",
            contactLastName="Name",
            contactPhone="04242772727"
        )
        request.save()

        sponsorUser = SponsorUser.objects(email=request.email).first()
        self.assertEqual(None, sponsorUser)

        # once request is approved must create a sponsorUser
        # and assign it to project
        request.status = "2"
        request.save()

        sponsorUser = SponsorUser.objects(email=request.email).first()
        self.assertEqual(request.email, sponsorUser.email)

        self.assertEqual(self.project.sponsor, sponsorUser)

    def test_create_coordinator_user_on_approve_request(self):

        sponsor = SponsorUser(
            name="Test",
            companyRIF="303993833",
            companyType="2",
            companyPhone="02343432323",
            contactFirstName="Danel",
            contactLastName="Ortega",
            contactPhone="04244664646",
            addressHome="House 34A",
            email="testemail@test.com",
            password="12345678",
            userType="3",
            phone="02322322323",
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
            firstName="Coordinator",
            lastName="Last Name",
            cardType="1",
            cardId="20922842",
            birthdate=str(datetime.utcnow()),
            gender="1",
            addressState=self.state,
            addressMunicipality=self.municipality,
            addressCity="Barquisimeto",
            addressStreet="calle 9 entre 1 y 2",
            addressHome="casa 20-2",
            email="uelibertador@test.com",
            phone="04144433434",
            homePhone="02524433434",
            profession="Teacher",
            referredName="Juan Veriken"
        )
        request.save()

        coordinatorUser = CoordinatorUser.objects(email=request.email).first()
        self.assertEqual(None, coordinatorUser)

        # once request is approved must create a coordinatorUser
        # and assign it to project
        request.status = "2"
        request.save()

        coordinatorUser = CoordinatorUser.objects(email=request.email).first()
        self.assertEqual(request.email, coordinatorUser.email)

        self.assertEqual(project.coordinator.id, coordinatorUser.id)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
