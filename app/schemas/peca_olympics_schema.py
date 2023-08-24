# app/schemas/peca_olympics_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, Range
from app.schemas.shared_schemas import FileSchema, ReferenceSchema
from app.models.peca_olympics_model import Section


class SectionSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    grade = fields.Str()

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_action(self, data, **kwargs):
        return Section(**data)


class StudentSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    section = fields.Nested(SectionSchema())
    status = fields.Str(
        validate=(
            OneOf(
                ["1", "2"],
                ["registered", "qualified", ]
            )))
    result = fields.Str(
        allow_none=True,
        validate=(
            OneOf(
                ["1", "2", "3"],
                ["gold", "silver", "bronze"]
            )))

    class Meta:
        unknown = EXCLUDE
        ordered = True


class OlympicsSchema(Schema):
    students = fields.List(fields.Nested(StudentSchema()))
    file = fields.Nested(FileSchema(), dump_only=True)
    description = fields.Str(dump_only=True)
    date = fields.DateTime(dump_only=True)
    order = fields.Int(validate=Range(min=0))
    
    class Meta:
        unknown = EXCLUDE
        ordered = True
