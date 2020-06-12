# app/schemas/peca_olympics_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf


class ScheduleActivitySchema(Schema):
    id = fields.Str(data_key="Id")
    subject = fields.Str(data_key="Subject")
    startTime = fields.Str(data_key="StartTime", required=True)
    endTime = fields.Str(data_key="EndTime")
    description = fields.Str(data_key="Description")

    class Meta:
        unknown = EXCLUDE
        ordered = True
