# app/schemas/teacher_testimonial_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, OneOf, validate_image)
from app.helpers.ma_schema_fields import MAImageField
from app.models.teacher_testimonial_model import TeacherTestimonial
from app.models.peca_project_model import Teacher


class TeacherTestimonialSchema(Schema):
    id = fields.Str(dump_only=True)
    teacher = MAReferenceField(document=Teacher, allow_none=True)
    image = MAImageField(
        allow_none=True,
        validate=validate_image,
        folder='teachertestimonial')
    function = fields.Str(
        validate=(not_blank, only_letters))
    description = fields.Str()
    status = fields.Str(
        validate=OneOf(
            ('1', '2', '3'),
            ("pending", "approved", "rejected")
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
