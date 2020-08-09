# app/tests/integration/validate_delete_test.py


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
from app.helpers.handler_seeds import create_standard_roles, create_initial_steps
from app.models.teacher_model import Teacher
from app.models.step_model import Step
from resources.images import test_image


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

        create_initial_steps()
        create_standard_roles()

        self.role = Role(name="custom").save()

        self.state = State(
            name="Lara"
        )
        self.state.save()

        self.municipality = Municipality(
            state=self.state,
            name="Iribarren"
        )
        self.municipality.save()

        self.zulia = State(
            name="Zulia"
        )
        self.zulia.save()

        self.maracaibo = Municipality(
            state=self.zulia,
            name="Maracaibo"
        ).save()

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

        self.sponsor2 = SponsorUser(
            name="Test2",
            companyRif="303993832",
            companyType="2",
            companyPhone="02343432323",
            contactFirstName="Juan",
            contactLastName="Ortega",
            contactPhone="04244664646",
            addressHome="House 34A",
            email="testemail2@test.com",
            password="12345678",
            userType="3",
            role=self.role,
            addressState=self.zulia,
            addressMunicipality=self.maracaibo
        )
        self.sponsor2.save()

        self.school = SchoolUser(
            name="School",
            code="0002",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Danel",
            principalLastName="Medina",
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
            school=self.school,
            phase="2"
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
                    {
                        "grade": "1",
                        "name": "A",
                        "goals": {
                            "wordsPerMin": 70,
                            "operationsPerMin": 30,
                            "multiplicationsPerMin": 40
                        },
                        "students": [
                            {
                                "firstName": "Victoria",
                                "lastName": "Gutierrez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                }
                            },
                            {
                                "firstName": "Eilen",
                                "lastName": "Rodriguez",
                                "birthdate": datetime.utcnow(),
                                "gender": "1",
                                "lapse1": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse2": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                },
                                "lapse3": {
                                    "multiplicationsPerMin": None,
                                    "operationsPerMin": None,
                                    "wordsPerMin": None
                                }
                            }
                        ],
                        "teacher": {
                            "firstName": "Maria",
                            "lastName": "Teran"
                        }
                    }
                ]
            }
        )
        self.pecaProject.save()

    def test_validate_delete(self):
        '''
        Test delete student
        '''

        # enable olympics for lapse1
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
            "section": str(self.pecaProject.school.sections[0].id),
            "student": str(self.pecaProject.school.sections[0].students[0].id),
            "status": "2",  # classified
            "result": "1"  # gold medal
        }
        res = self.client().post(
            '/pecaprojects/olympics/{}/{}'.format(self.pecaProject.id, 1),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # test delete student
        res = self.client().delete(
            '/pecaprojects/students/{}/{}/{}'.format(
                self.pecaProject.pk,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[0].id))
        self.assertEqual(res.status_code, 419)

        # delete student from olympics
        res = self.client().delete(
            '/pecaprojects/olympics/{}/{}/{}'.format(
                self.pecaProject.id,
                1,
                self.pecaProject.school.sections[0].students[0].id),
            data=requestData,
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # test delete student
        res = self.client().delete(
            '/pecaprojects/students/{}/{}/{}'.format(
                self.pecaProject.pk,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[0].id))
        self.assertEqual(res.status_code, 200)

        '''
        Test delete section
        '''
        # try delete (with student)
        res = self.client().delete(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, self.pecaProject.school.sections[0].id))
        self.assertEqual(res.status_code, 419)

        # test delete student
        res = self.client().delete(
            '/pecaprojects/students/{}/{}/{}'.format(
                self.pecaProject.pk,
                self.pecaProject.school.sections[0].id,
                self.pecaProject.school.sections[0].students[1].id))
        self.assertEqual(res.status_code, 200)

        # try delete (without students)
        res = self.client().delete(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, self.pecaProject.school.sections[0].id))
        self.assertEqual(res.status_code, 200)

        '''
        Test delete teacher
        '''

        # create section
        requestData = {
            "grade": "1",
            "name": "B",
            "teacher": str(self.school.teachers[0].id)
        }
        res = self.client().post(
            '/pecaprojects/sections/{}'.format(self.pecaProject.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        section = json.loads(res.data.decode('utf8').replace("'", '"'))

        # delete teacher
        res = self.client().delete(
            '/schools/teachers/{}/{}'.format(
                self.school.pk, self.school.teachers[0].id))
        self.assertEqual(res.status_code, 419)

        # delete section
        res = self.client().delete(
            '/pecaprojects/sections/{}/{}'.format(
                self.pecaProject.pk, section['id']))
        self.assertEqual(res.status_code, 200)

        # delete teacher
        res = self.client().delete(
            '/schools/teachers/{}/{}'.format(
                self.school.pk, self.school.teachers[0].id))
        self.assertEqual(res.status_code, 200)

    def test_validate_delete_project(self):
        '''
        Test delete project
        '''
        step = Step.objects(
            isDeleted=False, devName="sponsorPresentationSchool").first()
        requestData = dict(
            project=str(self.project.pk),
            user=str(self.sponsor.pk),
            stepId=str(step.pk),
            stepUploadedFile=(io.BytesIO(b'hi everyone'), 'test.pdf')
        )

        res = self.client().post(
            '/requestsstepapproval',
            data=requestData,
            content_type='multipart/form-data')
        approval_request = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)

        # delete project
        res = self.client().delete(
            '/projects/{}'.format(
                self.project.id))
        self.assertEqual(res.status_code, 419)

        res = self.client().put(
            '/requestscontentapproval/{}'.format(approval_request['id']),
            data=json.dumps({"status": "2"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # try delete peca
        res = self.client().put(
            '/enrollment/{}?action=delete'.format(self.project['id']),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # delete project
        res = self.client().delete(
            '/projects/{}'.format(
                self.project.id))
        self.assertEqual(res.status_code, 200)

    def test_validate_delete_peca(self):
        '''
        Test delete peca
        '''

        # set initial workshop
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
        approval_request = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        approval_request = approval_request['approvalHistory'][0]

        # try delete peca
        res = self.client().put(
            '/enrollment/{}?action=delete'.format(self.project['id']),
            content_type='application/json')
        self.assertEqual(res.status_code, 419)

        # cancel request
        requestData = {
            "status": "4"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(
                approval_request['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # try delete peca
        res = self.client().put(
            '/enrollment/{}?action=delete'.format(self.project['id']),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_delete_users(self):

        res = self.client().delete(
            '/users/{}?userType=3'.format(
                self.sponsor.id))
        self.assertEqual(res.status_code, 419)

        requestData = {
            "sponsor": str(self.sponsor2.id)
        }
        res = self.client().put(
            '/projects/{}'.format(
                self.project.id),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        res = self.client().delete(
            '/users/{}?userType=3'.format(
                self.sponsor.id))
        self.assertEqual(res.status_code, 200)

    def test_delete_states_municipalities(self):
        res = self.client().delete(
            '/municipalities/{}'.format(
                self.maracaibo.id))
        self.assertEqual(res.status_code, 419)

        res = self.client().delete(
            '/users/{}?userType=3'.format(
                self.sponsor2.id))
        self.assertEqual(res.status_code, 200)

        res = self.client().delete(
            '/municipalities/{}'.format(
                self.maracaibo.id))
        self.assertEqual(res.status_code, 200)

    def test_delete_role(self):
        res = self.client().delete(
            '/roles/{}'.format(
                self.role.id))
        self.assertEqual(res.status_code, 419)

        res = self.client().delete(
            '/users/{}?userType=3'.format(
                self.sponsor2.id))
        self.assertEqual(res.status_code, 200)

        res = self.client().delete(
            '/roles/{}'.format(
                self.role.id))
        self.assertEqual(res.status_code, 200)

    def test_delete_steps(self):
        generalStep = Step(
            name="step upload general",
            hasText=True,
            hasUpload=True,
            text="step description",
            tag="1",
            approvalType="3"
        )
        generalStep.save()

        requestData = dict(
            project=str(self.project.pk),
            user=str(self.sponsor.pk),
            stepId=str(generalStep.id),
            stepUploadedFile=(io.BytesIO(b'hi everyone'), 'test.pdf')
        )

        res = self.client().post(
            '/requestsstepapproval',
            data=requestData,
            content_type='multipart/form-data')
        approval_request = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)

        # delete step
        res = self.client().delete(
            '/steps/{}'.format(
                generalStep.id))
        self.assertEqual(res.status_code, 419)

        res = self.client().put(
            '/requestscontentapproval/{}'.format(approval_request['id']),
            data=json.dumps({"status": "3"}),
            content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # delete step
        res = self.client().delete(
            '/steps/{}'.format(
                generalStep.id))
        self.assertEqual(res.status_code, 200)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
