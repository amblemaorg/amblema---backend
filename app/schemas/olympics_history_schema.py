# app/schemas/olympics_history_schema.py

from marshmallow import Schema, fields, post_load, EXCLUDE
from app.helpers.ma_schema_validators import not_blank

class OlympicsHistoryDataSchema(Schema):
    regionalClassified = fields.Int()
    regionalGold = fields.Int()
    regionalSilver = fields.Int()
    regionalBronze = fields.Int()
    nationalClassified = fields.Int()
    nationalGold = fields.Int()
    nationalSilver = fields.Int()
    nationalBronze = fields.Int()

    class Meta:
        unknown = EXCLUDE
        ordered = True

class OlympicsHistorySchema(Schema):
    id = fields.Str(dump_only=True)
    schoolYearName = fields.Str(dump_only=True)
    mathOlympics = fields.Nested(OlympicsHistoryDataSchema)
    readingOlympics = fields.Nested(OlympicsHistoryDataSchema)

    class Meta:
        unknown = EXCLUDE
        ordered = True
