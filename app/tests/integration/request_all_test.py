# app/tests/integration/request_all_tests.py


import unittest
import json
from datetime import datetime

from app import create_app, db
from app.models.school_year_model import SchoolYear
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.school_contact_model import SchoolContact
from app.models.sponsor_contact_model import SponsorContact
from app.models.coordinator_contact_model import CoordinatorContact
from app.helpers.handler_seeds import create_standard_roles
from app.services.request_all_service import RequestsAll
from app.models.coordinator_user_model import CoordinatorUser
from app.models.project_model import Project


class ContactRequestTest(unittest.TestCase):

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

    def test_get_all_contact_requests(self):

        # school contact
        reqData = dict(
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
            schoolShift="3",
            hasSponsor=True,
            sponsorEmail="iamsponsor@test.com",
            sponsorName="Sponsor C.A.",
            sponsorRif="282882822",
            sponsorCompanyType="1",
            sponsorCompanyPhone="02524433434",
            sponsorAddress="Urb Simon Bolivar",
            sponsorAddressState=str(self.state.pk),
            sponsorAddressMunicipality=str(self.municipality.pk),
            sponsorAddressCity="Barquisimeto",
            sponsorAddressStreet="calle 9 entre 1 y 2",
            sponsorContactFirstName="Contact FirstName",
            sponsorContactLastName="Contact Lastname",
            sponsorContactPhone="04242772727"
        )

        res = self.client().post(
            '/schoolscontacts',
            data=json.dumps(reqData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

        # sponsor contact
        reqData = dict(
            hasSchool=False,
            email="iamsponsor2@test.com",
            name="Sponsor2 C.A.",
            rif="282882823",
            companyType="1",
            companyPhone="02524433434",
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
            '/sponsorscontacts',
            data=json.dumps(reqData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

        # coordinator contact
        reqData = dict(
            firstName="Coordinator",
            lastName="Last Name",
            name="hola",
            cardType="1",
            cardId="20922842",
            birthdate=str(datetime.utcnow()),
            gender="1",
            addressState=str(self.state.pk),
            addressMunicipality=str(self.municipality.pk),
            addressCity="Barquisimeto",
            addressStreet="calle 9 entre 1 y 2",
            addressHome="casa 20-2",
            email="coordinator@test.com",
            phone="04144433434",
            homePhone="02524433434",
            profession="Teacher",
            isReferred=True,
            referredName="Juan Veriken"
        )

        res = self.client().post(
            '/coordinatorscontacts',
            data=json.dumps(reqData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)

        res = self.client().get(
            '/contactrequests')
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("Coordinator Last Name",
                         result['records'][0]['name'])
        self.assertEqual('0000003', result['records'][0]['requestCode'])

    def test_get_all_contact_requests(self):

        coordinator = CoordinatorUser(
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
        coordinator.save()

        project = Project(
            schoolYear=self.schoolYear,
            coordinator=coordinator
        )
        project.save()

        data = dict(
            project=str(project.pk),
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            companyPhone="02524433434",
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

        data = dict(
            project=str(project.pk),
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

        secondProject = Project(
            schoolYear=self.schoolYear,
            coordinator=coordinator
        )
        secondProject.save()

        data = dict(
            project=str(secondProject.pk),
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            companyPhone="02524433434",
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

        data = dict(
            project=str(project.pk),
            email="iamsponsor@test.com",
            name="Sponsor C.A.",
            rif="282882822",
            companyType="1",
            companyPhone="02524433434",
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

        res = self.client().get(
            '/findrequests')
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("Sponsor C.A.",
                         result['records'][0]['name'])
        self.assertEqual('0000004', result['records'][0]['requestCode'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
