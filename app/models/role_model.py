# app/models/role_model.py


from datetime import datetime
from bson import ObjectId

from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    EmailField,
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
    ObjectIdField,
    ReferenceField,
    SortedListField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField)
from marshmallow import Schema, fields, pre_load, post_load, EXCLUDE

from app.helpers.ma_schema_validators import not_blank


class Action(EmbeddedDocument):
    name = StringField(unique=True, required=True)
    label = StringField(required=True)
    sort = IntField()
    status = BooleanField(default=True)

    meta = {
        'ordering': ['+sort']
    }


class Entity(Document):
    name = StringField(unique=True, required=True)
    status = BooleanField(default=True)
    actions = EmbeddedDocumentListField(Action)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)


class ActionHandler(EmbeddedDocument):
    name = StringField(required=True)
    label = StringField(required=True)
    sort = IntField()
    allowed = BooleanField(default=False)

    meta = {
        'ordering': ['+sort']
    }

class Permission(EmbeddedDocument):
    entityId = StringField(required=True)
    entityName = StringField(required=True)
    actions = EmbeddedDocumentListField(ActionHandler, required=True)

    meta = {
        'ordering': ['+entityName']
    }

class Role(Document):
    name = StringField(unique=True, required=True)
    status = BooleanField(default=True)
    permissions = EmbeddedDocumentListField(Permission)
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'ordering': ['+name', '+permissions__entityName']
    }


"""
SCHEMAS FOR MODELS 
"""


class ActionSchema(Schema):
    name = fields.Str(required=True, validate=not_blank)
    label = fields.Str(required=True, validate=not_blank)
    sort = fields.Int(required=True)

    @pre_load
    def process_input(self, data, **kwargs):
        data["name"] = data["name"].lower()
        data["label"] = data["label"].title()
        return data
    
    @post_load
    def make_action(self, data, **kwargs):
        return Action(**data)
    
    class Meta:
        unknown = EXCLUDE
        ordered = True


class EntitySchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    actions = fields.List(fields.Nested(ActionSchema(only=("name", "label", "sort"))),required=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data:
            data["name"] = data["name"].title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True

class ActionHandlerSchema(Schema):
    name = fields.Str(required=True, validate=not_blank)
    label = fields.Str(required=True, validate=not_blank)
    sort = fields.Int(required=True)
    allowed = fields.Bool(required=True)

class PermissionSchema(Schema):
    entityId = fields.Str(required=True, validate=not_blank)
    entityName = fields.Str(required=True, validate=not_blank)
    actions = fields.List(fields.Nested(ActionHandlerSchema()))
    
    @post_load
    def make_action(self, data, **kwargs):
        return Permission(**data)
    
    class Meta:
        unknown = EXCLUDE
        ordered = True
    

class RoleSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    permissions = fields.List(fields.Nested(PermissionSchema()))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        data["name"] = data["name"].title()
        return data
    
    class Meta:
        unknown = EXCLUDE
        ordered = True