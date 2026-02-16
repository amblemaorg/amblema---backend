
import unittest
import json
from datetime import datetime
import io
from bson import ObjectId

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
from resources.images import test_image
from app.models.peca_yearbook_model import Entity, GroupPhoto


class PecaYearbookGroupPhotoTest(unittest.TestCase):
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
            addressMunicipality=self.municipality,
            yearbook=Entity(
                name="School",
                image="https://someimage.jpg",
                content="this is my yearbook content"
            )
        )
        self.school.save()

        # create project
        self.project = Project(
            coordinator=self.coordinator,
            sponsor=self.sponsor,
            school=self.school
        )
        self.project.save()

        # create sections with different grades to test sorting
        # Grade 2 (should be second)
        self.section1 = {"id": str(ObjectId()), "grade": "2", "name": "B", "isDeleted": False}
        # Grade 0 (Preescolar - should be first)
        self.section2 = {"id": str(ObjectId()), "grade": "0", "name": "A", "isDeleted": False}

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
                "sections": [self.section1, self.section2]
            }
        )
        self.pecaProject.save()

    def test_yearbook_group_photo(self):
        
        requestData = {
            "groupPhoto": {
                "name": "Group Photo",
                "content": "group photo content",
                "image": test_image,
                "groupedSections": [self.section1["id"], self.section2["id"]]
            }
        }

        res = self.client().post(
            '/pecaprojects/yearbook/{}?userId={}'.format(
                self.pecaProject.id, self.coordinator.id),
            data=json.dumps(requestData),
            content_type='application/json')
        
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(str(self.coordinator.id),
                         result['approvalHistory'][0]['user']['id'])
        
        # Verify groupedSectionsContent enrichment for Backoffice
        # Checks for SORTING and RENAMING
        # Expected: Preescolar - A (Grade 0), then 2do Grado - B (Grade 2)
        content_list = result['approvalHistory'][0]['detail']['groupPhoto']['groupedSectionsContent']
        self.assertEqual(len(content_list), 2)
        self.assertEqual(content_list[0], "Preescolar - A")
        self.assertEqual(content_list[1], "2do Grado - B")
        
        # Approve request
        requestData = {
            "status": "2"
        }
        res = self.client().put(
            '/requestscontentapproval/{}'.format(
                result['approvalHistory'][0]['id']),
            data=json.dumps(requestData),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # check yearbook on peca
        res = self.client().get(
            '/pecaprojects/{}'.format(self.pecaProject.id)
        )
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(
            "group photo content",
            result['yearbook']['groupPhoto']['content'])
        self.assertIsNotNone(result['yearbook']['groupPhoto']['image'])
        # The list of IDs is stored as is (though arguably could be sorted too, the requirement was for display)
        self.assertIn(self.section1["id"], result['yearbook']['groupPhoto']['groupedSections'])
        self.assertIn(self.section2["id"], result['yearbook']['groupPhoto']['groupedSections'])

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
