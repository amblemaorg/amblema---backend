# app/schemas/peca_activities_slider_schema.py

import json

from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.schemas.shared_schemas import ApprovalSchema
from app.helpers.ma_schema_fields import MAImageField
from app.helpers.ma_schema_validators import validate_image


class ActivitiesSliderSchema(Schema):
    slider = fields.List(MAImageField(validate=validate_image))
    isInApproval = fields.Bool(dump_only=True)
    approvalHistory = fields.List(
        fields.Nested(ApprovalSchema), dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
