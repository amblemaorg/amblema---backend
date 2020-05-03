# app/tests/integration/request_project_confirmation_approval_test.py


import unittest
import json
import io
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step
from app.models.coordinator_user_model import CoordinatorUser
from app.models.sponsor_user_model import SponsorUser
from app.models.school_user_model import SchoolUser
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.request_step_approval_model import RequestStepApproval
from app.models.request_project_approval_model import RequestProjectApproval


class RequestProjectConfirmationTest(unittest.TestCase):
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

        self.sponsorAgreementSchoolFoundation = Step(
            name="Convenio escuela - fundación",
            devName="sponsorAgreementSchoolFoundation",
            tag="3",
            isStandard=True,
            approvalType="3",
            hasText=True,
            hasFile=True,
            hasUpload=True,
            text="some description",
            file={"name": "Agreement name",
                  "url": "https://urlserver.com/files/asd.pdf"}
        ).save()

        self.schoolAgreementFoundation = Step(
            name="Convenio escuela - fundación",
            devName="schoolAgreementFoundation",
            tag="4",
            isStandard=True,
            approvalType="3",
            hasText=True,
            hasFile=True,
            hasUpload=True,
            text="some description",
            file={"name": "Agreement name",
                    "url": "https://urlserver.com/files/asd.pdf"}
        )
        self.schoolAgreementFoundation.save()

        self.amblemaConfirmation = Step(
            name="Confirmación de AmbLeMa",
            devName="amblemaConfirmation",
            tag="1",
            isStandard=True,
            approvalType="1",
            hasText=True,
            text="some description"
        ).save()

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
            gender="1",
            birthdate=datetime.utcnow(),
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

        sponsor = SponsorUser(
            name="sponsor company name",
            email="sponsoruser@test.com",
            password="87654321",
            userType="3",
            role=self.role,
            addressState=self.state,
            addressMunicipality=self.municipality,
            address="street 3",
            companyRif="209228272",
            companyType="1",
            companyPhone="02524484747",
            contactFirstName="Juan",
            contactLastName="Contact",
            contactPhone="02323456789"
        )
        sponsor.save()

        school = SchoolUser(
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
            role=self.role,
            addressState=self.state,
            addressMunicipality=self.municipality
        ).save()

        self.project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator,
            sponsor=sponsor,
            school=school

        )
        self.project.save()
        self.assertEqual(3, len(self.project.stepsProgress.steps))

    def test_request_project_confirmation(self):
        reqStepApproval = RequestStepApproval(
            project=self.project,
            stepId=self.project.stepsProgress.steps[0].id,
            stepUploadedFile={
                "url": "https://somedomail.com/somefile.pdf", "name": "my file.pdf"}
        )
        reqStepApproval.save()
        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(
            str(reqStepApproval.pk), self.project.stepsProgress.steps[0].approvalHistory[0].id)

        # check fill of the step fields on approval
        self.assertEqual(
            self.sponsorAgreementSchoolFoundation.name, reqStepApproval.stepName)
        self.assertEqual(
            self.sponsorAgreementSchoolFoundation.devName, reqStepApproval.stepDevName)
        self.assertEqual(self.sponsorAgreementSchoolFoundation.hasUpload,
                         reqStepApproval.stepHasUpload)

        # approved
        reqStepApproval.status = "2"
        reqStepApproval.save()
        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(
            "3", self.project.stepsProgress.steps[0].status)

        self.assertEqual("3", self.project.stepsProgress.steps[1].status)
        self.assertEqual(
            "2", self.project.stepsProgress.steps[1]['approvalHistory'][0].status)

        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(0, self.project.stepsProgress.general)

        projectApproval = RequestProjectApproval.objects().first()

        res = self.client().get(
            '/requestsprojectapproval')
        self.assertEqual(res.status_code, 200)
        result = json.loads(res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(1, len(result['records']))

        self.assertEqual(str(projectApproval.id), result['records'][0]['id'])
        self.assertEqual('0000001', result['records'][0]['code'])
        self.assertEqual('1', result['records'][0]['status'])

        res = self.client().put(
            '/requestsprojectapproval/{}'.format(projectApproval.id),
            data=json.dumps({"status": "2"}),
            content_type='application/json')
        self.assertEqual(res.status_code, 200)

        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(100, self.project.stepsProgress.general)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
