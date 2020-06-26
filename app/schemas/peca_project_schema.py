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

from app.schemas.shared_schemas import ProjectReferenceSchema
from app.schemas.peca_amblecoins_schema import AmblecoinsPecaSchema
from app.schemas.peca_olympics_schema import OlympicsSchema
from app.schemas.peca_annual_preparation_schema import AnnualPreparationSchema
from app.schemas.peca_annual_convention_schema import AnnualConventionSchema
from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
from app.schemas.peca_activities_schema import ActivityPecaSchema
from app.schemas.peca_schedule_schema import ScheduleActivitySchema
from app.schemas.special_activity_schema import SpecialActivitySchema
from app.schemas.peca_yearbook_schema import YearbookSchema
from app.schemas.peca_school_schema import SchoolSchema


class LapseSchema(Schema):
    ambleCoins = fields.Nested(AmblecoinsPecaSchema)
    olympics = fields.Nested(OlympicsSchema)
    annualPreparation = fields.Nested(AnnualPreparationSchema)
    annualConvention = fields.Nested(AnnualConventionSchema)
    lapsePlanning = fields.Nested(LapsePlanningPecaSchema)
    initialWorkshop = fields.Nested(InitialWorkshopPecaSchema)
    specialActivity = fields.Nested(SpecialActivitySchema)
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
