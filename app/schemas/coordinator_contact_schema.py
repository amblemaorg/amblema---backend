# app/schemas/coordinator_contact_schema.py


from marshmallow import (
    Schema,
    fields,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import not_blank, only_numbers
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality


class CoordinatorContactSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str(required=True, validate=not_blank)
    lastName = fields.Str(required=True, validate=not_blank)
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            validate.OneOf(
                ["1", "2", "3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank, only_numbers))
    birthdate = fields.Date(required=True)
    gender = fields.Str(
        required=True,
        validate=validate.OneOf(
            ('1', '2'),
            ('female', 'male')
        ))
    addressState = MAReferenceField(document=State, required=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, required=True)
    addressCity = fields.Str(required=True, validate=not_blank)
    addressStreet = fields.Str()
    addressHome = fields.Str()
    email = fields.Email(required=True, validate=not_blank)
    phone = fields.Str(required=True, validate=(not_blank, only_numbers))
    homePhone = fields.Str(validate=only_numbers, required=True)
    profession = fields.Str(required=True, validate=not_blank)
    referredName = fields.Str(required=True, validate=not_blank)
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
        toTitle = (
            'firstName',
            'lastName',
            'addressCity',
            'addressStreet',
            'addressHome',
            'profession',
            'referredName'
        )
        for field in toTitle:
            if field in data:
                data[field] = data[field].title()
        if 'email' in data:
            data["email"] = data["email"].lower()
        return data

    class Meta:
        unknown = EXCLUDE
        ordered = True
