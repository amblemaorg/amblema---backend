# manage.py


from datetime import datetime
from app import db
import os
from flask import Flask
from flask_script import Manager

from app import create_app, db
from app.models.role_model import Role
from app.models.user_model import User
from app.models.school_year_model import SchoolYear
from app.models.step_model import Step

app = create_app(config_instance=os.getenv('INSTANCE'))
app.app_context().push()
db = db

manager = Manager(app)


@manager.command
def create_super_role():
    role = Role.objects(name='SuperAdmin').first()
    if not role:
        role = Role(name='SuperAdmin')
        role.save()
    return role


@manager.command
def create_super_user(email, password):
    role = create_super_role()
    user = User.objects(email=str(email).lower()).first()
    if not user:
        user = User(
            firstName="Super",
            lastName="Admin",
            name="Super Admin",
            email=str(email).lower(),
            password=str(password),
            cardType="1",
            cardId="00000000",
            birthdate=datetime.utcnow(),
            homePhone="07000000000",
            userType="0",
            phone="02322322323",
            role=role)
        user.save()


@manager.command
def create_initial_steps():
    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    if not schoolYear:
        return "An active school year is required"

    findSchool = Step(
        name="Encontrar Escuela",
        devName="findSchool",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna una escuela al proyecto"
    )
    findSchool.save()

    findSponsor = Step(
        name="Encontrar Padrino",
        devName="findSponsor",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna un padrino al proyecto"
    )
    findSponsor.save()

    findCoordinator = Step(
        name="Encontrar Coordinador",
        devName="findCoordinator",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna un coordinador al proyecto"
    )
    findCoordinator.save()

    amblemaConfirmation = Step(
        name="Confirmacion de AmbLeMa",
        devName="amblemaConfirmation",
        tag="1",
        isStandard=True,
        approvalType="1",
        hasText=True,
        text="some description"
    )
    amblemaConfirmation.save()

    coordinatorFillSchoolForm = Step(
        name="Rellenar planilla de escuela",
        devName="coordinatorFillSchoolForm",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    coordinatorFillSchoolForm.save()

    coordinatorFillSponsorForm = Step(
        name="Rellenar planilla de padrino",
        devName="coordinatorFillSponsorForm",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    coordinatorFillSponsorForm.save()

    coordinatorSendCurriculum = Step(
        name="Enviar curriculo Vitae",
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
        name="Completar modulos de formacion",
        devName="corrdinatorCompleteTrainingModules",
        tag="2",
        isStandard=True,
        approvalType="2"
    )
    corrdinatorCompleteTrainingModules.save()

    checklistInitialWorkshop = Step(
        name="Taller inicial",
        tag="2",
        hasText=True,
        hasChecklist=True,
        text="some description",
        checklist=[{"name": "Reunion con la escuela"},
                   {"name": "reunion con el padrino"}],
        approvalType="2"
    )
    checklistInitialWorkshop.save()

    sponsorFillSchoolForm = Step(
        name="Rellenar planilla de escuela",
        devName="sponsorFillSchoolForm",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    sponsorFillSchoolForm.save()

    sponsorFillCoordinatorForm = Step(
        name="Rellenar planilla de coordinador",
        devName="sponsorFillCoordinatorForm",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    sponsorFillCoordinatorForm.save()

    sponsorAgreementSchool = Step(
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
    sponsorAgreementSchool.save()

    sponsorAgreementSchoolFoundation = Step(
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
    sponsorAgreementSchoolFoundation.save()

    schoolFillSponsorlForm = Step(
        name="Rellenar planilla de padrino",
        devName="schoolFillSponsorlForm",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    schoolFillSponsorlForm.save()

    schoolFillCoordinatorForm = Step(
        name="Rellenar planilla de coordinador",
        devName="schoolFillCoordinatorForm",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    schoolFillCoordinatorForm.save()

    schoolAgreementSponsor = Step(
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
    schoolAgreementSponsor.save()

    schoolAgreementFoundation = Step(
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
    schoolAgreementFoundation.save()


if __name__ == "__main__":
    manager.run()
