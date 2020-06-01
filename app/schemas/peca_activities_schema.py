# app/schemas/peca_activities_schema.py

import json

from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_fields import MAReferenceField
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.schemas.shared_schemas import FileSchema, ReferenceSchema
from app.models.peca_activities_model import CheckElement
from app.models.user_model import User


class CheckSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    checked = fields.Bool()

    @post_load
    def make_document(self, data, **kwargs):
        return CheckElement(**data)


class ActivityFieldsSchema(Schema):
    id = fields.Str()
    name = fields.Str(dump_only=True)
    devName = fields.Str(dump_only=True)
    hasText = fields.Bool(dump_only=True)
    hasDate = fields.Bool(dump_only=True)
    hasFile = fields.Bool(dump_only=True)
    hasVideo = fields.Bool(dump_only=True)
    hasChecklist = fields.Bool(dump_only=True)
    hasUpload = fields.Bool(dump_only=True)
    text = fields.Str(dump_only=True)
    file = fields.Nested(FileSchema, dump_only=True)
    video = fields.Nested(FileSchema, dump_only=True)
    checklist = fields.List(fields.Nested(CheckSchema))
    date = fields.DateTime()
    uploadedFile = fields.Nested(FileSchema)
    approvalType = fields.Str(
        validate=OneOf(
            ["1", "2", "3", "4"],
            ["onlyAdmin", "fillAllFields", "approvalRequest", "internalApproval"]
        ),
        dump_only=True)
    isStandard = fields.Bool(dump_only=True)
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3"),
            ("pending", "in_approval", "approved")
        )
    )
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "checklist" in data and isinstance(data["checklist"], str):
            data["checklist"] = json.loads(data["checklist"])
        return data


class ApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    user = MAReferenceField(document=User, required=True, field="name")
    comments = fields.Str(dump_only=True)
    detail = fields.Dict(dump_only=True)
    status = fields.Str(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)


class ActivityPecaSchema(ActivityFieldsSchema):
    approvalHistory = fields.List(
        fields.Nested(ApprovalSchema()), dump_only=True)
