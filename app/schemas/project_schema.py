# app/schemas/project_schema.py


from marshmallow import (
    Schema,
    fields,
    validate,
    EXCLUDE)

from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_year_model import SchoolYear
from app.schemas.step_schema import FileSchema


class StepControlSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    type = fields.Str(dump_only=True)
    tag = fields.Str(dump_only=True)
    text = fields.Str(dump_only=True)
    date = fields.DateTime()
    file = fields.Nested(FileSchema, dump_only=True)
    video = fields.Nested(FileSchema, dump_only=True)
    schoolYear = MAReferenceField(document=SchoolYear, dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)


class StepsProgressSchema(Schema):
    general = fields.Str(dump_only=True)
    school = fields.Str(dump_only=True)
    sponsor = fields.Str(dump_only=True)
    coordinator = fields.Str(dump_only=True)
    steps = fields.List(fields.Nested(StepControlSchema))


class ProjectSchema(Schema):
    id = fields.Str(dump_only=True)
    code = fields.Function(lambda obj: str(obj.code).zfill(7))
    school = MAReferenceField(document=SchoolUser, allow_none=True)
    sponsor = MAReferenceField(document=SponsorUser, allow_none=True)
    coordinator = MAReferenceField(document=CoordinatorUser, allow_none=True)
    stepsProgress = fields.Nested(StepsProgressSchema, dump_only=True)
    status = fields.Str(validate=OneOf(
        ('1', '2'),
        ('in_progress', 'in_peca')
    ), dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
