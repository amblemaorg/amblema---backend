# app/schemas/shared_schemas.py


import json

from marshmallow import Schema, EXCLUDE, post_load, pre_load
from app.schemas import fields
from flask import current_app

from app.models.state_model import State, Municipality
from app.models.specialty_teacher_model import SpecialtyTeacher
from app.models.work_position_model import WorkPosition
from app.helpers.ma_schema_validators import OneOf, only_numbers, validate_email
from app.helpers.ma_schema_fields import MAReferenceField


class TeacherSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str()
    lastName = fields.Str()
    cardId = fields.Str(validate=only_numbers)
    cardType = fields.Str(
        validate=OneOf(
            ('1', '2'),
            ('V', 'E')
        ))
    gender = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('female', 'male')
        ))
    email = fields.Str(required=True, validate=validate_email)
    phone = fields.Str(validate=only_numbers)
    addressState = MAReferenceField(document=State)
    addressMunicipality = MAReferenceField(
        document=Municipality)
    specialty = MAReferenceField(
        document=SpecialtyTeacher, allow_none=True)
    workPosition = MAReferenceField(
        document=WorkPosition, allow_none=True)
    
    address = fields.Str()
    addressCity = fields.Str()
    status = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('active', 'inactive')
        ))
    annualPreparationStatus = fields.Str(
        dump_only=True
    )
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
