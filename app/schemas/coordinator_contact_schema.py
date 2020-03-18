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

from app.helpers.ma_schema_validators import (
    not_blank, only_numbers, OneOf, validate_image)
from app.helpers.ma_schema_fields import MAReferenceField, MAImageField
from app.models.state_model import State, Municipality


class CoordinatorContactSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str(required=True, validate=not_blank)
    lastName = fields.Str(required=True, validate=not_blank)
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            OneOf(
                ["1", "2", "3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank, only_numbers))
    birthdate = fields.DateTime(required=True)
    gender = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('female', 'male')
        ))
    addressState = MAReferenceField(document=State, required=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, required=True)
    addressCity = fields.Str()
    addressStreet = fields.Str()
    addressHome = fields.Str()
    email = fields.Email(required=True, validate=not_blank)
    phone = fields.Str(required=True, validate=(not_blank, only_numbers))
    homePhone = fields.Str(validate=only_numbers, required=True)
    profession = fields.Str(required=True, validate=not_blank)
    isReferred = fields.Bool(required=True)
    referredName = fields.Str(validate=not_blank)
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
            if field in data and isinstance(data[field], str):
                data[field] = data[field].title()
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].lower()
        return data

    class Meta:
        unknown = EXCLUDE
        ordered = True
