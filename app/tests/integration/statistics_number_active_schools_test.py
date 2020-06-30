# app/tests/integration/statistics_number_active_schools_test.py


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


class StatisticsNumberActiveSchoolsTest(unittest.TestCase):

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        # create schoolYear 1
        self.schoolYear1 = SchoolYear(
            name="Test",
            startDate="2020-09-01",
            endDate="2021-07-30")
        self.schoolYear1.initFirstPecaSetting()
        self.schoolYear1.save()

        # create schoolYear 2
        self.schoolYear2 = SchoolYear(
            name="Test",
            startDate="2021-09-01",
            endDate="2022-07-30")
        self.schoolYear2.initFirstPecaSetting()
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

        # create school 1
        self.school1 = SchoolUser(
            name="School1",
            code="0001",
            phone="11111111111",
            schoolType="1",
            principalFirstName="Principal",
            principalLastName="Uno",
            principalEmail="testemail1@test.com",
            principalPhone="11111111111",
            nTeachers=20,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=20,
            nGrades=20,
            nSections=20,
            schoolShift="1",
            email="someschoolemail1@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
        )
        self.school1.save()

        # create school 2
        self.school2 = SchoolUser(
            name="School2",
            code="0002",
            phone="22222222222",
            schoolType="1",
            principalFirstName="Principal",
            principalLastName="Dos",
            principalEmail="testemail2@test.com",
            principalPhone="22222222222",
            nTeachers=20,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=20,
            nGrades=20,
            nSections=20,
            schoolShift="1",
            email="someschoolemail2@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
        )
        self.school2.save()

        # create school 3
        self.school3 = SchoolUser(
            name="School3",
            code="0003",
            phone="33333333333",
            schoolType="1",
            principalFirstName="Principal",
            principalLastName="Tres",
            principalEmail="testemail3@test.com",
            principalPhone="33333333333",
            nTeachers=20,
            nAdministrativeStaff=20,
            nLaborStaff=20,
            nStudents=20,
            nGrades=20,
            nSections=20,
            schoolShift="1",
            email="someschoolemail3@test.com",
            password="12345678",
            userType="3",
            role=Role.objects(devName="school").first(),
            addressState=self.state,
            addressMunicipality=self.municipality,
        )
        self.school3.save()

        # create project 1
        self.project1 = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school1
        )
        self.project1.save()

        # create project 2
        self.project2 = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school2
        )
        self.project2.save()

        # create project 3
        self.project3 = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school3
        )
        self.project3.save()

        # create peca project 1 
        self.pecaProject1 = PecaProject(
            schoolYear=self.schoolYear1,
            schoolYearName=self.schoolYear1.name,
            project={
                "id": str(self.project1.id),
                "code": str(self.project1.code),
                "coordinator": {
                    "id": str(self.project1.coordinator.id),
                    "name": self.project1.coordinator.firstName + " " + self.project1.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project1.sponsor.id),
                    "name": self.project1.sponsor.name
                },
                "school": {
                    "id": str(self.project1.school.id),
                    "name": self.project1.school.name
                }
            },
            school={
                "name": self.school1.name,
                "code": self.school1.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school1.principalFirstName,
                "principalLastName": self.school1.principalLastName,
                "principalEmail": self.school1.principalEmail,
                "principalPhone": self.school1.principalPhone,
                "nTeachers": self.school1.nTeachers,
                "nGrades": self.school1.nGrades,
                "nStudents": self.school1.nStudents,
                "nAdministrativeStaff": self.school1.nAdministrativeStaff,
                "nLaborStaff": self.school1.nLaborStaff
            },
            createdAt = "2020-09-15 00:00:00",
            updatedAt = "2020-12-03 00:00:00"

        )
        self.pecaProject1.save()

        # create peca project 2
        self.pecaProject2 = PecaProject(
            schoolYear=self.schoolYear2,
            schoolYearName=self.schoolYear2.name,
            project={
                "id": str(self.project1.id),
                "code": str(self.project1.code),
                "coordinator": {
                    "id": str(self.project1.coordinator.id),
                    "name": self.project1.coordinator.firstName + " " + self.project1.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project1.sponsor.id),
                    "name": self.project1.sponsor.name
                },
                "school": {
                    "id": str(self.project1.school.id),
                    "name": self.project1.school.name
                }
            },
            school={
                "name": self.school1.name,
                "code": self.school1.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school1.principalFirstName,
                "principalLastName": self.school1.principalLastName,
                "principalEmail": self.school1.principalEmail,
                "principalPhone": self.school1.principalPhone,
                "nTeachers": self.school1.nTeachers,
                "nGrades": self.school1.nGrades,
                "nStudents": self.school1.nStudents,
                "nAdministrativeStaff": self.school1.nAdministrativeStaff,
                "nLaborStaff": self.school1.nLaborStaff
            },
            createdAt = "2022-04-15 00:00:00",
            updatedAt = "2022-06-03 00:00:00"

        )
        self.pecaProject2.save()

        # create peca project 3
        self.pecaProject3 = PecaProject(
            schoolYear=self.schoolYear1,
            schoolYearName=self.schoolYear1.name,
            project={
                "id": str(self.project2.id),
                "code": str(self.project2.code),
                "coordinator": {
                    "id": str(self.project2.coordinator.id),
                    "name": self.project2.coordinator.firstName + " " + self.project2.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project2.sponsor.id),
                    "name": self.project2.sponsor.name
                },
                "school": {
                    "id": str(self.project2.school.id),
                    "name": self.project2.school.name
                }
            },
            school={
                "name": self.school2.name,
                "code": self.school2.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school2.principalFirstName,
                "principalLastName": self.school2.principalLastName,
                "principalEmail": self.school2.principalEmail,
                "principalPhone": self.school2.principalPhone,
                "nTeachers": self.school2.nTeachers,
                "nGrades": self.school2.nGrades,
                "nStudents": self.school2.nStudents,
                "nAdministrativeStaff": self.school2.nAdministrativeStaff,
                "nLaborStaff": self.school2.nLaborStaff
            },
            createdAt = "2021-01-15 00:00:00",
            updatedAt = "2021-03-03 00:00:00"

        )
        self.pecaProject3.save()

        # create peca project 4
        self.pecaProject4 = PecaProject(
            schoolYear=self.schoolYear2,
            schoolYearName=self.schoolYear2.name,
            project={
                "id": str(self.project2.id),
                "code": str(self.project2.code),
                "coordinator": {
                    "id": str(self.project2.coordinator.id),
                    "name": self.project2.coordinator.firstName + " " + self.project2.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project2.sponsor.id),
                    "name": self.project2.sponsor.name
                },
                "school": {
                    "id": str(self.project2.school.id),
                    "name": self.project2.school.name
                }
            },
            school={
                "name": self.school2.name,
                "code": self.school2.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school2.principalFirstName,
                "principalLastName": self.school2.principalLastName,
                "principalEmail": self.school2.principalEmail,
                "principalPhone": self.school2.principalPhone,
                "nTeachers": self.school2.nTeachers,
                "nGrades": self.school2.nGrades,
                "nStudents": self.school2.nStudents,
                "nAdministrativeStaff": self.school2.nAdministrativeStaff,
                "nLaborStaff": self.school2.nLaborStaff
            },
            createdAt = "2021-11-15 00:00:00",
            updatedAt = "2022-03-03 00:00:00"

        )
        self.pecaProject4.save()

        # create peca project 5
        self.pecaProject5 = PecaProject(
            schoolYear=self.schoolYear1,
            schoolYearName=self.schoolYear1.name,
            project={
                "id": str(self.project3.id),
                "code": str(self.project3.code),
                "coordinator": {
                    "id": str(self.project3.coordinator.id),
                    "name": self.project3.coordinator.firstName + " " + self.project3.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project3.sponsor.id),
                    "name": self.project3.sponsor.name
                },
                "school": {
                    "id": str(self.project3.school.id),
                    "name": self.project3.school.name
                }
            },
            school={
                "name": self.school3.name,
                "code": self.school3.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school3.principalFirstName,
                "principalLastName": self.school3.principalLastName,
                "principalEmail": self.school3.principalEmail,
                "principalPhone": self.school3.principalPhone,
                "nTeachers": self.school3.nTeachers,
                "nGrades": self.school3.nGrades,
                "nStudents": self.school3.nStudents,
                "nAdministrativeStaff": self.school3.nAdministrativeStaff,
                "nLaborStaff": self.school3.nLaborStaff
            },
            createdAt = "2021-06-15 00:00:00",
            updatedAt = "2021-08-03 00:00:00"

        )
        self.pecaProject5.save()

        # create peca project 6
        self.pecaProject6 = PecaProject(
            schoolYear=self.schoolYear2,
            schoolYearName=self.schoolYear2.name,
            project={
                "id": str(self.project3.id),
                "code": str(self.project3.code),
                "coordinator": {
                    "id": str(self.project3.coordinator.id),
                    "name": self.project3.coordinator.firstName + " " + self.project3.coordinator.lastName
                },
                "sponsor": {
                    "id": str(self.project3.sponsor.id),
                    "name": self.project3.sponsor.name
                },
                "school": {
                    "id": str(self.project3.school.id),
                    "name": self.project3.school.name
                }
            },
            school={
                "name": self.school3.name,
                "code": self.school3.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school3.principalFirstName,
                "principalLastName": self.school3.principalLastName,
                "principalEmail": self.school3.principalEmail,
                "principalPhone": self.school3.principalPhone,
                "nTeachers": self.school3.nTeachers,
                "nGrades": self.school3.nGrades,
                "nStudents": self.school3.nStudents,
                "nAdministrativeStaff": self.school3.nAdministrativeStaff,
                "nLaborStaff": self.school3.nLaborStaff
            },
            createdAt = "2022-01-15 00:00:00",
            updatedAt = "2022-04-03 00:00:00"

        )
        self.pecaProject6.save()

    def test_statistics_number_active_schools(self):

        # get statistics number active schools
        res = self.client().get(
            '/statistics/numberactiveschools/{}/{}'.format(
                self.schoolYear1.pk, self.schoolYear2.pk)
        )
        self.assertEqual(res.status_code, 200)

        result = json.loads(res.data.decode('utf8').replace("'", '"'))

        self.assertEqual(str(self.schoolYear1.pk),result['records'][0]['academicPeriodId'])
        self.assertEqual(self.schoolYear1.name,result['records'][0]['academicPeriodName'])
        self.assertEqual(['2020', '2021'],result['records'][0]['academicPeriodYears'])
        self.assertEqual(1,result['records'][0]['trimesterOne'])
        self.assertEqual(2,result['records'][0]['trimesterTwo'])
        self.assertEqual(2,result['records'][0]['trimesterThree'])
        self.assertEqual(3,result['records'][0]['trimesterFour'])

        self.assertEqual(str(self.schoolYear2.pk),result['records'][1]['academicPeriodId'])
        self.assertEqual(self.schoolYear2.name,result['records'][1]['academicPeriodName'])
        self.assertEqual(['2021', '2022'],result['records'][1]['academicPeriodYears'])
        self.assertEqual(1,result['records'][1]['trimesterOne'])
        self.assertEqual(2,result['records'][1]['trimesterTwo'])
        self.assertEqual(3,result['records'][1]['trimesterThree'])
        self.assertEqual(3,result['records'][1]['trimesterFour'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()