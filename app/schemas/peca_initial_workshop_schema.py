# app/schemas/peca_initial_workshop_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, validate_image
from app.helpers.ma_schema_fields import MAImageField
from app.schemas.shared_schemas import FileSchema, ReferenceSchema
from app.models.peca_initial_workshop_model import Image


class ImageSchema(Schema):
    image = MAImageField(
        validate=(not_blank, validate_image))
    description = fields.Str()
    status = fields.Str(
        validate=(
            OneOf(
                ["1", "2", "3"],
                ["pending", "approved", "rejected"]
            )))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Image(**data)


class InitialWorkshopPecaSchema(Schema):
    name = fields.Str(dump_only=True)
    agreementFile = fields.Nested(FileSchema(), dump_only=True)
    agreementDescription = fields.Str(dump_only=True)
    planningMeetingFile = fields.Nested(FileSchema(), dump_only=True)
    planningMeetingDescription = fields.Str(dump_only=True)
    teachersMeetingFile = fields.Nested(FileSchema(), dump_only=True)
    teachersMeetingDescription = fields.Str(dump_only=True)
    isStandard = fields.Bool(dump_only=True)
    description = fields.Str()
    images = fields.List(fields.Nested(ImageSchema))

    class Meta:
        unknown = EXCLUDE
        ordered = True
