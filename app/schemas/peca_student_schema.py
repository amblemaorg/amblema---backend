# app/schemas/peca_student_schema.py


from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_numbers, OneOf, Range, validate_url, validate_email)


class DiagnosticSchema(Schema):
    multiplicationsPerMin = fields.Int(min=0)
    multiplicationsPerMinIndex = fields.Float(dump_only=True)
    operationsPerMin = fields.Int(min=0)
    operationsPerMinIndex = fields.Float(dump_only=True)
    wordsPerMin = fields.Int(min=0)
    wordsPerMinIndex = fields.Float(dump_only=True)
    readingDate = fields.DateTime(dump_only=True)
    mathDate = fields.DateTime(dump_only=True)
    logicDate = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class StudentSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str(required=True)
    lastName = fields.Str(required=True)
    cardId = fields.Str(validate=only_numbers)
    cardType = fields.Str(
        validate=OneOf(
            ('1', '2'),
            ('V', 'E')
        ))
    birthdate = fields.DateTime(required=True)
    gender = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('female', 'male')
        ))
    lapse1 = fields.Nested(DiagnosticSchema(), dump_only=True)
    lapse2 = fields.Nested(DiagnosticSchema(), dump_only=True)
    lapse3 = fields.Nested(DiagnosticSchema(), dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
