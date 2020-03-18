# app/schemas/role_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank
from app.models.role_model import Permission


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
    devName = fields.Str(dump_only=True)
    status = fields.Str(validate=validate.OneOf(
        ('1', '2'),
        ('active', 'inactive')
    ))
    permissions = fields.List(fields.Nested(PermissionSchema()))
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
