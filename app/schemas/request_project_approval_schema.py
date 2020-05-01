# app/schemas/request_project_approval_schema.py


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
from app.schemas.shared_schemas import ProjectReferenceSchema


class RequestProjectApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Function(lambda obj: str(obj.code).zfill(7))
    project = fields.Nested(ProjectReferenceSchema)
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3"),
            ("pending", "approved", "rejected")
        )
    )
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
