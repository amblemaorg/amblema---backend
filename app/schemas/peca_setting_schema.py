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
from app.helpers.ma_schema_validators import not_blank, OneOf, validate_image
from app.helpers.ma_schema_fields import MAImageField
from app.schemas.shared_schemas import FileSchema, CheckTemplateSchema
from app.models.peca_setting_model import (
    LapsePlanning, InitialWorshop, Lapse, PecaSetting)
from app.schemas.learning_module_schema import ImageSchema
from app.schemas.activity_schema import ActivitySchema
from app.schemas.goal_setting_schema import GoalSettingSchema
from app.schemas.environmental_project_schema import EnvironmentalProjectSchema


ImageSchema.image = MAImageField(
    validate=(not_blank, validate_image),
    folder='peca_settings')


class InicialWorkshopSchema(Schema):
    agreementFile = fields.Nested(FileSchema())
    agreementDescription = fields.Str()
    planningMeetingFile = fields.Nested(FileSchema())
    planningMeetingDescription = fields.Str()
    teachersMeetingFile = fields.Nested(FileSchema())
    teachersMeetingDescription = fields.Str()

    @post_load
    def make_document(self, data, **kwargs):
        return InitialWorshop(**data)


class LapsePlanningSchema(Schema):
    proposalFundationFile = fields.Nested(FileSchema())
    proposalFundationDescription = fields.Str()
    meetingDescription = fields.Str()

    @post_load
    def make_document(self, data, **kwargs):
        return LapsePlanning(**data)


class AmbleCoinsSchema(Schema):
    teachersMeetingFile = fields.Nested(FileSchema())
    teachersMeetingDescription = fields.Str()
    piggyBankDescription = fields.Str()
    piggyBankSlider = fields.List(fields.Nested(ImageSchema()))

    @pre_load
    def process_input(self, data, **kwargs):
        if 'piggyBankSlider' in data and isinstance(data['piggyBankSlider'], str):
            data['piggyBankSlider'] = json.loads(data['piggyBankSlider'])
        return data


class AnnualConventionSchema(Schema):
    step1Description = fields.Str()
    step2Description = fields.Str()
    step3Description = fields.Str()
    step4Description = fields.Str()


class LapseSchema(Schema):
    initialWorshop = fields.Nested(InicialWorkshopSchema)
    lapsePlanning = fields.Nested(LapsePlanningSchema)
    ambleCoins = fields.Nested(AmbleCoinsSchema)
    annualConvention = fields.Nested(AnnualConventionSchema)
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

    @post_load
    def make_document(self, data, **kwargs):
        return PecaSetting(**data)
