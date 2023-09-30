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
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.peca_student_model import SectionClass
from app.models.school_year_model import SchoolYear

class DiagnosticSchema(Schema):
    multiplicationsPerMin = fields.Int(allow_none=True)
    multiplicationsPerMinIndex = fields.Decimal(
        dump_only=True, places=2, as_string=True)
    operationsPerMin = fields.Int(allow_none=True)
    operationsPerMinIndex = fields.Decimal(
        dump_only=True, places=2, as_string=True)
    wordsPerMin = fields.Int(allow_none=True)
    wordsPerMinIndex = fields.Decimal(
        dump_only=True, places=2, as_string=True)
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

class SectionClassSchema(Schema):
    id = fields.Str(dump_only=True)
    grade = fields.Str(
        required=True,
        validate=OneOf(
            ('0', '1', '2', '3', '4', '5', '6'),
            ('preschool', '1', '2', '3', '4', '5', '6')
        ))
    name = fields.Str(required=True)
    schoolYear = MAReferenceField(document=SchoolYear, required=True)

class StudentClassSchema(Schema):
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
    sections = fields.List(fields.Nested(SectionClassSchema()))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
