# app/schemas/peca_activity_yearbook_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.models.peca_yearbook_model import Entity
from app.helpers.ma_schema_fields import MAImageField
from app.schemas.shared_schemas import ApprovalSchema

from flask import current_app


class EntitySchema(Schema):
    name = fields.Str(allow_none=True)
    image = MAImageField()
    content = fields.Str()

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Entity(**data)


class YearbookSchema(Schema):
    historicalReview = fields.Nested(EntitySchema)
    sponsor = fields.Nested(EntitySchema)
    school = fields.Nested(EntitySchema)
    coordinator = fields.Nested(EntitySchema)
    isInApproval = fields.Bool()
    approvalHistory = fields.List(fields.Nested(ApprovalSchema))
    updatedAt = fields.DateTime()

    class Meta:
        unknown = EXCLUDE
        ordered = True
