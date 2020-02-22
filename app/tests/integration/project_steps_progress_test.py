# app/tests/project_steps_progress_test.py


import unittest
import json

from app import create_app, db

from app.models.school_year_model import SchoolYear
from app.models.step_model import Step, Check
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.project_model import Project, StepControl, CheckElement
from app.models.role_model import Role
from app.models.state_model import State, Municipality


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
            type="1",
            tag="1",
            text="some description",
            isStandard=True
        )
        self.findSchool.save()

        self.findSponsor = Step(
            name="Encontrar Padrino",
            devName="findSponsor",
            type="1",
            tag="1",
            text="some description",
            isStandard=True
        )
        self.findSponsor.save()

        self.findCoordinator = Step(
            name="Encontrar Coordinador",
            devName="findCoordinator",
            type="1",
            tag="1",
            text="some description",
            isStandard=True
        )
        self.findCoordinator.save()

        self.initialWorkshopPlanning = Step(
            name="Planificacion taller inicial",
            type="4",
            tag="1",
            text="some description",
            date="2020-02-20",
            file={"url": "http://somefile.com/file.pdf",
                  "name": "Planificacion inicial"}
        )
        self.initialWorkshopPlanning.save()

        self.amblemaConfirmation = Step(
            name="Confirmacion de AmbLeMa",
            devName="amblemaConfirmation",
            type="1",
            tag="1",
            text="some description",
            isStandard=True
        )
        self.amblemaConfirmation.save()

        self.coordinatorFillSchoolForm = Step(
            name="Rellenar planilla de escuela",
            devName="coordinatorFillSchoolForm",
            type="6",
            tag="2",
            text="some description",
            isStandard=True
        )
        self.coordinatorFillSchoolForm.save()

        self.coordinatorFillSponsorForm = Step(
            name="Rellenar planilla de padrino",
            devName="coordinatorFillSponsorForm",
            type="6",
            tag="2",
            text="some description",
            isStandard=True
        )
        self.coordinatorFillSponsorForm.save()

        self.coordinatorSendCurriculum = Step(
            name="Enviar curriculo Vitae",
            devName="coordinatorSendCurriculum",
            type="3",
            tag="2",
            text="some description",
            isStandard=True
        )
        self.coordinatorSendCurriculum.save()

        self.corrdinatorCompleteTrainingModules = Step(
            name="Completar modulos de formacion",
            devName="corrdinatorCompleteTrainingModules",
            type="1",
            tag="2",
            text="some description",
            isStandard=True
        )
        self.corrdinatorCompleteTrainingModules.save()

        self.checklistInitialWorkshop = Step(
            name="Completar modulos de formacion",
            devName="corrdinatorCompleteTrainingModules",
            type="5",
            tag="2",
            text="some description",
            checklist=[{"name": "Reunion con la escuela"},
                       {"name": "reunion con el padrino"}]
        )
        self.checklistInitialWorkshop.save()

        self.sponsorFillSchoolForm = Step(
            name="Rellenar planilla de escuela",
            devName="sponsorFillSchoolForm",
            type="6",
            tag="3",
            text="some description",
            isStandard=True
        )
        self.sponsorFillSchoolForm.save()

        self.sponsorFillCoordinatorForm = Step(
            name="Rellenar planilla de coordinador",
            devName="sponsorFillCoordinatorForm",
            type="6",
            tag="3",
            text="some description",
            isStandard=True
        )
        self.sponsorFillCoordinatorForm.save()

        self.sponsorAgreementSchool = Step(
            name="Convenio Padrino - Escuela",
            devName="sponsorAgreementSchool",
            type="3",
            tag="3",
            text="some description",
            isStandard=True,
            file={"name": "Agreement name",
                  "url": "https://urlserver.com/files/asd.pdf"}
        )
        self.sponsorAgreementSchool.save()

        self.sponsorAgreementSchoolFoundation = Step(
            name="Convenio Escuela - Fundacion",
            devName="sponsorAgreementSchoolFoundation",
            type="3",
            tag="3",
            text="some description",
            isStandard=True,
            file={"name": "Agreement name",
                  "url": "https://urlserver.com/files/asd.pdf"}
        )
        self.sponsorAgreementSchoolFoundation.save()

        self.schoolFillSponsorlForm = Step(
            name="Rellenar planilla de padrino",
            devName="schoolFillSponsorlForm",
            type="6",
            tag="4",
            text="some description",
            isStandard=True
        )
        self.schoolFillSponsorlForm.save()

        self.schoolFillCoordinatorForm = Step(
            name="Rellenar planilla de coordinador",
            devName="schoolFillCoordinatorForm",
            type="6",
            tag="4",
            text="some description",
            isStandard=True
        )
        self.schoolFillCoordinatorForm.save()

        self.schoolAgreementSponsor = Step(
            name="Convenio Escuela - Padrino",
            devName="schoolAgreementSponsor",
            type="3",
            tag="4",
            text="some description",
            isStandard=True,
            file={"name": "Agreement name",
                  "url": "https://urlserver.com/files/asd.pdf"}
        )
        self.schoolAgreementSponsor.save()

        self.schoolAgreementFoundation = Step(
            name="Convenio Escuela - Fundacion",
            devName="schoolAgreementFoundation",
            type="3",
            tag="4",
            text="some description",
            isStandard=True,
            file={"name": "Agreement name",
                  "url": "https://urlserver.com/files/asd.pdf"}
        )
        self.schoolAgreementFoundation.save()

        self.schoolStepType1 = Step(
            name="School Step type 1",
            type="1",
            tag="4",
            text="some description"
        )
        self.schoolStepType1.save()

        self.schoolStepType2 = Step(
            name="School Step type 2",
            type="2",
            tag="4",
            text="some description"
        )
        self.schoolStepType2.save()

        self.schoolStepType3 = Step(
            name="School Step type 3",
            type="3",
            tag="4",
            text="some description",
            file={"name": "filename", "url": "https://somedomainname.com/file.pdf"}
        )
        self.schoolStepType3.save()

        self.schoolStepType4 = Step(
            name="School Step type 4",
            type="4",
            tag="4",
            text="some description",
            file={"name": "filename", "url": "https://somedomainname.com/file.pdf"}
        )
        self.schoolStepType4.save()

        self.schoolStepType5 = Step(
            name="School Step type 5",
            type="5",
            tag="4",
            text="some description",
            checklist=[{"name": "find lema"}, {
                "name": "meeting with teachers"}]
        )
        self.schoolStepType5.save()

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
            birthdate="1993-09-08",
            homePhone="02343432323",
            addressHome="House 34A",
            email="testemail@test.com",
            password="12345678",
            userType="2",
            phone="02322322323",
            role=self.role,
            addressState=self.state,
            addressMunicipality=self.municipality
        )
        self.coordinator.save()

    def test_update_project_steps(self):

        # create project
        self.project = Project(
            coordinator=self.coordinator
        )
        self.project.save()
        self.assertEqual(23, len(self.project.stepsProgress.steps))

        # update step type 1
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepType1.id),
                status="2"
            )
        )

        # update step type 2
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepType2.id),
                date="2020-02-20"
            )
        )

        # update step type 3
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepType3.id),
                uploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
            )
        )

        # update step type 4
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepType4.id),
                uploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"},
                date="2020-02-20"
            )
        )

        # update step type 5
        checklist = []
        for check in self.schoolStepType5.checklist:
            checklist.append(
                CheckElement(
                    id=str(check.id),
                    name=check.name,
                    checked=True
                )
            )
        self.project.updateStep(
            StepControl(
                id=str(self.schoolStepType5.id),
                checklist=checklist
            )
        )

        # standard step is approved automatically: schoolFillCoordinatorForm
        approvedSteps = 0
        for step in self.project.stepsProgress.steps:
            if step.tag == "4" and step.status == "2":
                approvedSteps += 1
        self.assertEqual(6, approvedSteps)

        # Check progress
        self.assertEqual(66.67, self.project.stepsProgress.school)
        self.assertEqual(20, self.project.stepsProgress.general)
        self.assertEqual(0, self.project.stepsProgress.coordinator)
        self.assertEqual(25, self.project.stepsProgress.sponsor)

        # Agreements steps
        self.project.updateStep(
            StepControl(
                id=str(self.schoolAgreementFoundation.id),
                uploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
            )
        )
        self.project.updateStep(
            StepControl(
                id=str(self.sponsorAgreementSchool.id),
                uploadedFile={"name": "uploaded",
                              "url": "https://server.com/files/asd.pdf"}
            )
        )
        self.assertEqual(50, self.project.stepsProgress.sponsor)
        self.assertEqual(77.78, self.project.stepsProgress.school)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')


if __name__ == "__main__":
    unittest.main()
