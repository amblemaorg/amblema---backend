# manage.py


from datetime import datetime
from app import db
import os
from flask import Flask
from flask_script import Manager

from app import create_app, db
from app.models.role_model import Role, Permission, ActionHandler
from app.models.entity_model import Entity
from app.models.user_model import User
from app.models.school_year_model import SchoolYear
from app.models.step_model import Step

app = create_app(config_instance=os.getenv('INSTANCE'))
app.app_context().push()
db = db

manager = Manager(app)


@manager.command
def create_super_user(email, password):
    role = Role.objects(devName="superadmin").first()
    if not role:
        return "Super admin role is required"
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
        user.setHashPassword()
        user.save()


@manager.command
def create_entity_actions():
    from app.helpers.handler_seeds import create_entities
    create_entities()


@manager.command
def create_standard_roles():
    from app.helpers.handler_seeds import create_standard_roles
    return create_standard_roles()


@manager.command
def create_initial_steps():
    from app.helpers.handler_seeds import create_initial_steps
    return create_initial_steps()


@manager.command
def create_initial_schoolyear(startDate, endDate):
    """
    Script for create a initial school year   
    Params:
      startDate: str yyyy-mm-dd
      endDateL str yyyy-mm-dd"""

    ys, ms, ds = startDate.split("-")
    ye, me, de = endDate.split("-")
    schoolYear = SchoolYear(
        name="Año Escolar " + str(ys)+" - "+str(ye),
        startDate=startDate,
        endDate=endDate)
    schoolYear.save()


@manager.command
def create_peca_setting():
    from app.models.school_year_model import SchoolYear
    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    if schoolYear:
        if not schoolYear.pecaSetting:
            schoolYear.initFirstPecaSetting()
            schoolYear.save()


if __name__ == "__main__":
    manager.run()
