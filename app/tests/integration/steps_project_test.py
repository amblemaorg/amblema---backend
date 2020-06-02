# app/tests/integration/request_find_school_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.shared_embedded_documents import CheckTemplate, Link


class InitialSteps(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-02-14",
            endDate="2020-09-14")
        self.schoolYear.save()

        self.generalSteps = []
        for i in range(2):
            generalStep = Step(
                name="step {}".format(str(i)),
                hasText=True,
                text="step description {}".format(str(i)),
                tag="1",
                approvalType="1"
            )
            generalStep.save()
            self.generalSteps.append(generalStep)
        for i in range(5):
            schoolStep = Step(
                name="step {}".format(str(i)),
                hasText=True,
                text="step description {}".format(str(i)),
                tag="2",
                approvalType="1"
            )
            schoolStep.save()
        for i in range(4):
            sponsorStep = Step(
                name="step {}".format(str(i)),
                hasText=True,
                text="step description {}".format(str(i)),
                tag="3",
                approvalType="1"
            )
            sponsorStep.save()
        for i in range(5):
            coordinatorStep = Step(
                name="step {}".format(str(i)),
                hasText=True,
                text="step description {}".format(str(i)),
                tag="4",
                approvalType="1"
            )
            coordinatorStep.save()

        coordinatorSendCurriculum = Step(
            name="Enviar currículo vitae",
            devName="coordinatorSendCurriculum",
            tag="2",
            isStandard=True,
            approvalType="3",
            hasUpload=True,
            hasText=True,
            text="some description"

        )
        coordinatorSendCurriculum.save()

        corrdinatorCompleteTrainingModules = Step(
            name="Completar módulos de formación",
            devName="corrdinatorCompleteTrainingModules",
            tag="2",
            isStandard=True,
            approvalType="2"
        )
        corrdinatorCompleteTrainingModules.save()

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
            isReferred=False,
            curriculum=Link(
                url="https://someurl.com/file.pdf",
                name="some file name"
            ),
            instructed=True
        )
        self.coordinator.save()

    def test_create_initial_steps_on_create_project(self):

        self.project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        self.project.save()

        self.assertEqual(18, len(self.project.stepsProgress.steps))

        curriculumStep = self.project.stepsProgress.steps.filter(
            devName="coordinatorSendCurriculum").first()
        self.assertEqual(
            "some file name", curriculumStep.approvalHistory[0].data['stepUploadedFile']['name'])
        self.assertEqual("3", curriculumStep.status)

        instructedStep = self.project.stepsProgress.steps.filter(
            devName="corrdinatorCompleteTrainingModules").first()
        self.assertEqual("3", curriculumStep.status)

    def test_update_project_steps_on_create_new_step(self):
        project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        project.save()
        self.assertEqual(18, len(project.stepsProgress.steps))

        generalStep = Step(
            name="new step",
            hasText=True,
            text="new step description",
            tag="1",
            approvalType="1"
        )
        generalStep.save()

        project = Project.objects.get(id=str(project.id))
        self.assertEqual(19, len(project.stepsProgress.steps))

    def test_update_project_steps_on_delete_step(self):
        project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        project.save()
        self.assertEqual(18, len(project.stepsProgress.steps))

        step1 = self.generalSteps[0]
        step1.status = "2"
        step1.save()

        project = Project.objects.get(id=str(project.id))
        self.assertEqual(17, len(project.stepsProgress.steps))

        step1 = self.generalSteps[1]
        step1.isDeleted = True
        step1.save()

        project = Project.objects.get(id=str(project.id))
        self.assertEqual(16, len(project.stepsProgress.steps))

    def test_update_project_steps_on_activate_step(self):
        project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        project.save()
        self.assertEqual(18, len(project.stepsProgress.steps))

        step1 = self.generalSteps[0]
        step1.status = "2"
        step1.save()

        project = Project.objects.get(id=str(project.id))
        self.assertEqual(17, len(project.stepsProgress.steps))

        step1 = self.generalSteps[0]
        step1.status = "1"
        step1.save()

        project = Project.objects.get(id=str(project.id))
        self.assertEqual(18, len(project.stepsProgress.steps))

    def test_update_value_steps(self):
        project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        project.save()

        stepId = project.stepsProgress.steps[0].id
        step = Step.objects.get(id=stepId)

        step.name = "new name"
        step.save()

        project = Project.objects.get(id=str(project.pk))
        self.assertEqual("new name", project.stepsProgress.steps[0].name)
        self.assertEqual("step 1", project.stepsProgress.steps[1].name)

    def test_checklist_step(self):
        project = Project(
            schoolYear=self.schoolYear,
            coordinator=self.coordinator
        )
        project.save()
        self.assertEqual(18, len(project.stepsProgress.steps))

        check1 = CheckTemplate(name="check1")
        check2 = CheckTemplate(name="check2")
        generalStep = Step(
            name="new step",
            text="new step description",
            hasText=True,
            hasChecklist=True,
            approvalType="1",
            tag="1",
            checklist=[]
        )
        generalStep.checklist.append(check1)
        generalStep.checklist.append(check2)
        generalStep.save()

        checkId = ""
        for check in generalStep.checklist:
            if check.name == "check1":
                checkId = check.id

        project = Project.objects.get(id=str(project.id))
        self.assertEqual(
            "check1", project.stepsProgress.steps[18].checklist.filter(id=str(checkId)).first().name)

        for check in generalStep.checklist:
            if check.id == checkId:
                check.name = "check updated"
        generalStep.save()

        project = Project.objects.get(id=str(project.id))
        for check in project.stepsProgress.steps[18].checklist:
            if check.id == checkId:
                self.assertEqual(
                    "check updated", check.name)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
