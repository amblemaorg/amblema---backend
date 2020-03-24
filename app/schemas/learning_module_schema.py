# app/schemas/learning_module_schema.py

import time
import mimetypes

from flask import current_app
from marshmallow import (
    Schema, pre_load, post_load, EXCLUDE, validate)

from app.schemas import fields
from app.helpers.ma_schema_fields import MAImageField
from app.helpers.ma_schema_validators import (
    not_blank, validate_image, validate_video, validate_url, OneOf, Range, Length)
from app.models.learning_module_model import Quiz, Image, SliderElement


class SliderElementSchema(Schema):
    url = MAImageField(
        validate=(not_blank),
        folder='learningmodules',
        size=800)
    description = fields.Str(
        required=True,
        validate=Length(max=71))
    type = fields.Str(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        slider = SliderElement(**data)
        if str(data["url"]).startswith(current_app.config.get("SERVER_URL")):
            slider.type = "1"
        else:
            slider.type = "2"
        return slider


class ImageSchema(Schema):
    image = MAImageField(
        validate=(not_blank, validate_image),
        folder='learningmodules',
        size=800)
    description = fields.Str(
        required=True,
        validate=Length(max=56))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Image(**data)


class QuizSchema(Schema):
    id = fields.Str()
    question = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=116)))
    optionA = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=132)))
    optionB = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=132)))
    optionC = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=132)))
    optionD = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=132)))
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
    name = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=60)))
    title = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=140)))
    description = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=2800)))
    secondaryTitle = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=140)))
    secondaryDescription = fields.Str(
        required=True,
        validate=(
            not_blank,
            Length(max=4970)))
    objectives = fields.List(
        fields.String(
            validate=(
                not_blank,
                Length(max=873))),
        validate=Length(max=5))
    slider = fields.List(
        fields.Nested(SliderElementSchema),
        validate=Length(max=4))
    images = fields.List(
        fields.Nested(ImageSchema),
        validate=Length(max=6))
    duration = fields.Method("get_duration", deserialize="load_duration")
    quizzes = fields.List(
        fields.Nested(QuizSchema, required=True),
        validate=Length(max=15)
    )
    priority = fields.Int(allow_none=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)

    def get_duration(self, obj):
        return time.strftime('%H%M', time.gmtime(obj.duration))

    def load_duration(self, value):
        h = value[:2]
        m = value[2:]
        return int(h) * 3600 + int(m) * 60

    class Meta:
        unknown = EXCLUDE
        ordered = True
