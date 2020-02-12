# app/sponsor_contact_schema.py


from marshmallow import (
    Schema,
    fields,
    pre_load,
    EXCLUDE,
    validate)

from app.helpers.ma_schema_validators import not_blank, only_numbers
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality


class SponsorContactSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    email = fields.Email(required=True, validate=not_blank)
    rif = fields.Str(required=True, validate=only_numbers)
    companyType = fields.Str(required=True)
    phone = fields.Str(required=True, validate=only_numbers)
    address = fields.Str(required=True, validate=not_blank)
    addressState = MAReferenceField(required=True, document=State)
    addressMunicipality = MAReferenceField(
        required=True, document=Municipality)
    addressCity = fields.Str(required=True)
    addressStreet = fields.Str()
    contactName = fields.Str(required=True, validate=not_blank)
    contactPhone = fields.Str(required=True, validate=not_blank)
    schoolContact = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1', '2', '3', '4'),
            ('director', 'teacher', 'parent', 'neighbor')
        ))
    schoolContactName = fields.Str(required=True, validate=not_blank)
    state = fields.Str(
        default="1",
        validate=validate.OneOf(
            ('1', '2', '3'),
            ('pending', 'acepted', 'rejected')
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
