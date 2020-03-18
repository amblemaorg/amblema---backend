# app/schemas/shared_schemas.py


import json

from marshmallow import Schema, post_load, pre_load
from app.schemas import fields

from app.helpers.ma_schema_validators import validate_url, not_blank
from app.models.shared_embedded_documents import Link


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
    id = fields.Str()
    name = fields.Str()
    checked = fields.Bool()


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