# app/schemas/shared_schemas.py


from marshmallow import Schema
from app.schemas import fields


class ReferenceSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)


class ProjectReferenceSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Str(dump_only=True)
    sponsor = fields.Nested(ReferenceSchema, dump_only=True)
    coordinator = fields.Nested(ReferenceSchema, dump_only=True)
    school = fields.Nested(ReferenceSchema, dump_only=True)


class CheckSchema(Schema):
    name = fields.Str()
    checked = fields.Bool()
