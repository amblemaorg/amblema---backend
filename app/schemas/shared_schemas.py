# app/schemas/shared_schemas.py


import json

from marshmallow import Schema, post_load, pre_load
from app.schemas import fields
from flask import current_app

from app.helpers.ma_schema_fields import MAImageField
from app.helpers.ma_schema_validators import validate_url, not_blank, validate_image, OneOf
from app.models.shared_embedded_documents import Link, CheckTemplate


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


class ImageStatusSchema(Schema):
    id = fields.Str(dump_only=True)
    pecaId = fields.Str(dump_only=True)
    image = MAImageField(
        validate=(not_blank, validate_image),
        folder='schools',
        size=800)
    description = fields.Str()
    approvalStatus = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ("pending", "approved", "rejected")
        ))
    visibilityStatus = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ("active", "inactive")
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
