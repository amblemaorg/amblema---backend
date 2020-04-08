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
    not_blank, only_numbers, OneOf, Range, validate_url, validate_email)
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality
from app.schemas.shared_schemas import ProjectReferenceSchema


class DiagnosticSchema(Schema):
    multitplicationsPerMin = fields.Int(min=0)
    multitplicationsPerMinIndex = fields.Float(dump_only=True)
    operationsPerMin = fields.Int(min=0)
    operationsPerMinIndex = fields.Float(dump_only=True)
    wordsPerMin = fields.Int(min=0)
    wordsPerMinIndex = fields.Float(dump_only=True)
    readingDate = fields.DateTime(dump_only=True)
    mathDate = fields.DateTime(dump_only=True)


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
    addressStreet = fields.Str()
    addressCity = fields.Str()
    status = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('active', 'inactive')
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)


class TeacherLinkSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str()
    lastName = fields.Str()


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
    principalEmail = fields.Str(required=True, validate=validate_email)
    principalPhone = fields.Str(required=True, validate=only_numbers)
    subPrincipalFirstName = fields.Str()
    subPrincipalLastName = fields.Str()
    subPrincipalEmail = fields.Str(validate=validate_email)
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
    teachers = fields.List(fields.Nested(TeacherSchema()), dump_only=True)


class PecaProjectSchema(Schema):
    schoolYear = fields.Str()
    schoolYearName = fields.Str()
    project = fields.Nested(ProjectReferenceSchema)
    school = fields.Nested(SchoolSchema)
