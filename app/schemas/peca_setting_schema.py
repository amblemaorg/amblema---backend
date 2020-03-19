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
from app.schemas.shared_schemas import FileSchema
from app.models.peca_setting_model import (
    LapsePlanning, InitialWorshop, Lapse1, Lapse2, Lapse3, PecaSetting)
from app.schemas.learning_module_schema import ImageSchema


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


class Lapse1Schema(Schema):
    initialWorshop = fields.Nested(InicialWorkshopSchema)
    lapsePlanning = fields.Nested(LapsePlanningSchema)
    ambleCoins = fields.Nested(AmbleCoinsSchema)
    annualConvention = fields.Nested(AnnualConventionSchema)

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse1(**data)


class Lapse2Schema(Schema):
    lapsePlanning = fields.Nested(LapsePlanningSchema)

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse2(**data)


class Lapse3Schema(Schema):
    lapsePlanning = fields.Nested(LapsePlanningSchema)

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse3(**data)


class PecaSettingSchema(Schema):
    lapse1 = fields.Nested(Lapse1Schema)
    lapse2 = fields.Nested(Lapse2Schema)
    lapse3 = fields.Nested(Lapse3Schema)

    @post_load
    def make_document(self, data, **kwargs):
        return PecaSetting(**data)
