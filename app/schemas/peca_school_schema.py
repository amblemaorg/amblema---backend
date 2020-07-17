# app/schemas/peca_school_schema.py


from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import (
    not_blank, only_numbers, OneOf, Range, validate_url, validate_email)

from app.schemas.shared_schemas import ImageStatusSchema, ApprovalSchema
from app.schemas.peca_section_schema import SectionSchema
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.state_model import State, Municipality
from app.schemas.peca_activities_slider_schema import ActivitiesSliderSchema


class SchoolSchema(Schema):
    name = fields.Str(dump_only=True)
    code = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True)
    addressState = MAReferenceField(document=State, dump_only=True)
    addressMunicipality = MAReferenceField(
        document=Municipality, dump_only=True)
    address = fields.Str(dump_only=True)
    addressCity = fields.Str(dump_only=True)
    principalFirstName = fields.Str()
    principalLastName = fields.Str()
    principalEmail = fields.Str(validate=validate_email)
    principalPhone = fields.Str(validate=only_numbers)
    subPrincipalFirstName = fields.Str(allow_none=True)
    subPrincipalLastName = fields.Str(allow_none=True)
    subPrincipalEmail = fields.Str(allow_none=True, validate=validate_email)
    subPrincipalPhone = fields.Str(allow_none=True, validate=only_numbers)
    nTeachers = fields.Int(validate=Range(min=0))
    nGrades = fields.Int(validate=Range(min=0))
    nStudents = fields.Int(validate=Range(min=0))
    nAdministrativeStaff = fields.Int(
        validate=Range(min=0))
    nLaborStaff = fields.Int(validate=Range(min=0))
    facebook = fields.Str(allow_none=True)
    instagram = fields.Str(allow_none=True)
    twitter = fields.Str(allow_none=True)
    sections = fields.List(fields.Nested(SectionSchema()), dump_only=True)
    slider = fields.List(fields.Nested(ImageStatusSchema))
    activitiesSlider = fields.Nested(ActivitiesSliderSchema, dump_only=True)
    isInApproval = fields.Bool(dump_only=True)
    approvalHistory = fields.List(
        fields.Nested(ApprovalSchema), dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
