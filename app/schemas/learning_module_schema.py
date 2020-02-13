# app/schemas/learning_module_schema.py

from marshmallow import (
    Schema, fields, pre_load, post_load, EXCLUDE, validate)

from app.helpers.ma_schema_fields import MAImageField
from app.helpers.ma_schema_validators import (
    not_blank, validate_image, validate_video, OneOf, Range)
from app.models.learning_module_model import Quiz


class QuizSchema(Schema):
    id = fields.Str()
    question = fields.Str(required=True, validate=not_blank)
    optionA = fields.Str(required=True, validate=not_blank)
    optionB = fields.Str(required=True, validate=not_blank)
    optionC = fields.Str(required=True, validate=not_blank)
    optionD = fields.Str(required=True, validate=not_blank)
    correctOption = fields.Str(
        required=True,
        validate=OneOf(
            ["optionA", "optionB", "optionC", "optionD"],
            ["optionA", "optionB", "optionC", "optionD"]))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Quiz(**data)


class LearningModuleSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=not_blank)
    description = fields.Str(required=True, validate=not_blank)
    secondaryTitle = fields.Str(required=True, validate=not_blank)
    secondaryDescription = fields.Str(required=True, validate=not_blank)
    objectives = fields.List(fields.String(validate=not_blank))
    images = fields.List(
        MAImageField(
            validate=(not_blank, validate_image),
            folder='learningmodules'
        ),
        required=True,
        validate=not_blank)
    videos = fields.List(
        fields.Str(validate=(not_blank, validate_video)),
        required=True,
        validate=not_blank)
    duration = fields.Int(required=True, validate=Range(min=0))
    points = fields.Int(required=True, validate=Range(min=0))
    quizzes = fields.List(fields.Nested(QuizSchema, required=True))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
