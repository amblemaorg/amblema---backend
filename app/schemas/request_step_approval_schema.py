# app/schemas/request_step_approval_schema.py


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
from app.models.user_model import User
from app.schemas.project_schema import CheckSchema
from app.schemas.step_schema import FileSchema


class RequestStepApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    stepId = fields.Str(required=True)
    project = MAReferenceField(document=Project, required=True, field="code")
    user = MAReferenceField(document=User, required=True, field="name")
    comments = fields.Str()
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected", "cancelled")
        )
    )
    stepName = fields.Str(dump_only=True)
    stepDevName = fields.Str(dump_only=True)
    stepTag = fields.Str(dump_only=True)
    stepHasText = fields.Bool(dump_only=True)
    stepHasDate = fields.Bool(dump_only=True)
    stepHasFile = fields.Bool(dump_only=True)
    stepHasVideo = fields.Bool(dump_only=True)
    stepHasChecklist = fields.Bool(dump_only=True)
    stepHasUpload = fields.Bool(dump_only=True)
    stepText = fields.Str(dump_only=True)
    stepFile = fields.Nested(FileSchema, dump_only=True)
    stepVideo = fields.Nested(FileSchema, dump_only=True)
    stepChecklist = fields.List(fields.Nested(CheckSchema))
    stepDate = fields.DateTime()
    stepUploadedFile = fields.Nested(FileSchema)
    stepIsStandard = fields.Bool(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "stepChecklist" in data and isinstance(data["stepChecklist"], str):
            data["stepChecklist"] = json.loads(data["stepChecklist"])
        return data
