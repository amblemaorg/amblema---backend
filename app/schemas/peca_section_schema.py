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


class TeacherLinkSchema(Schema):
    id = fields.Str()
    firstName = fields.Str()
    lastName = fields.Str()

    @post_load
    def make_action(self, data, **kwargs):
        return TeacherLink(**data)


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
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
