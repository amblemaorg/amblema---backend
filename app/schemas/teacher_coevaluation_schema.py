# -*- coding: utf-8 -*-
# app/schemas/teacher_coevaluation_schema.py

from marshmallow import Schema, EXCLUDE, validates_schema, ValidationError, validate

from app.schemas import fields
from app.helpers.coevaluation_helper import N_ITEMS, MIN_SCORE, MAX_SCORE


class CoevaluationScoreSchema(Schema):
    number = fields.Int(required=True, strict=True,
                        validate=validate.Range(min=1, max=N_ITEMS))
    score = fields.Int(required=True, strict=True,
                       validate=validate.Range(min=MIN_SCORE, max=MAX_SCORE))

    class Meta:
        unknown = EXCLUDE


class CoevaluationScoresSchema(Schema):
    """Payload de guardado: los 15 ítems, cada uno una sola vez, puntaje entero 0-5."""
    scores = fields.List(fields.Nested(CoevaluationScoreSchema), required=True)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_all_items(self, data, **kwargs):
        numbers = [item["number"] for item in data.get("scores", [])]
        if sorted(numbers) != list(range(1, N_ITEMS + 1)):
            raise ValidationError(
                [{"status": "4", "msg": "All {} items must be scored exactly once".format(N_ITEMS)}],
                "scores")


def scores_to_list(data):
    """Convierte [{number, score}] (ya validado) a una lista ordenada por número de ítem."""
    ordered = sorted(data["scores"], key=lambda item: item["number"])
    return [item["score"] for item in ordered]


def scores_to_items(scores):
    """Lista ordenada -> [{number, score}] para las respuestas JSON."""
    return [{"number": index + 1, "score": score} for index, score in enumerate(scores or [])]
