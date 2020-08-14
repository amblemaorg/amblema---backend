# app/schemas/peca_setting_schema.py

import json

from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, validate_image, Length
from app.helpers.ma_schema_fields import MAImageField
from app.schemas.shared_schemas import FileSchema, CheckTemplateSchema
from app.models.peca_setting_model import (
    LapsePlanning, InitialWorshop, Lapse, PecaSetting)
from app.schemas.learning_module_schema import ImageSchema
from app.schemas.activity_schema import ActivitySchema
from app.schemas.goal_setting_schema import GoalSettingSchema
from app.schemas.environmental_project_schema import EnvironmentalProjectSchema
from app.schemas.monitoring_activity_schema import MonitoringActivitySchema


ImageSchema.image = MAImageField(
    validate=(not_blank, validate_image),
    folder='peca_settings')


class InicialWorkshopSchema(Schema):
    name = fields.Str(dump_only=True)
    description = fields.Str(validate=Length(max=100))
    #agreementFile = fields.Nested(FileSchema())
    #agreementDescription = fields.Str()
    #planningMeetingFile = fields.Nested(FileSchema())
    #planningMeetingDescription = fields.Str()
    #teachersMeetingFile = fields.Nested(FileSchema())
    #teachersMeetingDescription = fields.Str()
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return InitialWorshop(**data)


class LapsePlanningSchema(Schema):
    name = fields.Str(dump_only=True)
    proposalFundationFile = fields.Nested(FileSchema())
    proposalFundationDescription = fields.Str(validate=Length(max=730))
    meetingDescription = fields.Str(validate=Length(max=730))
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return LapsePlanning(**data)


class AmbleCoinsSchema(Schema):
    name = fields.Str(dump_only=True)
    description = fields.Str(validate=Length(max=100))
    teachersMeetingFile = fields.Nested(FileSchema())
    teachersMeetingDescription = fields.Str(validate=Length(max=730))
    piggyBankDescription = fields.Str()
    piggyBankSlider = fields.List(fields.Nested(ImageSchema()))
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if 'piggyBankSlider' in data and isinstance(data['piggyBankSlider'], str):
            data['piggyBankSlider'] = json.loads(data['piggyBankSlider'])
        return data


class AnnualPreparationSchema(Schema):
    name = fields.Str(dump_only=True)
    step1Description = fields.Str(validate=Length(max=196))
    step2Description = fields.Str(validate=Length(max=196))
    step3Description = fields.Str(validate=Length(max=196))
    step4Description = fields.Str(validate=Length(max=196))
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

class CheckTmpSchema(CheckTemplateSchema):
    name = fields.Str(required=True, validate=Length(max=196))

class AnnualConventionSchema(Schema):
    name = fields.Str(dump_only=True)
    description = fields.Str(validate=Length(max=100))
    checklist = fields.List(fields.Nested(CheckTmpSchema))
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if 'checklist' in data and isinstance(data['checklist'], str):

            data['checklist'] = json.loads(data['checklist'])
        return data


class MathOlympicSchema(Schema):
    name = fields.Str(dump_only=True)
    file = fields.Nested(FileSchema())
    description = fields.Str(validate=Length(max=730))
    webDescription = fields.Str(validate=Length(max=100))
    date = fields.DateTime(allow_none=True)
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class SpecialLapseActivitySchema(Schema):
    name = fields.Str(dump_only=True)
    description = fields.Str(validate=Length(max=100))
    isStandard = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class LapseSchema(Schema):
    initialWorshop = fields.Nested(InicialWorkshopSchema)
    lapsePlanning = fields.Nested(LapsePlanningSchema)
    ambleCoins = fields.Nested(AmbleCoinsSchema)
    annualConvention = fields.Nested(AnnualConventionSchema)
    annualPreparation = fields.Nested(AnnualPreparationSchema)
    mathOlympic = fields.Nested(MathOlympicSchema)
    specialLapseActivity = fields.Nested(SpecialLapseActivitySchema)
    activities = fields.List(fields.Nested(ActivitySchema))

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse(**data)


class PecaSettingSchema(Schema):
    lapse1 = fields.Nested(LapseSchema)
    lapse2 = fields.Nested(LapseSchema)
    lapse3 = fields.Nested(LapseSchema)
    goalSetting = fields.Nested(GoalSettingSchema)
    environmentalProject = fields.Nested(EnvironmentalProjectSchema)
    monitoringActivities = fields.Nested(MonitoringActivitySchema)

    @post_load
    def make_document(self, data, **kwargs):
        return PecaSetting(**data)
