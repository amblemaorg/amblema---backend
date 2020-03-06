# manage.py


from datetime import datetime
from app import db
import os
from flask import Flask
from flask_script import Manager

from app import create_app, db
from app.models.role_model import Role
from app.models.user_model import User

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


if __name__ == "__main__":
    manager.run()
