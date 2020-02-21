# app/schemas/step_schema.py

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
from app.helpers.ma_schema_validators import not_blank, validate_url, OneOf
from app.helpers.ma_schema_fields import MAReferenceField
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_year_model import SchoolYear
from app.models.shared_embedded_documents import Link

from app.models.step_model import Check


class FileSchema(Schema):
    name = fields.Str(validate=not_blank)
    url = fields.Str(validate=(not_blank, validate_url))

    @pre_load
    def process_input(self, data, **kwargs):
        if isinstance(data, str):
            data = json.loads(data)
        return data

    @post_load
    def make_document(self, data, **kwargs):
        return Link(**data)


class CheckSchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if isinstance(data, str):
            data = json.loads(data)
        return data

    @post_load
    def make_document(self, data, **kwargs):
        return Check(**data)


class StepSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    type = fields.Str(
        validate=OneOf(
            ["1", "2", "3", "4", "5", "6"],
            ["Text", "Date", "AttachedFile", "DateAttachedFile", "Checklist", "Form"]
        ), required=True)
    tag = fields.Str(
        validate=OneOf(
            ["1", "2", "3", "4"],
            ["General", "Coordinator", "Sponsor", "School"]
        ), required=True)
    text = fields.Str(required=True, validate=not_blank)
    date = fields.DateTime()
    file = fields.Nested(FileSchema)
    video = fields.Nested(FileSchema)
    checklist = fields.List(fields.Nested(CheckSchema()))
    schoolYear = MAReferenceField(document=SchoolYear, dump_only=True)
    status = fields.Str(
        validate=OneOf(
            ["1", "2"],
            ["active", "inactive"]
        )
    )
    isStandard = fields.Bool(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].title()
        if "checklist" in data and isinstance(data["checklist"], str):
            data["checklist"] = json.loads(data["checklist"])
        return data

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = {}
        if (
            str(data["type"]) == "2"
            and "date" not in data
        ):
            errors["date"] = ["Field is required"]
        if (
            str(data["type"]) == "3"
            and "file" not in data
        ):
            errors["file"] = ["Field is required"]
        if (
            str(data["type"]) == "4"
            and ("date" not in data or "file" not in data)
        ):
            errors["date"] = [{"status": "2", "msg": "Field is required"}]
            errors["file"] = [{"status": "2", "msg": "Field is required"}]
        if (
            str(data["type"]) == "5"
            and "checklist" not in data
        ):
            errors["checklist"] = [{"status": "2", "msg": "Field is required"}]
        if errors:
            raise ValidationError(errors)

    class Meta:
        unknown = EXCLUDE
        ordered = True
