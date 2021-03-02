# app/models/peca_environmental_project_model.py


import json
import time

from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.helpers.ma_schema_validators import not_blank, OneOf, validate_url, Length
from app.models.peca_environmental_project_model import Level, LevelDetail, Topic, Lapse
from app.schemas.shared_schemas import CheckSchema


class LevelSchema(Schema):
    label = fields.Str(
        validate=OneOf(
            ('0', '1', '2', '3', '4', '5', '6'),
            ('preschool', '1', '2', '3', '4', '5', '6'),
        ))
    value = fields.Bool(default=False)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Level(**data)


class LevelDetailSchema(Schema):
    target = fields.List(fields.Nested(LevelSchema()))
    #week = fields.List(fields.DateTime(), max_length=2)
    duration = fields.Method("get_duration", deserialize="load_duration")
    techniques = fields.List(fields.Str())
    activities = fields.List(fields.Nested(CheckSchema()))
    resources = fields.List(fields.Str())
    evaluations = fields.List(fields.Str())
    supportMaterial = fields.List(fields.Str(
        validate=validate_url
    ))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    def get_duration(self, obj):
        if obj.duration:
            return time.strftime('%H%M', time.gmtime(obj.duration))

    def load_duration(self, value):
        if value:
            h = value[:2]
            m = value[2:]
            return int(h) * 3600 + int(m) * 60

    @post_load
    def make_document(self, data, **kwargs):
        return LevelDetail(**data)


class TopicSchema(Schema):
    name = fields.Str()
    objectives = fields.List(fields.Str())
    strategies = fields.List(fields.Str())
    contents = fields.List(fields.Str())
    levels = fields.List(
        fields.Nested(LevelDetailSchema()),
        validate=Length(max=7))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Topic(**data)


class LapseSchema(Schema):
    generalObjective = fields.Str()
    topics = fields.List(
        fields.Nested(TopicSchema()),
        validate=Length(max=7))

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_document(self, data, **kwargs):
        return Lapse(**data)


class EnvironmentalProjectPecaSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()
    lapse1 = fields.Nested(LapseSchema(), allow_none=True)
    lapse2 = fields.Nested(LapseSchema(), allow_none=True)
    lapse3 = fields.Nested(LapseSchema(), allow_none=True)
    updatedAt = fields.DateTime(dump_only=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True
