# app/schemas/peca_project_schema.py


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
    not_blank, only_numbers, OneOf, Range, validate_url)
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality
from app.schemas.shared_schemas import ProjectReferenceSchema


class StudentSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str(required=True)
    lastName = fields.Str(required=True)
    birthdate = fields.DateTime(required=True)
    gender = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('female', 'male')
        ))


class SectionSchema(Schema):
    id = fields.Str(dump_only=True)
    grade = fields.Str(
        required=True,
        validate=(
            OneOf(('1', '2', '3', '4', '5', '6'))
        ))
    name = fields.Str(required=True)
    students = fields.List(fields.Nested(StudentSchema()), dump_only=True)


class SchoolSchema(Schema):
    name = fields.Str(dump_only=True)
    code = fields.Str(dump_only=True)
    addressState = MAReferenceField(document=State, dump_only=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, dump_only=True)
    addressStreet = fields.Str(dump_only=True)
    addressCity = fields.Str(dump_only=True)
    principalFirstName = fields.Str(required=True)
    principalLastName = fields.Str(required=True)
    principalEmail = fields.Email(required=True)
    principalPhone = fields.Str(required=True, validate=only_numbers)
    subPrincipalFirstName = fields.Str()
    subPrincipalLastName = fields.Str()
    subPrincipalEmail = fields.Email()
    subPrincipalPhone = fields.Str(validate=only_numbers)
    nTeachers = fields.Int(validate=Range(min=0))
    nGrades = fields.Int(validate=Range(min=0))
    nStudents = fields.Int(validate=Range(min=0))
    nAdministrativeStaff = fields.Int(
        validate=Range(min=0))
    nLaborStaff = fields.Int(validate=Range(min=0))
    facebook = fields.Str(validate=validate_url)
    instagram = fields.Str()
    twitter = fields.Str()
    sections = fields.List(fields.Nested(SectionSchema()), dump_only=True)


class PecaProjectSchema(Schema):
    schoolYear = fields.Str()
    schoolYearName = fields.Str()
    project = fields.Nested(ProjectReferenceSchema)
    school = fields.Nested(SchoolSchema)
