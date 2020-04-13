# app/schemas/activity_schema.py

import json

from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.schemas.shared_schemas import FileSchema, CheckTemplateSchema


class ActivitySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    devName = fields.Str(dump_only=True)
    hasText = fields.Bool(required=True, default=False)
    hasDate = fields.Bool(required=True, default=False)
    hasFile = fields.Bool(required=True, default=False)
    hasVideo = fields.Bool(required=True, default=False)
    hasChecklist = fields.Bool(required=True, default=False)
    hasUpload = fields.Bool(required=True, default=False)
    text = fields.Str(validate=not_blank)
    file = fields.Nested(FileSchema)
    video = fields.Nested(FileSchema)
    checklist = fields.List(
        fields.Nested(CheckTemplateSchema()),
        allow_none=True)
    approvalType = fields.Str(
        validate=OneOf(
            ["1", "2"],
            ["onlyAdmin", "approvalRequest"]
        ), required=True)
    status = fields.Str(
        validate=OneOf(
            ["1", "2"],
            ["active", "inactive"]
        )
    )
    isStandard = fields.Bool(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].title()
        if "checklist" in data and isinstance(data["checklist"], str):
            if not data["checklist"]:
                data["checklist"] = None
            else:
                data["checklist"] = json.loads(data["checklist"])
        convertBool = [
            "hasText",
            "hasDate",
            "hasFile",
            "hasVideo",
            "hasChecklist",
            "hasUpload"
        ]
        for boolField in convertBool:
            if boolField in data and isinstance(data[boolField], str):
                data[boolField] = json.loads(data[boolField])
        return data

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = {}
        if (
            "hasText" in data and data["hasText"]
            and "text" not in data
        ):
            errors["text"] = [{"status": "2", "msg": "Field is required"}]
        if (
            "hasFile" in data and data["hasFile"]
            and "file" not in data
        ):
            errors["file"] = [{"status": "2", "msg": "Field is required"}]
        if (
            "hasVideo" in data and data["hasVideo"]
            and "video" not in data
        ):
            errors["video"] = [{"status": "2", "msg": "Field is required"}]
        if (
            "hasChecklist" in data and data["hasChecklist"]
            and "checklist" not in data
        ):
            errors["checklist"] = [{"status": "2", "msg": "Field is required"}]
        if (
            "hasChecklist" in data and data["hasChecklist"]
            and "checklist" in data and data["checklist"] == []
        ):
            errors["checklist"] = [{"status": "12", "msg": "Out of range"}]
        if errors:
            raise ValidationError(errors)


class ActivitySummarySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    devName = fields.Str(dump_only=True)
    isStandard = fields.Bool(default=False, dump_only=True)
    status = fields.Str(
        validate=OneOf(
            ["1", "2"],
            ["active", "inactive"]
        ), default="1")


class ActivityHandleStatus(Schema):
    id = fields.Str(required=True)
    lapse = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ('1', '2', '3')
        ),
        required=True
    )
    isStandard = fields.Bool(required=True)
    status = fields.Str(
        validate=OneOf(
            ('1', '2'),
            ('active', 'inactive')
        ),
        required=True
    )
