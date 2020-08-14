# app/schemas/request_content_approval_schema.py


import json

from marshmallow import (
    Schema,
    validate,
    pre_load,
    post_load,
    post_dump,
    EXCLUDE)

from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.user_model import User
from app.helpers.ma_schema_fields import serialize_links


class RequestContentApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Function(lambda obj: str(obj.code).zfill(7))
    project = fields.Nested(ProjectReferenceSchema)
    type = fields.Str(
        validate=OneOf(
            ('1', '2', '3', '4', '5', '6'),
            ('steps', 'testimonials', 'activities',
             'slider', 'initialWorkshop', 'specialActivity')
        ), required=True)
    user = MAReferenceField(document=User, fields=["id", "name"])
    comments = fields.Str()
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected", "cancelled")
        )
    )
    detail = fields.Dict()
    createdAt = fields.Function(lambda obj: obj.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
    updatedAt = fields.Function(lambda obj: obj.updatedAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_dump
    def process_dump(self, data, **kwargs):
        data['detail'] = serialize_links(data['detail'])
        return data
