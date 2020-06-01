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
from app.schemas.shared_schemas import ProjectReferenceSchema, ImageStatusSchema
from app.models.peca_project_model import TeacherLink
from app.schemas.peca_amblecoins_schema import AmblecoinsPecaSchema
from app.schemas.peca_olympics_schema import OlympicsSchema
from app.schemas.peca_annual_preparation_schema import AnnualPreparationSchema
from app.schemas.peca_annual_convention_schema import AnnualConventionSchema
from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
from app.schemas.peca_activities_schema import ActivityPecaSchema


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


class SchoolSchema(Schema):
    name = fields.Str(dump_only=True)
    code = fields.Str(dump_only=True)
    addressState = MAReferenceField(document=State, dump_only=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, dump_only=True)
    address = fields.Str(dump_only=True)
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
    slider = fields.List(fields.Nested(ImageStatusSchema()), dump_only=True)


class LapseSchema(Schema):
    ambleCoins = fields.Nested(AmblecoinsPecaSchema)
    olympics = fields.Nested(OlympicsSchema)
    annualPreparation = fields.Nested(AnnualPreparationSchema)
    annualConvention = fields.Nested(AnnualConventionSchema)
    lapsePlanning = fields.Nested(LapsePlanningPecaSchema)
    initialWorkshop = fields.Nested(InitialWorkshopPecaSchema)
    activities = fields.List(fields.Nested(ActivityPecaSchema))

    class Meta:
        unknown = EXCLUDE
        ordered = True


class PecaProjectSchema(Schema):
    #schoolYear = fields.Str()
    schoolYearName = fields.Str()
    project = fields.Nested(ProjectReferenceSchema)
    school = fields.Nested(SchoolSchema)
    lapse1 = fields.Nested(LapseSchema)
    lapse2 = fields.Nested(LapseSchema)
    lapse3 = fields.Nested(LapseSchema)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
