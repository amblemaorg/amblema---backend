# -*- coding: utf-8 -*-
# app/helpers/coordinator_evaluation_helper.py
"""
Instrumento de Valoración / Opinión del Coordinador AmbLeMa HQS (versión 1).

Fuente única de las 4 preguntas cerradas, la escala de frecuencia y el cálculo
del puntaje (base 100 puntos, 25 pts por pregunta).
"""

from __future__ import division


INSTRUMENT_VERSION = 1
MAX_QUESTION_SCORE = 25.0
MAX_TOTAL = 100.0

OPTIONS = [
    {
        "code": "never",
        "label": u"Nunca",
        "description": u"No se presentaron dificultades u obstáculos durante el lapso evaluado.",
        "numerator": 3,
        "denominator": 3,
        "score": 25.0,
        "percentage": 100.0,
    },
    {
        "code": "rarely",
        "label": u"Pocas veces",
        "description": u"Se presentaron dificultades puntuales o aisladas, resueltas sin afectar la continuidad.",
        "numerator": 2,
        "denominator": 3,
        "score": 16.67,
        "percentage": 66.7,
    },
    {
        "code": "frequently",
        "label": u"Con frecuencia",
        "description": u"Se presentaron dificultades recurrentes que afectaron parcialmente el ritmo de trabajo.",
        "numerator": 1,
        "denominator": 3,
        "score": 8.33,
        "percentage": 33.3,
    },
    {
        "code": "always",
        "label": u"Siempre",
        "description": u"La dificultad fue constante a lo largo de todo el lapso evaluado.",
        "numerator": 0,
        "denominator": 3,
        "score": 0.0,
        "percentage": 0.0,
    },
]

QUESTIONS = [
    {
        "number": 1,
        "dimension": u"Recepción y uso de AmbLeMa",
        "question": u"¿Se presentaron dificultades o resistencias para que AmbLeMa fuera asumida como una herramienta de apoyo en el desarrollo general de la escuela?",
    },
    {
        "number": 2,
        "dimension": u"Planificación vs. improvisación",
        "question": u"Al planificar las actividades de AmbLeMa con la escuela, ¿se presentaron situaciones de improvisación o incumplimiento de lo planificado?",
    },
    {
        "number": 3,
        "dimension": u"Relación con familias y representantes",
        "question": u"¿Se presentaron dificultades en la relación con los representantes o en su incorporación a la dinámica escuela–familia–AmbLeMa?",
    },
    {
        "number": 4,
        "dimension": u"Acceso, comunicación y seguimiento",
        "question": u"Al asistir a la escuela en los días previstos, ¿se presentaron obstáculos en la comunicación con los directivos, en el acceso a salones y docentes, o para avanzar en diagnósticos, planificación, seguimiento y acompañamiento?",
    },
]

N_QUESTIONS = len(QUESTIONS)
OPTION_CODES = [opt["code"] for opt in OPTIONS]
OPTIONS_BY_CODE = dict((opt["code"], opt) for opt in OPTIONS)

STATUS_NOT_STARTED = "not_started"
STATUS_COMPLETED = "completed"
STATUS_LABELS = {
    STATUS_NOT_STARTED: u"Pendiente",
    STATUS_COMPLETED: u"Completada",
}


def get_coordinator_instrument(include_scores=True):
    """Catálogo serializable que consumen front y backoffice."""
    options = []
    for opt in OPTIONS:
        item = {
            "code": opt["code"],
            "label": opt["label"],
            "description": opt["description"],
        }
        if include_scores:
            item["score"] = opt["score"]
            item["percentage"] = opt["percentage"]
        options.append(item)
    return {
        "version": INSTRUMENT_VERSION,
        "maxQuestionScore": MAX_QUESTION_SCORE if include_scores else None,
        "maxTotal": MAX_TOTAL if include_scores else None,
        "options": options,
        "questions": QUESTIONS,
    }


def option_raw_score(code):
    """Puntaje exacto (sin redondeo intermedio) de una opción sobre 25 pts."""
    opt = OPTIONS_BY_CODE.get(code)
    if not opt:
        return None
    return MAX_QUESTION_SCORE * opt["numerator"] / opt["denominator"]


def get_option_label(code):
    opt = OPTIONS_BY_CODE.get(code)
    return opt["label"] if opt else None


def compute_coordinator_results(answer_options):
    """
    Calcula los puntajes por pregunta y el puntaje total (0-100, redondeado a 2 decimales).
    Suma los valores exactos antes de redondear el total para evitar errores acumulados
    (p. ej. 3 × 16.6667 = 50.00, no 50.01).
    Devuelve None si faltan respuestas o alguna opción es inválida.
    """
    if not answer_options or len(answer_options) != N_QUESTIONS:
        return None
    raw_scores = []
    for code in answer_options:
        raw = option_raw_score(code)
        if raw is None:
            return None
        raw_scores.append(raw)
    scores = [round(raw, 2) for raw in raw_scores]
    total = round(sum(raw_scores), 2)
    return {
        "scores": scores,
        "totalScore": total,
    }
