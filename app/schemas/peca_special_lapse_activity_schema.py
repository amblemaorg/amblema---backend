# app/schemas/peca_special_lapse_activity_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import (OneOf, not_blank)
from app.schemas.shared_schemas import ApprovalSchema
from app.models.peca_special_lapse_activity_model import ItemSpecialActivity


class ItemSpecialActivitySchema(Schema):
    name = fields.Str(required=True, validate=not_blank)
    description = fields.Str(required=True, validate=not_blank)
    quantity = fields.Int(default=0.0)
    unitPrice = fields.Float(default=0.0)
    tax = fields.Float(default=0.0)
    subtotal = fields.Float(default=0.0)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return ItemSpecialActivity(**data)


class SpecialActivitySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str()
    activityDate = fields.DateTime(required=True)
    approvalStatus = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected", "cancelled")
        ))
    itemsActivities = fields.List(fields.Nested(ItemSpecialActivitySchema))
    total = fields.Float(default=0.0)
    isInApproval = fields.Boolean(dump_only=True)
    approvalHistory = fields.List(
        fields.Nested(ApprovalSchema), dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
    isDeleted = fields.Bool(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
