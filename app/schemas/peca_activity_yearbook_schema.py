# app/schemas/peca_activity_yearbook_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.models.peca_activity_yearbook_model import ActivityYearbook


class ActivityYearbookSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    description = fields.Str(allow_none=True)
    images = fields.List(fields.Str())

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_action(self, data, **kwargs):
        return ActivityYearbook(**data)
