# app/models/user_model.py


from datetime import datetime

from flask_bcrypt import Bcrypt
from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    EmailField,
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
    ReferenceField,
    SortedListField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import (
    Schema,
    fields,
    pre_load,
    post_load,
    EXCLUDE,
    validate)

from app.helpers.ma_schema_validators import not_blank, only_letters, only_numbers
from app.helpers.ma_schema_fields import MAReferenceField
from app.helpers.error_helpers import RegisterNotFound
from app.services.generic_service import getRecordOr404
from app.models.role_model import Role
from app.models.state_model import State, Municipality


class User(Document):
    email = EmailField(unique=True, required=True)
    password = StringField(required=True)
    firstName = StringField(required=True)
    lastName = StringField(required=True)
    userType= StringField(required=True)
    phone = StringField(required=True)
    role = ReferenceField('Role', required=True)
    addressState = ReferenceField('State', required=True)
    addressMunicipality = ReferenceField('Municipality')
    address = StringField()
    state = StringField(default='1')
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    status = BooleanField(default=True)

    def clean(self):
        """Initialize the user"""
        if not self.pk:
            self.password = Bcrypt().generate_password_hash(self.password).decode()

    def setHashPassword(self):
        """Set a hashed password"""
        self.password = Bcrypt().generate_password_hash(self.password).decode()

    def password_is_valid(self, password):
        """
        Checks the password against it's hash to validates the user's password
        """
        return Bcrypt().check_password_hash(self.password, password)
        

    meta = {'allow_inheritance': True}


class AdministratorUser(User):
    cardType = StringField(required=True)
    cardId = StringField(required=True)
    function = StringField(required=True)


class CoordinatorUser(User):
    cardType = StringField(required=True)
    cardId = StringField(required=True)


class SponsorUser(User):
    cardType = StringField(required=True)
    cardId = StringField(required=True)


class SchoolUser(User):
    institutionCode = StringField(required=True)
    institutionPhone = StringField(required=True)


"""
SCHEMAS FOR MODELS 
"""

class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Email(required=True, validate=not_blank)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=(
            not_blank,
            validate.Length(equal=8)))
    firstName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    lastName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    userType = fields.Str(
        required=True,
        validate=(
            not_blank,
            only_numbers,
            validate.OneOf(
                ["1", "2","3","4"],
                ["admin", "coordinator", "sponsor", "school"]
            )))
    phone = fields.Str()
    role = MAReferenceField(required=True)
    addressState = MAReferenceField(required=True)
    addressMunicipality = MAReferenceField(required=True)
    address = fields.Str()
    state = fields.Str(validate=validate.OneOf(["1","2"]))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "role" in data:
            role = getRecordOr404(Role,data['role'])
            data['role'] = role
        if "addressState" in data:
            state = getRecordOr404(State,data['addressState'])
            data['addressState'] = state
        if "addressMunicipality" in data:
            municipality = getRecordOr404(Municipality,data['addressMunicipality'])
            data['addressMunicipality'] = municipality
        if 'email' in data:
            data["email"] = str(data["email"]).lower()
        if 'firstName' in data:
            data["firstName"] = str(data["firstName"]).title()
        if 'lastName' in data:
            data["lastName"] = str(data["lastName"]).title()
        if 'address' in data:
            data["address"] = str(data["address"]).title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True


class AdminUserSchema(UserSchema):
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            validate.OneOf(
                ["1", "2","3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank,only_numbers))
    function = fields.Str(required=True, validate=not_blank)


class CoordinatorUserSchema(UserSchema):
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            validate.OneOf(
                ["1", "2","3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank,only_numbers))


class SponsorUserSchema(UserSchema):
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            validate.OneOf(
                ["1", "2","3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank,only_numbers))


class SchoolUserSchema(UserSchema):
    institutionCode = fields.Str(required=True, validate=not_blank)
    institutionPhone = fields.Str()