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


ImageSchema.image = MAImageField(
    validate=(not_blank, validate_image),
    folder='peca_settings')


class InicialWorkshopSchema(Schema):
    name = fields.Str(dump_only=True)
    agreementFile = fields.Nested(FileSchema())
    agreementDescription = fields.Str()
    planningMeetingFile = fields.Nested(FileSchema())
    planningMeetingDescription = fields.Str()
    teachersMeetingFile = fields.Nested(FileSchema())
    teachersMeetingDescription = fields.Str()
    isStandard = fields.Bool(default=True, dump_only=True)

    @post_load
    def make_document(self, data, **kwargs):
        return InitialWorshop(**data)


class LapsePlanningSchema(Schema):
    name = fields.Str(dump_only=True)
    proposalFundationFile = fields.Nested(FileSchema())
    proposalFundationDescription = fields.Str()
    meetingDescription = fields.Str()
    isStandard = fields.Bool(default=True, dump_only=True)

    @post_load
    def make_document(self, data, **kwargs):
        return LapsePlanning(**data)


class AmbleCoinsSchema(Schema):
    name = fields.Str(dump_only=True)
    teachersMeetingFile = fields.Nested(FileSchema())
    teachersMeetingDescription = fields.Str()
    piggyBankDescription = fields.Str()
    piggyBankSlider = fields.List(fields.Nested(ImageSchema()))
    isStandard = fields.Bool(default=True, dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if 'piggyBankSlider' in data and isinstance(data['piggyBankSlider'], str):
            data['piggyBankSlider'] = json.loads(data['piggyBankSlider'])
        return data


class AnnualConventionSchema(Schema):
    name = fields.Str(dump_only=True)
    step1Description = fields.Str()
    step2Description = fields.Str()
    step3Description = fields.Str()
    step4Description = fields.Str()
    isStandard = fields.Bool(default=True, dump_only=True)


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

    @post_load
    def make_document(self, data, **kwargs):
        return PecaSetting(**data)
