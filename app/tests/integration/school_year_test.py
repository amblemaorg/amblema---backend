# app/tests/school_year_test.py


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
from app.models.peca_project_model import PecaProject
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.helpers.handler_seeds import create_standard_roles
from app.helpers.handler_seeds import create_initial_steps
from app.models.step_model import Step

class SchoolYearTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

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
            name="School 1",
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

    def test_create_school_year(self):
        requestData = {
            "name": "2020 - 2021"
        }
        # create schoolyear
        res = self.client().post(
            '/schoolyears',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)
        result1 = json.loads(res.data.decode('utf8').replace("'", '"'))

        result1 = SchoolYear.objects(id=result1['id'], isDeleted=False).first()
        self.assertEqual([], result1['pecaSetting']['lapse1']['activities'])
        self.assertEqual("1", result1.status)

        create_initial_steps()
        steps = Step.objects(isDeleted=False).count()
        self.assertEqual(21, steps)

        # create new schoolyear
        requestData = {
            "name": "2021-2022"
        }
        res = self.client().post(
            '/schoolyears',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)

        schoolYear = SchoolYear.objects(id=result1['id']).first()
        schoolYear.endDate = schoolYear.endDate.replace(
            schoolYear.endDate.year - 1)
        schoolYear.save()

        # create new schoolyear
        requestData = {
            "name": "2021 - 2022"
        }
        res = self.client().post(
            '/schoolyears',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)
        result2 = json.loads(res.data.decode('utf8').replace("'", '"'))

        result2 = SchoolYear.objects(id=result2['id'], isDeleted=False).first()
        self.assertEqual([], result2['pecaSetting']['lapse1']['activities'])
        self.assertEqual("1", result2.status)

        result1 = SchoolYear.objects(id=result1['id'], isDeleted=False).first()
        self.assertEqual("2", result1.status)

        steps = Step.objects(isDeleted=False).count()
        self.assertEqual(42, steps)

        steps = Step.objects(isDeleted=False, schoolYear=result2.id).count()
        self.assertEqual(21, steps)


    def test_enroll_school(self):
        requestData = {
            "name": "2020 - 2021"
        }
        # create schoolyear
        res = self.client().post(
            '/schoolyears',
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)
        schoolyear = json.loads(res.data.decode('utf8').replace("'", '"'))

        requestData = {
            "name": "Some name",
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

        # create second school
        self.school2 = SchoolUser(
            name="School 2",
            code="0003",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Maria",
            principalLastName="Gonzalez",
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
        self.school2.save()

        # create project
        project = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school,
            phase="2"  # approved
        )
        project.save()

        # create project 2
        project2 = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school2,
            phase="1"  # in steps
        )
        project2.save()

        # get available schools
        res = self.client().get(
            '/enrollment')
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(0,
                         len(result['enrolledSchools']))
        self.assertEqual(1,
                         len(result['availableSchools']))

        # enroll school
        res = self.client().put(
            '/enrollment/{}'.format(project['id']),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            '2022 - 2023', result['schoolYears'][0]['schoolYear']['name'])

        project = Project.objects(id=project['id']).first()
        self.assertEqual(1, len(project.schoolYears))

        # get available schools
        res = self.client().get(
            '/enrollment')
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(1,
                         len(result['enrolledSchools']))
        self.assertEqual(0,
                         len(result['availableSchools']))

        # delete school
        res = self.client().put(
            '/enrollment/{}?action=delete'.format(project['id']),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        project = Project.objects(id=project['id']).first()
        self.assertEqual(0, len(project.schoolYears))

        # get available schools
        res = self.client().get(
            '/enrollment')
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(0,
                         len(result['enrolledSchools']))
        self.assertEqual(1,
                         len(result['availableSchools']))

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
