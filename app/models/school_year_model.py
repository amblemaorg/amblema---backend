# /app/models/school_year_model.py


from datetime import datetime
import json

from mongoengine import (
    Document,
    StringField,
    URLField,
    BooleanField,
    IntField,
    DateField,
    DateTimeField,
    EmbeddedDocument,
    EmbeddedDocumentField)
from marshmallow import (
    Schema,
    fields,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.helpers.ma_schema_validators import not_blank, OneOf


class ReadingDiagnostic(EmbeddedDocument):
    wordsPerMin = IntField(required=True)


class MathDiagnostic(EmbeddedDocument):
    multiplicationsPerMin = IntField(required=True)
    operationsPerMin = IntField(required=True)


class DiagnosticSettings(EmbeddedDocument):
    reading = EmbeddedDocumentField(ReadingDiagnostic, required=True)
    math = EmbeddedDocumentField(MathDiagnostic, required=True)


class SchoolYear(Document):
    name = StringField(required=True)
    startDate = DateField(required=True)
    endDate = DateField(required=True)
    diagnosticSettings = EmbeddedDocumentField(DiagnosticSettings)
    status = StringField(required=True, default="1")
    isDeleted = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'school_years'}

    def clean(self):
        self.updatedAt = datetime.utcnow()


"""
SCHEMAS
"""


class ReadingSchema(Schema):
    wordsPerMin = fields.Int(required=True)

    @post_load
    def make_action(self, data, **kwargs):
        return ReadingDiagnostic(**data)


class MathSchema(Schema):
    multiplicationsPerMin = fields.Int(required=True)
    operationsPerMin = fields.Int(required=True)

    @post_load
    def make_action(self, data, **kwargs):
        return MathDiagnostic(**data)


class DiagnosticSettingsSchema(Schema):
    reading = fields.Nested(ReadingSchema, required=True)
    math = fields.Nested(MathSchema, required=True)

    @post_load
    def make_action(self, data, **kwargs):
        return DiagnosticSettings(**data)


class SchoolYearSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    startDate = fields.Date(required=True)
    endDate = fields.Date(required=True)
    diagnosticSettings = fields.Nested(DiagnosticSettingsSchema)
    status = fields.Str(
        validate=OneOf(
            ["1", "2"],
            ["Active", "Inactive"]
        ), required=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].title()
        return data

    class Meta:
        unknown = EXCLUDE
        ordered = True
