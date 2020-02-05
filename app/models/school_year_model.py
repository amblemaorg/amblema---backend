# /app/models/step_model.py


from datetime import datetime
import json

from mongoengine import (
    Document,
    StringField,
    URLField,
    BooleanField,
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

from app.helpers.ma_schema_validators import not_blank


class SchoolYear(Document):
    name = StringField(required=True)
    startDate = DateField(required=True)
    endDate = DateField(required=True)
    state = StringField(required=True, default="1")
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'seasons'}

    def clean(self):
        self.updatedAt = datetime.utcnow()
    
"""
SCHEMAS
"""


class SchoolYearSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    startDate = fields.Date(required=True)
    endDate = fields.Date(required=True)
    state = fields.Str(
        validate=validate.OneOf(
            ["1","2"],
            ["Active", "Inactive"]
        ), required=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if 'name' in data:
            data["name"] = data["name"].title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True