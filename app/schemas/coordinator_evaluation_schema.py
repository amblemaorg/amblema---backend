# -*- coding: utf-8 -*-
# app/schemas/coordinator_evaluation_schema.py

from marshmallow import Schema, EXCLUDE, validates_schema, ValidationError, validate

from app.schemas import fields
from app.helpers.coordinator_evaluation_helper import N_QUESTIONS, OPTION_CODES


class CoordinatorAnswerSchema(Schema):
    number = fields.Int(required=True, strict=True,
                        validate=validate.Range(min=1, max=N_QUESTIONS))
    option = fields.Str(required=True,
                        validate=validate.OneOf(OPTION_CODES))

    class Meta:
        unknown = EXCLUDE


class CoordinatorAnswersSchema(Schema):
    """Payload de guardado: las 4 preguntas cerradas, cada una una sola vez."""
    answers = fields.List(fields.Nested(CoordinatorAnswerSchema), required=True)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_all_questions(self, data, **kwargs):
        numbers = [item["number"] for item in data.get("answers", [])]
        if sorted(numbers) != list(range(1, N_QUESTIONS + 1)):
            raise ValidationError(
                [{"status": "4", "msg": "All {} questions must be answered exactly once".format(N_QUESTIONS)}],
                "answers")


def answers_to_list(data):
    """Convierte [{number, option}] (ya validado) a una lista ordenada por número."""
    ordered = sorted(data["answers"], key=lambda item: item["number"])
    return [item["option"] for item in ordered]
