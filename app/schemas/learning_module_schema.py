# app/schemas/learning_module_schema.py

import time
import mimetypes

from flask import current_app
from marshmallow import (
    Schema, fields, pre_load, post_load, EXCLUDE, validate)

from app.helpers.ma_schema_fields import MAImageField
from app.helpers.ma_schema_validators import (
    not_blank, validate_image, validate_video, validate_url, OneOf, Range)
from app.models.learning_module_model import Quiz, Image, SliderElement


class SliderElementSchema(Schema):
    url = MAImageField(
        validate=(not_blank),
        folder='learningmodules')
    description = fields.Str(required=True)
    type = fields.Str(dump_only=True)

    @post_load
    def make_document(self, data, **kwargs):
        slider = SliderElement(**data)
        if data["url"].startswith(current_app.config.get("SERVER_URL")):
            slider.type = "1"
        else:
            slider.type = "2"
        return slider


class ImageSchema(Schema):
    url = MAImageField(
        validate=(not_blank, validate_image),
        folder='learningmodules')
    description = fields.Str(required=True)

    @post_load
    def make_document(self, data, **kwargs):
        return Image(**data)


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
    slider = fields.List(fields.Nested(SliderElementSchema))
    images = fields.List(
        fields.Nested(ImageSchema))
    duration = fields.Method("get_duration", deserialize="load_duration")
    quizzes = fields.List(fields.Nested(QuizSchema, required=True))
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    def get_duration(self, obj):
        return time.strftime('%H:%M', time.gmtime(obj.duration))

    def load_duration(self, value):
        h, m = value.split(':')
        return int(h) * 3600 + int(m) * 60

    class Meta:
        unknown = EXCLUDE
        ordered = True
