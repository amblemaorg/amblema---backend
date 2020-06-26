# app/schemas/shared_schemas.py


import json

from marshmallow import Schema, post_load, pre_load, post_dump
from app.schemas import fields
from flask import current_app

from app.helpers.ma_schema_fields import MAImageField, MAReferenceField
from app.helpers.ma_schema_validators import validate_url, not_blank, validate_image, OneOf
from app.models.shared_embedded_documents import Link, CheckTemplate, Coordinate, ImageStatus
from app.models.user_model import User
from app.helpers.ma_schema_fields import serialize_links


class ReferenceSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)


class SchoolReferenceSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    code = fields.Str(dump_only=True)


class ProjectReferenceSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Str(dump_only=True)
    sponsor = fields.Nested(ReferenceSchema, dump_only=True)
    coordinator = fields.Nested(ReferenceSchema, dump_only=True)
    school = fields.Nested(SchoolReferenceSchema, dump_only=True)


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

    @post_dump
    def process_dump(self, data, **kwargs):
        if 'url' in data and data['url'].startswith('/resources/'):
            data['url'] = current_app.config.get('SERVER_URL') + data['url']
        return data

    @post_load
    def make_document(self, data, **kwargs):
        return Link(**data)


class CheckTemplateSchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if isinstance(data, str):
            data = json.loads(data)
        return data

    @post_load
    def make_document(self, data, **kwargs):
        return CheckTemplate(**data)


class ApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    user = MAReferenceField(document=User, required=True, field="name")
    comments = fields.Str(dump_only=True)
    detail = fields.Dict(dump_only=True)
    status = fields.Str(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @post_dump
    def process_dump(self, data, **kwargs):
        data['detail'] = serialize_links(data['detail'])
        return data


class ImageStatusSchema(Schema):
    id = fields.Str()
    image = MAImageField(
        validate=(not_blank, validate_image),
        folder='schools',
        size=800)
    description = fields.Str()

    @post_load
    def make_document(self, data, **kwargs):
        return ImageStatus(**data)


class CoordinateSchema(Schema):
    latitude = fields.Float()
    longitude = fields.Float()

    @post_load
    def make_document(self, data, **kwargs):
        return Coordinate(**data)
