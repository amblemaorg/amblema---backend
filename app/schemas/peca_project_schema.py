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
from app.schemas.peca_amblecoins_schema import AmblecoinsPecaSchema
from app.schemas.peca_olympics_schema import OlympicsSchema
from app.schemas.peca_annual_preparation_schema import AnnualPreparationSchema
from app.schemas.peca_annual_convention_schema import AnnualConventionSchema
from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
from app.schemas.peca_activities_schema import ActivityPecaSchema
from app.schemas.peca_schedule_schema import ScheduleActivitySchema
from app.schemas.peca_section_schema import SectionSchema
from app.schemas.peca_yearbook_schema import YearbookSchema


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
    id = fields.Str(dump_only=True)
    #schoolYear = fields.Str()
    schoolYearName = fields.Str()
    project = fields.Nested(ProjectReferenceSchema)
    school = fields.Nested(SchoolSchema)
    lapse1 = fields.Nested(LapseSchema)
    lapse2 = fields.Nested(LapseSchema)
    lapse3 = fields.Nested(LapseSchema)
    schedule = fields.List(fields.Nested(ScheduleActivitySchema))
    yearbook = fields.Nested(YearbookSchema())
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
