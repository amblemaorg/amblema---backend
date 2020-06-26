# app/schemas/teacher_testimonial_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import (not_blank, OneOf, validate_image)
from app.helpers.ma_schema_fields import MAImageField
from app.schemas.shared_schemas import ApprovalSchema


class TeacherTestimonialSchema(Schema):
    id = fields.Str(dump_only=True)
    teacherId = fields.Str(required=True, validate=not_blank)
    firstName = fields.Str()
    lastName = fields.Str()
    image = MAImageField(
        required=True,
        validate=(not_blank, validate_image),
        folder='teachertestimonial')
    function = fields.Str(required=True, validate=not_blank)
    description = fields.Str(required=True, validate=not_blank)
    approvalStatus = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4"),
            ("pending", "approved", "rejected", "cancelled")
        ))
    visibilityStatus = fields.Str(
        validate=OneOf(
            ("1", "2"),
            ("active", "inactive")
        ))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
    isInApproval = fields.Boolean(dump_only=True)
    approvalHistory = fields.List(
        fields.Nested(ApprovalSchema), dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True