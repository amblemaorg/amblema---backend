# app/tests/integration/contact_request_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db
from app.models.school_year_model import SchoolYear
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.user_model import User
from app.models.school_contact_model import SchoolContact
from app.models.sponsor_contact_model import SponsorContact
from app.models.coordinator_contact_model import CoordinatorContact
from app.helpers.handler_seeds import create_standard_roles


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

    def test_endpoint_school_contact(self):

        # with sponsor
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
            sponsorRIF="282882822",
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
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)

        contactReq = SchoolContact.objects.get(id=json_res['id'])
        contactReq.status = "2"
        contactReq.save()

        schoolUser = User.objects(
            email="uelibertador@test.com").only('email').first()
        self.assertIsNotNone(schoolUser)
        sponsorUser = User.objects(
            email="iamsponsor@test.com").only('email').first()
        self.assertIsNotNone(sponsorUser)

        # without sponsor
        reqData = dict(
            name="U.E. Concepcion",
            code="316",
            email="ueconcepcion@test.com",
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
            hasSponsor=False
        )

        res = self.client().post(
            '/schoolscontacts',
            data=json.dumps(reqData),
            content_type='application/json')
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)

        contactReq = SchoolContact.objects.get(id=json_res['id'])
        contactReq.status = "2"
        contactReq.save()

        schoolUser = User.objects(
            email="ueconcepcion@test.com").only('email').first()
        self.assertIsNotNone(schoolUser)

    def test_endpoint_sponsor_contact(self):

        # with school
        reqData = dict(
            schoolName="U.E. Libertador",
            schoolCode="315",
            schoolEmail="uelibertador@test.com",
            schoolAddress="Urb Simon Bolivar",
            schoolAddressState=str(self.state.pk),
            schoolAddressMunicipality=str(self.municipality.pk),
            schoolAddressCity="Barquisimeto",
            schoolAddressStreet="calle 9 entre 1 y 2",
            schoolPhone="02524433434",
            schoolType="1",
            schoolPrincipalFirstName="Marlene",
            schoolPrincipalLastName="Mejia",
            schoolPrincipalEmail="mmejia@test.com",
            schoolPrincipalPhone="04242772727",
            schoolSubPrincipalFirstName="Nelly",
            schoolSubPrincipalLastName="Velazquez",
            schoolSubPrincipalEmail="nvelazquez@test.com",
            schoolSubPrincipalPhone="04244545454",
            schoolNTeachers=22,
            schoolNAdministrativeStaff=10,
            schoolNLaborStaff=3,
            schoolNStudents=500,
            schoolNGrades=6,
            schoolNSections=18,
            schoolShift="3",
            hasSchool=True,
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
            '/sponsorscontacts',
            data=json.dumps(reqData),
            content_type='application/json')
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)

        contactReq = SponsorContact.objects.get(id=json_res['id'])
        contactReq.status = "2"
        contactReq.save()

        schoolUser = User.objects(
            email="uelibertador@test.com").only('email').first()
        self.assertIsNotNone(schoolUser)
        self.assertEqual("uelibertador@test.com", schoolUser.email)
        sponsorUser = User.objects(
            email="iamsponsor@test.com").only('email').first()
        self.assertIsNotNone(sponsorUser)

        # without school
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
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)

        contactReq = SponsorContact.objects.get(id=json_res['id'])
        contactReq.status = "2"
        contactReq.save()

        sponsorUser = User.objects(
            email="iamsponsor2@test.com").only('email').first()
        self.assertIsNotNone(sponsorUser)

    def test_endpoint_coordinator_contact(self):

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
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)
