# app/schemas/request_content_approval_schema.py


import json

from marshmallow import (
    Schema,
    validate,
    pre_load,
    post_load,
    EXCLUDE)

from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.project_model import Project
from app.schemas.project_schema import CheckSchema
from app.schemas.step_schema import FileSchema


class RequestContentApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Function(lambda obj: str(obj.code).zfill(7))
    parentId = fields.Str(required=True)
    type = fields.Str(
        validate=OneOf(
            ('schoolSlider',)
        ), required=True)
    comments = fields.Str()
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected", "cancelled")
        )
    )
    content = fields.Dict(dump_only=True)
