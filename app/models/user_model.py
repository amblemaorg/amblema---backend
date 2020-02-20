# app/models/user_model.py


from datetime import datetime
import random
import string

from flask import current_app
from flask_bcrypt import Bcrypt
from mongoengine import Document, fields, signals, QuerySetManager, DynamicDocument

from app.models.role_model import Role
from app.models.state_model import State, Municipality
from app.helpers.handler_emails import send_email
from resources.email_templates.register_email import messageRegisterEmail


class User(DynamicDocument):
    objects = QuerySetManager()
    name = fields.StringField()
    email = fields.EmailField(unique_c=True, required=True)
    password = fields.StringField(required=True)
    userType = fields.StringField(required=True)
    phone = fields.StringField(required=True)
    role = fields.ReferenceField('Role', required=True)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality')
    addressCity = fields.StringField()
    address = fields.StringField()
    status = fields.StringField(default='1')
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    isDeleted = fields.BooleanField(default=False)

    def clean(self):
        """Initialize the user"""
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        current_app.logger.info('user pre_save')
        if not document.id:
            current_app.logger.info('Before created')
            document.setHashPassword()

    def setHashPassword(self):
        """Set a hashed password"""
        self.password = Bcrypt().generate_password_hash(self.password).decode()

    def generatePassword(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(8))

    def password_is_valid(self, password):
        """
        Checks the password against it's hash to validates the user's password
        """
        return Bcrypt().check_password_hash(self.password, password)

    def get_permissions(self):
        """
        Checks all available permissions for each entity
        """
        permissions = []
        if not self.role.isDeleted and self.role.status == "1":
            for permission in self.role.permissions:
                for action in permission.actions:
                    if action.allowed:
                        permissions.append(action.name)
        return permissions

    def sendRegistrationEmail(self, password):
        """
        Send email when a user is registered
        Params:
            password: str (user password)
        """
        if not current_app.config.get("TESTING"):
            send_email(
                messageRegisterEmail(self.email, password),
                'Amblema - Registro de usuario',
                self.email)

    meta = {
        'allow_inheritance': True,
        'collection': 'users'}


signals.pre_save.connect(User.pre_save, sender=User)
