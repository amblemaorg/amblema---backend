# app/models/user_model.py


from datetime import datetime

from flask import current_app
from flask_bcrypt import Bcrypt
from mongoengine import Document, fields, signals, QuerySetManager, DynamicDocument

from app.models.role_model import Role
from app.models.state_model import State, Municipality


class User(DynamicDocument):
    objects = QuerySetManager()
    name = fields.StringField()
    email = fields.EmailField(unique=True, required=True)
    password = fields.StringField(required=True)
    userType = fields.StringField(required=True)
    phone = fields.StringField(required=True)
    role = fields.ReferenceField('Role', required=True)
    addressState = fields.ReferenceField('State', required=True)
    addressMunicipality = fields.ReferenceField('Municipality')
    addressCity = fields.StringField()
    address = fields.StringField()
    state = fields.StringField(default='1')
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    status = fields.BooleanField(default=True)

    def clean(self):
        """Initialize the user"""
        self.updatedAt = datetime.utcnow()

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        current_app.logger.info('user pre_save')
        if 'created' in kwargs and kwargs['created']:
            current_app.logger.info('Before created')
            document.setHashPassword()

    def setHashPassword(self):
        """Set a hashed password"""
        self.password = Bcrypt().generate_password_hash(self.password).decode()

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
        for permission in self.role.permissions:
            for action in permission.actions:
                if action.allowed:
                    permissions.append(action.name)
        return permissions

    meta = {
        'allow_inheritance': True,
        'collection': 'users'}


signals.pre_save_post_validation.connect(User.pre_save, sender=User)
