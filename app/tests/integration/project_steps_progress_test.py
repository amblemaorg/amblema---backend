# app/tests/project_steps_progress_test.py


import unittest
import json
from datetime import datetime

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step, Check
from app.models.coordinator_user_model import CoordinatorUser, Answer
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project, StepControl, CheckElement
from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.models.learning_module_model import LearningModule, Quiz
from app.models.request_step_approval_model import RequestStepApproval


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

        self.findSchool = Step(
            name="Encontrar Escuela",
            devName="findSchool",
            tag="1",
            hasText=True,
            isStandard=True,
            approvalType="3",
            text="some description"
        )
        self.findSchool.save()

        self.findSponsor = Step(
            name="Encontrar Padrino",
            devName="findSponsor",
            tag="1",
            hasText=True,
            isStandard=True,
            approvalType="3",
            text="some description"
        )
        self.findSponsor.save()

        self.findCoordinator = Step(
            name="Encontrar Coordinador",
            devName="findCoordinator",
            tag="1",
            hasText=True,
            isStandard=True,
            approvalType="3",
            text="some description"
        )
        self.findCoordinator.save()

        self.amblemaConfirmation = Step(
            name="Confirmacion de AmbLeMa",
            devName="amblemaConfirmation",
            tag="1",
            isStandard=True,
            approvalType="1",
            hasText=True,
            text="some description"
        )
        self.amblemaConfirmation.save()

        self.coordinatorFillSchoolForm = Step(
            name="Rellenar planilla de escuela",
            devName="coordinatorFillSchoolForm",
            tag="2",
            isStandard=True,
            approvalType="3",
            hasText=True,
            text="some description"
        )
        self.coordinatorFillSchoolForm.save()

        self.coordinatorFillSponsorForm = Step(
            name="Rellenar planilla de padrino",
            devName="coordinatorFillSponsorForm",
            tag="2",
            isStandard=True,
            approvalType="3",
            hasText=True,
            text="some description"
        )
        self.coordinatorFillSponsorForm.save()

        self.coordinatorSendCurriculum = Step(
            name="Enviar curriculo Vitae",
            devName="coordinatorSendCurriculum",
            tag="2",
            isStandard=True,
            approvalType="3",
            hasUpload=True,
            hasText=True,
            text="some description"

        )
        self.coordinatorSendCurriculum.save()

        self.corrdinatorCompleteTrainingModules = Step(
            name="Completar modulos de formacion",
            devName="corrdinatorCompleteTrainingModules",
            tag="2",
            isStandard=True,
            approvalType="2"
        )
        self.corrdinatorCompleteTrainingModules.save()

        self.checklistInitialWorkshop = Step(
            name="Taller inicial",
            tag="2",
            hasText=True,
            hasChecklist=True,
            text="some description",
            checklist=[{"name": "Reunion con la escuela"},
                       {"name": "reunion con el padrino"}],
            approvalType="2"
        )
        self.checklistInitialWorkshop.save()

        self.sponsorFillSchoolForm = Step(
            name="Rellenar planilla de escuela",
            devName="sponsorFillSchoolForm",
            tag="3",
            isStandard=True,
            approvalType="3",
            hasText=True,
            text="some description"
        )
        self.sponsorFillSchoolForm.save()

        self.sponsorFillCoordinatorForm = Step(
            name="Rellenar planilla de coordinador",
            devName="sponsorFillCoordinatorForm",
            tag="3",
            isStandard=True,
            approvalType="3",
            hasText=True,
            text="some description"
        )
        self.sponsorFillCoordinatorForm.save()

        self.sponsorAgreementSchool = Step(
            name="Convenio Padrino - Escuela",
            devName="sponsorAgreementSchool",
            tag="3",
            isStandard=True,
            approvalType="3",
            hasText=True,
            hasFile=True,
            hasUpload=True,
            text="some description",
            file={"name": "Agreement name",
                  "url": "https://urlserver.com/files/asd.pdf"}
        )
        self.sponsorAgreementSchool.save()

        self.sponsorAgreementSchoolFoundation = Step(
            name="Convenio Escuela - Fundacion",
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
        )
        self.sponsorAgreementSchoolFoundation.save()

        self.schoolFillSponsorlForm = Step(
            name="Rellenar planilla de padrino",
            devName="schoolFillSponsorlForm",
            tag="4",
            isStandard=True,
            approvalType="3",
            hasText=True,
            text="some description"
        )
        self.schoolFillSponsorlForm.save()

        self.schoolFillCoordinatorForm = Step(
            name="Rellenar planilla de coordinador",
            devName="schoolFillCoordinatorForm",
            tag="4",
            isStandard=True,
            approvalType="3",
            hasText=True,
            text="some description"
        )
        self.schoolFillCoordinatorForm.save()

        self.schoolAgreementSponsor = Step(
            name="Convenio Escuela - Padrino",
            devName="schoolAgreementSponsor",
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
        self.schoolAgreementSponsor.save()

        self.schoolAgreementFoundation = Step(
            name="Convenio Escuela - Fundacion",
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

        self.schoolStepText = Step(
            name="School Step only text",
            tag="4",
            hasText=True,
            approvalType="1",
            text="some description"
        )
        self.schoolStepText.save()

        self.schoolStepDate = Step(
            name="School Step with date",
            tag="4",
            approvalType="2",
            hasDate=True
        )
        self.schoolStepDate.save()

        self.schoolStepFile = Step(
            name="School Step with file",
            tag="4",
            approvalType="2",
            hasFile=True,
            file={"name": "filename", "url": "https://somedomainname.com/file.pdf"},
            hasUpload=True
        )
        self.schoolStepFile.save()

        self.schoolStepDateFile = Step(
            name="School Step Date file",
            tag="4",
            approvalType="3",
            hasFile=True,
            hasDate=True,
            file={"name": "filename", "url": "https://somedomainname.com/file.pdf"}
        )
        self.schoolStepDateFile.save()

        self.schoolStepChecklist = Step(
            name="School Step checklist",
            tag="4",
            approvalType="2",
            hasChecklist=True,
            checklist=[{"name": "find lema"}, {
                "name": "meeting with teachers"}]
        )
        self.schoolStepChecklist.save()

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
        self.coordinator.save()

    def test_update_project_steps(self):

        # create project
        self.project = Project(
            coordinator=self.coordinator
        )
        self.project.save()
        self.assertEqual(22, len(self.project.stepsProgress.steps))

        # update step text
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepText.id),
                status="3"  # approved
            )
        )

        # update step date
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepDate.id),
                date="2020-02-20"
            )
        )

        # update step file
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepFile.id),
                uploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
            )
        )

        # update step date file (approval process)
        approvalRequest = RequestStepApproval(
            stepId=str(self.schoolStepDateFile.id),
            project=self.project,
            stepUploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"},
            stepDate="2020-02-20"
        )
        approvalRequest.save()
        approvalRequest.status = "2"
        approvalRequest.save()
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepDateFile.id),
                uploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"},
                date="2020-02-20"
            )
        )

        # update step checklist
        checklist = []
        for check in self.schoolStepChecklist.checklist:
            checklist.append(
                CheckElement(
                    id=str(check.id),
                    name=check.name,
                    checked=True
                )
            )
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepChecklist.id),
                checklist=checklist
            )
        )

        # standard step is approved automatically: schoolFillCoordinatorForm
        approvedSteps = 0
        for step in self.project.stepsProgress.steps:
            if step.tag == "4" and step.status == "3":
                approvedSteps += 1
        self.assertEqual(6, approvedSteps)

        # Check progress
        self.assertEqual(66.67, self.project.stepsProgress.school)
        self.assertEqual(25, self.project.stepsProgress.general)
        self.assertEqual(0, self.project.stepsProgress.coordinator)
        self.assertEqual(25, self.project.stepsProgress.sponsor)

        # Agreements steps
        # update step date file (approval process)
        approvalRequest = RequestStepApproval(
            stepId=str(self.schoolAgreementFoundation.id),
            project=self.project,
            stepUploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
        )
        approvalRequest.save()
        approvalRequest.status = "2"
        approvalRequest.save()

        approvalRequest = RequestStepApproval(
            stepId=str(self.sponsorAgreementSchool.id),
            project=self.project,
            stepUploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
        )
        approvalRequest.save()
        approvalRequest.status = "2"
        approvalRequest.save()

        self.project = Project.objects.get(id=self.project.id)
        self.assertEqual(75, self.project.stepsProgress.sponsor)

        self.assertEqual(88.89, self.project.stepsProgress.school)

        # coordinatorSendCurriculum
        approvalRequest = RequestStepApproval(
            stepId=str(self.coordinatorSendCurriculum.id),
            project=self.project,
            stepUploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
        )
        approvalRequest.save()
        approvalRequest.status = "2"
        approvalRequest.save()

        self.project = Project.objects.get(id=self.project.id)
        self.assertEqual(20, self.project.stepsProgress.coordinator)
        self.coordinator = CoordinatorUser.objects().get(id=str(self.coordinator.id))
        self.assertEqual("https://server.com/files/asd.pdf",
                         self.coordinator.curriculum.url)
        self.assertEqual("1", self.coordinator.status)

        self.learningModule = LearningModule(
            name="module name",
            title="module for test",
            description="module description test",
            secondaryTitle="secondaryTitle",
            secondaryDescription="secondaryDescription",
            objectives=["first objective", "second objective"],
            slider=[{"url": "https://youtube.com",
                     "description": "some description", "type": "2"}],
            images=[{"image": "http://localhost:10505/resources/images/learningmodules/5e4edc7edb90150c560b2dc1.png",
                     "description": "some description"}],
            duration=3600)
        self.learningModule.quizzes.append(
            Quiz(
                question="cual es el lema de amblema?",
                optionA="HQS",
                optionB="HP",
                optionC="HMH",
                optionD="QAS",
                correctOption="optionA")
        )
        self.learningModule.save()

        # correct answer
        result = self.coordinator.tryAnswerLearningModule(
            self.learningModule,
            [
                Answer(
                    quizId=self.learningModule.quizzes[0].id,
                    option="optionA")
            ]
        )
        self.assertEqual(result["approved"], True)

        self.coordinator = CoordinatorUser.objects().get(id=str(self.coordinator.id))
        self.assertEqual("3", self.coordinator.status)

        self.project = Project.objects.get(id=self.project.id)
        self.assertEqual(40, self.project.stepsProgress.coordinator)

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

        self.project.sponsor = sponsor
        self.project.save()

        self.assertEqual(60, self.project.stepsProgress.coordinator)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
