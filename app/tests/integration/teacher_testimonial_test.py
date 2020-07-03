# app/tests/integration/teacher_testimonial_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.peca_project_model import PecaProject
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.helpers.handler_seeds import create_standard_roles
from app.models.teacher_model import Teacher


class TeacherTestimonialTest(unittest.TestCase):

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
            nTeachers=2,
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
            teachers=[
                Teacher(
                    firstName="Arelis",
                    lastName="Crespo",
                    cardType="1",
                    cardId="20928888",
                    gender="1",
                    email="arelis@test.com",
                    phone="04122222233",
                    addressState=str(self.state.id),
                    addressMunicipality=str(self.municipality.id),
                    address="19th street",
                    addressCity="Barquisimeto"
                ),
                Teacher(
                    firstName="Juan",
                    lastName="Perez",
                    cardType="1",
                    cardId="19105444",
                    gender="2",
                    email="juanp@test.com",
                    phone="04245670901",
                    addressState=str(self.state.id),
                    addressMunicipality=str(self.municipality.id),
                    address="Av 20 entre calles 15 y 16",
                    addressCity="Barquisimeto"
                )
            ]
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
                "nLaborStaff": self.school.nLaborStaff
            }

        )
        self.pecaProject.save()

    def test_teacher_testimonials(self):

        # create teacher testimonials
        requestData = {
            "testimonials": [
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test A",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[1].id),
                    "position": "Profesor de Matematicas",
                    "description": "Testimonio test B",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                }
            ]
        }
        res = self.client().post(
            '/schools/teacherstestimonials/{}?userId={}'.format(
                self.school.pk, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("1", result['approvalStatus'])
        self.assertEqual(True, result['isInApproval'])
        self.assertEqual("1", result['approvalHistory'][0]['status'])
        self.assertEqual(2, len(result['testimonials']))
        self.assertEqual(self.school.teachers[0].firstName, result['testimonials'][0]['firstName'])
        self.assertEqual(self.school.teachers[1].firstName, result['testimonials'][1]['firstName'])
        self.assertEqual("Testimonio test A", result['testimonials'][0]['description'])
        self.assertEqual("Testimonio test B", result['testimonials'][1]['description'])
        testimonials = result

        # approve request testimonials
        requestData = {
            "status": "2"
        }
        res = self.client().put('/requestscontentapproval/{}'.format(
            testimonials['approvalHistory'][0]['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # get all teacher testimonials access peca
        res = self.client().get(
            '/schools/teacherstestimonials/{}?access={}'.format(
                self.school.pk, "peca")
        )
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("2", result['approvalStatus'])
        self.assertEqual(False, result['isInApproval'])
        self.assertEqual("2", result['approvalHistory'][0]['status'])
        self.assertEqual(2, len(result['testimonials']))
        self.assertEqual(self.school.teachers[0].firstName, result['testimonials'][0]['firstName'])
        self.assertEqual(self.school.teachers[1].firstName, result['testimonials'][1]['firstName'])
        self.assertEqual("Testimonio test A", result['testimonials'][0]['description'])
        self.assertEqual("Testimonio test B", result['testimonials'][1]['description'])

        # update teacher testimonials
        requestData = {
            "testimonials": [
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test AA",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[1].id),
                    "position": "Profesor de Matematicas",
                    "description": "Testimonio test B",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test C",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                }
            ]
        }
        res = self.client().post(
            '/schools/teacherstestimonials/{}?userId={}'.format(
                self.school.pk, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual("2", result['approvalStatus'])
        self.assertEqual(True, result['isInApproval'])
        self.assertEqual("1", result['approvalHistory'][1]['status'])
        self.assertEqual(len(testimonials['testimonials']), len(result['testimonials']))
        self.assertEqual(self.school.teachers[0].firstName, result['testimonials'][0]['firstName'])
        self.assertEqual(self.school.teachers[1].firstName, result['testimonials'][1]['firstName'])
        self.assertEqual(testimonials['testimonials'][0]['description'], result['testimonials'][0]['description'])
        testimonials = result

        # cancel request testimonials
        requestData = {
            "status": "4"
        }
        res = self.client().put('/requestscontentapproval/{}'.format(
            testimonials['approvalHistory'][1]['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # get all teacher testimonials access web
        res = self.client().get(
            '/schools/teacherstestimonials/{}?access={}'.format(
                self.school.pk, "web")
        )
        self.assertEqual(res.status_code, 200)

        # create teacher testimonials > 4
        requestData = {
            "testimonials": [
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test AA",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[1].id),
                    "position": "Profesor de Matematicas",
                    "description": "Testimonio test B",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test C",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test AA",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[1].id),
                    "position": "Profesor de Matematicas",
                    "description": "Testimonio test B",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                },
                {
                    "teacherId": str(self.school.teachers[0].id),
                    "position": "Profesor de Biologia",
                    "description": "Testimonio test C",
                    "image": "http://localhost:10505/resources/images/teachertestimonial/5ef49ae48a57c592db438227.jpg"
                }
            ]
        }
        res = self.client().post(
            '/schools/teacherstestimonials/{}?userId={}'.format(
                self.school.pk, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
