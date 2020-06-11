# app/schemas/request_content_approval_schema.py


import json

from marshmallow import (
    Schema,
    validate,
    pre_load,
    post_load,
    pre_dump,
    EXCLUDE)

from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)
from app.schemas.shared_schemas import ImageStatusSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.user_model import User


class RequestContentApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Function(lambda obj: str(obj.code).zfill(7))
    project = fields.Nested(ProjectReferenceSchema)
    type = fields.Str(
        validate=OneOf(
            ('1', '2', '3', '4', '5', '6'),
            ('steps', 'testimonials', 'activities', 'slider', 'initialWorkshop', 'specialActivity')
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
    createdAt = fields.Str(dump_only=True)
    updatedAt = fields.Str(dump_only=True)

    # @pre_dump
    # def process_input(self, data, **kwargs):
    # if data['type'] == '4':
    #    data['detail'] = ImageStatusSchema().dump(data['detail'])
    # return data

    class Meta:
        unknown = EXCLUDE
        ordered = True
