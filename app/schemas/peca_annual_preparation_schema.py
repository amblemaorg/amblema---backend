# app/schemas/peca_annual_preparation_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, Range


class TeachersSchema(Schema):
    id = fields.Str(dump_only=True)
    firstName = fields.Str()
    lastName = fields.Str()
    phone = fields.Str()
    email = fields.Str()
    annualPreparationStatus = fields.Str(
        validate=OneOf(
            ('1', '2'),
            ('preregistered', 'confirmed')
        ),
        allow_none=True)
    pecaId = fields.Str()

    class Meta:
        unknown = EXCLUDE
        ordered = True


class AnnualPreparationSchema(Schema):
    step1Description = fields.Str()
    step2Description = fields.Str()
    step3Description = fields.Str()
    step4Description = fields.Str()
    teachers = fields.List(fields.Nested(TeachersSchema()))
    order = fields.Int(validate=Range(min=0))
    
    class Meta:
        unknown = EXCLUDE
        ordered = True
