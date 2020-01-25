# /app/models/state_model.py


from datetime import datetime

from mongoengine import (
    EmbeddedDocument,
    Document,
    StringField,
    PolygonField,
    BooleanField,
    DateTimeField,
    ObjectIdField,
    ReferenceField)
from marshmallow import Schema, fields, pre_load, EXCLUDE

from app.helpers.ma_schema_fields import MAPolygonField, MAReferenceField
from app.helpers.ma_schema_validators import not_blank
from app.helpers.error_helpers import RegisterNotFound



class State(Document):
    name = StringField(unique=True, required=True)
    polygon = PolygonField()
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    def clean(self):
        self.updatedAt = datetime.utcnow()


class Municipality(Document):
    name = StringField(unique=True, required=True)
    state = ReferenceField(State,required=True)
    polygon = PolygonField()
    status = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    def clean(self):
        self.updatedAt = datetime.utcnow()

"""
SCHEMAS FOR MODELS 
"""


class StateSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    polygon = MAPolygonField()
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


class MunicipalitySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    state = MAReferenceField(required=True)
    polygon = MAPolygonField()
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "state" in data:
            state = State.objects(id=data["state"], status=True).first()
            if not state:
                raise RegisterNotFound(message="State not found",
                                       status_code=404,
                                       payload={"id": data['state']})
            data['state'] = state
        if 'name' in data:
            data["name"] = data["name"].title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True