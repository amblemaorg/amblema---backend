# app/schemas/monitoring_activity_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import (not_blank, validate_image, Length)
from app.helpers.ma_schema_fields import MAImageField


class DetailActivitySchema(Schema):
    description = fields.Str(required=True, validate=not_blank)
    image = MAImageField(
        allow_none=True,
        validate=validate_image,
        folder='monitoringactivities')


class MonitoringActivitySchema(Schema):
    environmentActivities = fields.List(fields.Nested(DetailActivitySchema), validate=Length(max=4))
    readingActivities = fields.List(fields.Nested(DetailActivitySchema), validate=Length(max=4))
    mathActivities = fields.List(fields.Nested(DetailActivitySchema), validate=Length(max=4))