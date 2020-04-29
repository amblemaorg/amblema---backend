# app/schemas/goal_setting_schema.py

import json

from marshmallow import (
    Schema,
    pre_load,
    post_load,
    EXCLUDE,
    validate,
    validates_schema,
    ValidationError)

from app.schemas import fields
from app.models.goal_setting_model import GradeSetting


class GradeSettingSchema(Schema):
    multiplicationsPerMin = fields.Int(min=0)
    operationsPerMin = fields.Int(min=0)
    wordsPerMin = fields.Int(min=0)

    class Meta:
        unknown = EXCLUDE
        ordered = True

    @post_load
    def make_action(self, data, **kwargs):
        return GradeSetting(**data)


class GoalSettingSchema(Schema):
    grade1 = fields.Nested(GradeSettingSchema())
    grade2 = fields.Nested(GradeSettingSchema())
    grade3 = fields.Nested(GradeSettingSchema())
    grade4 = fields.Nested(GradeSettingSchema())
    grade5 = fields.Nested(GradeSettingSchema())
    grade6 = fields.Nested(GradeSettingSchema())

    class Meta:
        unknown = EXCLUDE
        ordered = True
