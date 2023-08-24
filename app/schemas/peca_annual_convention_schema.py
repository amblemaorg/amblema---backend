# app/schemas/peca_annual_preparation_schema.py

import json

from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, Range
from app.schemas.shared_schemas import CheckSchema


class AnnualConventionSchema(Schema):
    checklist = fields.List(fields.Nested(CheckSchema()))
    order = fields.Int(validate=Range(min=0))
    
    class Meta:
        unknown = EXCLUDE
        ordered = True

    @pre_load
    def process_input(self, data, **kwargs):
        if 'checklist' in data and isinstance(data['checklist'], str):
            data['checklist'] = json.loads(data['checklist'])
        return data
