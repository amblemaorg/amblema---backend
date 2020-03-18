# app/schemas/entity_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank
from app.models.entity_model import Action


class ActionSchema(Schema):
    name = fields.Str(required=True, validate=not_blank)
    label = fields.Str(required=True, validate=not_blank)
    sort = fields.Int(required=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].lower()
        if "label" in data and isinstance(data["label"], str):
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
    actions = fields.List(fields.Nested(ActionSchema(
        only=("name", "label", "sort"))), required=True)
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
