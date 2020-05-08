# app/schemas/peca_amblecoins_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.models.peca_amblecoins_model import AmbleSection


class SectionSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    grade = fields.Str(dump_only=True)
    status = fields.Str(
        required=True,
        validate=(
            OneOf(
                ["1", "2"],
                ["confirmed", "pending", ]
            )))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_action(self, data, **kwargs):
        return AmbleSection(**data)


class AmblecoinsPecaSchema(Schema):
    meetingDate = fields.DateTime()
    elaborationDate = fields.DateTime()
    sections = fields.List(
        fields.Nested(SectionSchema())
    )

    class Meta:
        unknown = EXCLUDE
        ordered = True
