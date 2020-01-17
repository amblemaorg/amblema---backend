# /app/models/State.py


from datetime import datetime
from bson import ObjectId

from mongoengine import (
    EmbeddedDocument,
    DynamicDocument,
    StringField,
    PolygonField,
    BooleanField,
    DateTimeField,
    ObjectIdField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, pre_load, EXCLUDE

from app.helpers.ma_schema_fields import MAPolygonField
from app.helpers.ma_schema_validators import must_not_be_blank


class Municipality(EmbeddedDocument):
    id = ObjectIdField(default=ObjectId)
    name = StringField(unique=True)
    polygon = PolygonField()
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)


class State(DynamicDocument):
    name = StringField(unique=True)
    polygon = PolygonField()
    status = BooleanField(default=True)
    municipalities = EmbeddedDocumentListField(Municipality)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    def clean(self):
        self.updatedAt = datetime.utcnow()



"""
SCHEMAS FOR MODELS 
"""

class MunicipalitySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=must_not_be_blank)
    polygon = MAPolygonField()
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        data["name"] = data["name"].title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True


class StateSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=must_not_be_blank)
    polygon = MAPolygonField()
    municipalities = fields.List(fields.Nested(MunicipalitySchema(only=("id","name"))),dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        data["name"] = data["name"].title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True

