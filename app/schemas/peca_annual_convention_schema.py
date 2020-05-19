# app/schemas/peca_annual_preparation_schema.py

import json

from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf
from app.models.project_model import CheckElement


class CheckSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    checked = fields.Bool()

    @post_load
    def make_document(self, data, **kwargs):
        return CheckElement(**data)


class AnnualConventionSchema(Schema):
    checklist = fields.List(fields.Nested(CheckSchema()))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if 'checklist' in data and isinstance(data['checklist'], str):
            data['checklist'] = json.loads(data['checklist'])
        return data
