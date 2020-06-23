# app/schemas/peca_section_schema.py


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
from app.models.peca_section_model import TeacherLink
from app.schemas.peca_student_schema import StudentSchema
from app.schemas.goal_setting_schema import GradeSettingSchema


class TeacherLinkSchema(Schema):
    id = fields.Str()
    firstName = fields.Str()
    lastName = fields.Str()

    @post_load
    def make_action(self, data, **kwargs):
        return TeacherLink(**data)


class DiagnosticSumarySchema(Schema):
    wordsPerMin = fields.Float(default=0, dump_only=True)
    wordsPerMinIndex = fields.Float(default=0, dump_only=True)
    multiplicationsPerMin = fields.Float(default=0, dump_only=True)
    multiplicationsPerMinIndex = fields.Float(default=0, dump_only=True)
    operationsPerMin = fields.Float(default=0, dump_only=True)
    operationsPerMinIndex = fields.Float(default=0, dump_only=True)


class DiagnosticsSchema(Schema):
    lapse1 = fields.Nested(DiagnosticSumarySchema, dump_only=True)
    lapse2 = fields.Nested(DiagnosticSumarySchema, dump_only=True)
    lapse3 = fields.Nested(DiagnosticSumarySchema, dump_only=True)


class SectionSchema(Schema):
    id = fields.Str(dump_only=True)
    grade = fields.Str(
        required=True,
        validate=OneOf(
            ('0', '1', '2', '3', '4', '5', '6'),
            ('preschool', '1', '2', '3', '4', '5', '6')
        ))
    name = fields.Str(required=True)
    students = fields.List(fields.Nested(StudentSchema()), dump_only=True)
    teacher = fields.Nested(TeacherLinkSchema())
    diagnostics = fields.Nested(DiagnosticsSchema, dump_only=True)
    goals = fields.Nested(GradeSettingSchema, dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
