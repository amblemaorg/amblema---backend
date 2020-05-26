# app/schemas/request_find_sponsor_schema.py


from marshmallow import (
    Schema,
    pre_load,
    EXCLUDE,
    validate)

from app.schemas import fields
from app.models.user_model import User
from app.models.request_find_sponsor_model import Project
from app.helpers.ma_schema_fields import MAReferenceField
from app.helpers.ma_schema_validators import not_blank, only_numbers, OneOf, only_letters, validate_email
from app.models.state_model import State, Municipality


class ReqFindSponsorSchema(Schema):
    id = fields.Str(dump_only=True)
    requestCode = fields.Function(lambda obj: obj.requestCode.zfill(7))
    project = MAReferenceField(required=True, document=Project, field="code")
    user = MAReferenceField(required=True, document=User, field="name")
    name = fields.Str(required=True, validate=not_blank)
    email = fields.Str(required=True, validate=(not_blank, validate_email))
    rif = fields.Str(required=True, validate=only_numbers)
    companyType = fields.Str(
        required=True,
        validate=OneOf(
            ('0', '1', '2', '3', '4'),
            ('other', 'factory', 'grocery', 'personal business', 'estate')
        ))
    companyOtherType = fields.Str()
    companyPhone = fields.Str(required=True, validate=only_numbers)
    address = fields.Str()
    addressState = MAReferenceField(required=True, document=State)
    addressMunicipality = MAReferenceField(
        required=True, document=Municipality)
    addressCity = fields.Str()
    contactFirstName = fields.Str(validate=(not_blank, only_letters))
    contactLastName = fields.Str(validate=(not_blank, only_letters))
    contactEmail = fields.Str(validate=validate_email)
    contactPhone = fields.Str(required=True, validate=not_blank)
    status = fields.Str(
        default="1",
        validate=OneOf(
            ('1', '2', '3'),
            ('pending', 'accepted', 'rejected')
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].title()
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower()
        return data

    class Meta:
        unknown = EXCLUDE
        ordered = True
