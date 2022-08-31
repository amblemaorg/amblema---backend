# app/schemas/peca_activity_yearbook_schema.py


from marshmallow import Schema, pre_load, post_load, EXCLUDE, validate

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, validate_image
from app.models.peca_yearbook_model import Entity, Lapse
from app.helpers.ma_schema_fields import MAImageField
from app.schemas.shared_schemas import ApprovalSchema

from flask import current_app

class PrintSchema(Schema):
    print = fields.Bool()
    expandGallery = fields.Bool()

    class Meta:
        unknown = EXCLUDE
        ordered = True
class EntitySchema(Schema):
    name = fields.Str(allow_none=True)
    image = MAImageField(allow_none=True)
    content = fields.Str(allow_none=True)
    printOption = fields.Nested(PrintSchema, allow_none=True)
    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Entity(**data)

class IndexSchema(Schema):
    print = fields.Bool()
    class Meta:
        unknown = EXCLUDE
        ordered = True
class SectionImageSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    grade = fields.Str()
    image = MAImageField(allow_none=True, validate=validate_image,
                         folder='sections')
    printOption = fields.Nested(PrintSchema, allow_none=True)
    class Meta:
        unknown = EXCLUDE
        ordered = True


class LapseSchema(Schema):
    readingDiagnosticAnalysis = fields.Str()
    mathDiagnosticAnalysis = fields.Str()
    logicDiagnosticAnalysis = fields.Str()
    printOption = fields.Nested(PrintSchema, allow_none=True)
    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse(**data)


class YearbookSchema(Schema):
    historicalReview = fields.Nested(EntitySchema)
    sponsor = fields.Nested(EntitySchema)
    school = fields.Nested(EntitySchema)
    coordinator = fields.Nested(EntitySchema)
    sections = fields.List(fields.Nested(SectionImageSchema))
    lapse1 = fields.Nested(LapseSchema)
    lapse2 = fields.Nested(LapseSchema)
    lapse3 = fields.Nested(LapseSchema)
    index = fields.Nested(IndexSchema)
    isInApproval = fields.Bool()
    approvalHistory = fields.List(fields.Nested(ApprovalSchema()))
    updatedAt = fields.DateTime()

    class Meta:
        unknown = EXCLUDE
        ordered = True
