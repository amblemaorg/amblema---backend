# app/schemas/school_year_schema.py


from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf


class SchoolYearSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=not_blank)
    startDate = fields.Date(required=True)
    endDate = fields.Date(required=True)
    status = fields.Str(
        validate=OneOf(
            ["1", "2"],
            ["Active", "Inactive"]
        ), required=True)
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
