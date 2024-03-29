# app/schemas/coordinator_user_schema.py


from marshmallow import Schema, validate, EXCLUDE, post_load

from app.schemas.user_schema import UserSchema
from app.schemas.shared_schemas import ProjectReferenceSchema
from app.helpers.ma_schema_validators import (
    not_blank, only_letters, only_numbers, OneOf, validate_image)
from app.helpers.ma_schema_fields import MAReferenceField, MAImageField
from app.schemas import fields
from app.models.coordinator_user_model import Answer, Attempt, LearningMod, CoordinatorUser


class AnswerSchema(Schema):
    quizId = fields.Str(required=True)
    option = fields.Str(
        required=True,
        validate=OneOf(
            ('optionA', 'optionB', 'optionC', 'optionD')
        ))

    @post_load
    def make_document(self, data, **kwargs):
        return Answer(**data)


class AttemptSchema(Schema):
    answers = fields.List(fields.Nested(AnswerSchema()), required=True)
    status = fields.Str(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)


class TryAnswerSchema(Schema):
    coordinator = MAReferenceField(document=CoordinatorUser, required=True)
    answers = fields.List(fields.Nested(AnswerSchema()), required=True)


class LearningModSchema(Schema):
    moduleId = fields.Str(dump_only=True)
    score = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    attempts = fields.List(fields.Nested(AttemptSchema()))


class CoordinatorUserSchema(UserSchema):
    firstName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    lastName = fields.Str(
        required=True,
        validate=(not_blank, only_letters))
    cardType = fields.Str(
        required=True,
        validate=(
            not_blank,
            OneOf(
                ["1", "2", "3"],
                ["v", "j", "e"]
            )))
    cardId = fields.Str(
        required=True,
        validate=(not_blank, only_numbers))
    phone = fields.Str(validate=only_numbers)
    gender = fields.Str(
        required=True,
        validate=OneOf(
            ('1', '2'),
            ('female', 'male')
        ))
    birthdate = fields.DateTime(required=True)
    projects = fields.List(fields.Nested(
        ProjectReferenceSchema), dump_only=True)
    homePhone = fields.Str(required=True, validate=only_numbers)
    addressHome = fields.Str()
    profession = fields.Str(allow_none=True)
    isReferred = fields.Bool()
    referredName = fields.Str(allow_none=True)
    image = MAImageField(validate=validate_image,
                         folder='coordinators',
                         allow_none=True)
    learning = fields.List(fields.Nested(LearningModSchema()), dump_only=True)
    nCoins = fields.Int(dump_only=True)
    instructed = fields.Bool(dump_only=True)
    status = fields.Str(
        validate=OneOf(
            ("1", "2"),
            ("active", "inactive")
        )
    )
    phase = fields.Str(
        validate=OneOf(
            ("1", "2", "3", "4", "5"),
            ("initial", "interested", "instructed", "approved", "peca")
        )
    )

    class Meta:
        unknown = EXCLUDE
        ordered = True
