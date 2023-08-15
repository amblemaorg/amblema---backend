# app/schemas/work_position_schemas.py


import json

from marshmallow import Schema, EXCLUDE, post_load, pre_load
from app.schemas import fields
from flask import current_app

from app.models.work_position_model import WorkPosition
from app.helpers.ma_schema_validators import OneOf, only_numbers, validate_email
from app.helpers.ma_schema_fields import MAReferenceField


class WorkPositionSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str()
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
