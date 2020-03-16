# app/schemas/peca_setting_schema.py


from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.schemas.shared_schemas import FileSchema
from app.models.peca_setting_model import (
    LapsePlanning, InitialWorshop, Lapse1, Lapse2, Lapse3, PecaSetting)


class InicialWorkShopSchema(Schema):
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


class Lapse1Schema(Schema):
    initialWorshop = fields.Nested(InitialWorshop)
    lapsePlanning = fields.Nested(LapsePlanning)

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse1(**data)


class Lapse2Schema(Schema):
    lapsePlanning = fields.Nested(LapsePlanning)

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse2(**data)


class Lapse3Schema(Schema):
    lapsePlanning = fields.Nested(LapsePlanning)

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
