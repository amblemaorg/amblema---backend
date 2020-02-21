# app/schemas/project_schema.py


import json

from marshmallow import (
    Schema,
    fields,
    validate,
    pre_load,
    post_load,
    EXCLUDE)

from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf)
from app.helpers.ma_schema_fields import MAReferenceField
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.school_year_model import SchoolYear
from app.models.project_model import StepControl
from app.schemas.step_schema import FileSchema
from app.schemas.shared_schemas import CheckSchema


class StepControlSchema(Schema):
    id = fields.Str()
    name = fields.Str(dump_only=True)
    type = fields.Str(dump_only=True)
    tag = fields.Str(dump_only=True)
    text = fields.Str(dump_only=True)
    date = fields.DateTime()
    file = fields.Nested(FileSchema, dump_only=True)
    video = fields.Nested(FileSchema, dump_only=True)
    checklist = fields.List(fields.Nested(CheckSchema))
    uploadedFile = fields.Nested(FileSchema)
    isStandard = fields.Bool(dump_only=True)
    status = fields.Str(
        validate=OneOf(
            ("1", "2"),
            ("pending", "approved")
        )
    )
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        if "checklist" in data and isinstance(data["checklist"], str):
            data["checklist"] = json.loads(data["checklist"])
        return data

    @post_load
    def make_document(self, data, **kwargs):
        return StepControl(**data)


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
