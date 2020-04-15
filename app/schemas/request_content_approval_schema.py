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


class RequestContentApprovalSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Function(lambda obj: str(obj.code).zfill(7))
    pecaId = fields.Str(required=True)
    recordId = fields.Str(required=True)
    type = fields.Str(
        validate=OneOf(
            ('schoolSlider',)
        ), required=True)
    comments = fields.Str()
    status = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected")
        )
    )
    content = fields.Dict()
    createdAt = fields.Str(dump_only=True)
    updatedAt = fields.Str(dump_only=True)

    @pre_dump
    def process_input(self, data, **kwargs):
        if data['type'] == 'schoolSlider':
            data['content'] = ImageStatusSchema().dump(data['content'])
        return data

    class Meta:
        unknown = EXCLUDE
        ordered = True
