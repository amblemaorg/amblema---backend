# app/models/admin_user_model.py


from datetime import datetime

from flask import current_app
from mongoengine import fields

from app.models.user_model import User


class AdminUser(User):
    firstName = fields.StringField(required=True)
    lastName = fields.StringField(required=True)
    cardType = fields.StringField(required=True)
    cardId = fields.StringField(required=True, unique_c=True)
    phone = fields.StringField(required=True)
    function = fields.StringField(required=True)

    def clean(self):
        self.name = self.firstName + ' ' + self.lastName
