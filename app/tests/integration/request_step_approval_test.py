# app/tests/integration/request_find_school_test.py


import unittest
import json
import io
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step
from app.models.coordinator_user_model import CoordinatorUser
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.request_step_approval_model import RequestStepApproval


class StepApprovalTest(unittest.TestCase):
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

        self.generalStep = Step(
            name="step upload general",
            hasText=True,
            hasUpload=True,
            text="step description",
            tag="1",
            approvalType="3"
        )
        self.generalStep.save()

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

        self.project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        self.project.save()
        self.assertEqual(1, len(self.project.stepsProgress.steps))

    def test_endpoint_step_approval(self):
        requestData = dict(
            project=str(self.project.pk),
            stepId=str(self.generalStep.pk),
            stepUploadedFile=(io.BytesIO(b'hi everyone'), 'test.pdf')
        )

        res = self.client().post(
            '/requestsstepapproval',
            data=requestData,
            content_type='multipart/form-data')
        approval_request = json.loads(
            res.data.decode('utf8').replace("'", '"'))

        self.assertEqual(res.status_code, 201)

        res = self.client().put(
            '/requestsstepapproval/{}'.format(approval_request['id']),
            data={"status": "2"})
        self.assertEqual(res.status_code, 200)

        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(
            "3", self.project.stepsProgress.steps[0].status)

    def test_update_step_on_approval(self):
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
        self.assertEqual(self.generalStep.name, reqStepApproval.stepName)
        self.assertEqual(self.generalStep.devName, reqStepApproval.stepDevName)
        self.assertEqual(self.generalStep.hasUpload,
                         reqStepApproval.stepHasUpload)

        # approved
        reqStepApproval.status = "2"
        reqStepApproval.save()
        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(
            "3", self.project.stepsProgress.steps[0].status)

    def test_update_step_on_rejected(self):
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

        self.assertEqual(
            "2", self.project.stepsProgress.steps[0].status)

        # check fill of the step fields on approval
        self.assertEqual(self.generalStep.name, reqStepApproval.stepName)
        self.assertEqual(self.generalStep.devName, reqStepApproval.stepDevName)
        self.assertEqual(self.generalStep.hasUpload,
                         reqStepApproval.stepHasUpload)

        # rejected
        reqStepApproval.status = "3"
        reqStepApproval.comments = "Something is wrong!"
        reqStepApproval.save()
        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(
            "1", self.project.stepsProgress.steps[0].status)
        self.assertEqual(
            "3", self.project.stepsProgress.steps[0].approvalHistory[0].status)
        self.assertEqual(
            reqStepApproval.comments, self.project.stepsProgress.steps[0].approvalHistory[0].comments)

    def test_update_step_on_cancelled(self):
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

        self.assertEqual(
            "2", self.project.stepsProgress.steps[0].status)

        # check fill of the step fields on approval
        self.assertEqual(self.generalStep.name, reqStepApproval.stepName)
        self.assertEqual(self.generalStep.devName, reqStepApproval.stepDevName)
        self.assertEqual(self.generalStep.hasUpload,
                         reqStepApproval.stepHasUpload)

        # cancelled
        reqStepApproval.status = "4"
        reqStepApproval.save()
        self.project = Project.objects.get(id=self.project.pk)
        self.assertEqual(
            "1", self.project.stepsProgress.steps[0].status)
        self.assertEqual(
            "4", self.project.stepsProgress.steps[0].approvalHistory[0].status)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
