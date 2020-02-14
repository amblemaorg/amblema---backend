# /app/models/step_model.py


from datetime import datetime
import json
from flask import current_app

from mongoengine import (
    Document,
    StringField,
    URLField,
    BooleanField,
    DateTimeField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ReferenceField)
from marshmallow import (
    Schema,
    fields,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import not_blank, validate_url, OneOf
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.school_year_model import SchoolYear
from app.helpers.error_helpers import RegisterNotFound


class File(EmbeddedDocument):
    name = StringField(required=True)
    url = URLField(required=True)


class Step(Document):
    name = StringField(required=True)
    type = StringField(required=True, max_length=1)
    tag = StringField(required=True, max_length=1)
    text = StringField(required=True)
    date = DateTimeField(required=False)
    file = EmbeddedDocumentField(File, is_file=True)
    schoolYear = ReferenceField('SchoolYear', required=True)
    isDeleted = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'steps'}

    def clean(self):
        self.updatedAt = datetime.utcnow()


"""
SCHEMAS
"""


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
        return File(**data)


class StepSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    type = fields.Str(
        validate=OneOf(
            ["1", "2", "3", "4", "5"],
            ["Text", "Date", "AttachedFile", "DateAttachedFile", "Form"]
        ), required=True)
    tag = fields.Str(
        validate=OneOf(
            ["1", "2", "3", "4"],
            ["General", "School", "Sponsor", "Coordinator"]
        ), required=True)
    text = fields.Str(required=True, validate=not_blank)
    date = fields.DateTime()
    file = fields.Nested(FileSchema)
    schoolYear = MAReferenceField(required=True, document=SchoolYear)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].title()
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
            errors["date"] = ["Field is required"]
            errors["file"] = ["Field is required"]
        if errors:
            raise ValidationError(errors)

    class Meta:
        unknown = EXCLUDE
        ordered = True
