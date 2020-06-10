# app/schemas/special_activity_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import OneOf


class ItemSpecialActivitySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    description = fields.Str(required=True, validate=not_blank)
    quantity = fields.Int(default=0.0)
    unitPrice = fields.Float(default=0.0)
    tax = fields.Float(default=0.0)
    subtotal = fields.Float(default=0.0)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)


class SpecialActivitySchema(Schema):
    id = fields.Str(dump_only=True)
    #name = fields.StringField(default="Actividad especial de lapso")
    activityDate = fields.DateTime(required=True)
    approvalStatus = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected", "cancelled")
        ))
    itemsActivities = fields.List(fields.Nested(ItemSpecialActivitySchema))
    total = fields.Float(default=0.0)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)