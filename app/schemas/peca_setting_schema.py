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
from app.models.peca_setting_model import InitialWorshop, Activities, PecaSetting


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


class ActivitiesSchema(Schema):
    initialWorkshop = fields.Nested(InicialWorkShopSchema())

    @post_load
    def make_document(self, data, **kwargs):
        return Activities(**data)


class PecaSettingSchema(Schema):
    activities = fields.Nested(ActivitiesSchema)

    @post_load
    def make_document(self, data, **kwargs):
        return PecaSetting(**data)
