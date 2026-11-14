# -*- coding: utf-8 -*-
# app/helpers/hqs_award_helper.py
"""Cálculo del premio Escuela HQS (fuente única de las reglas).

Reglas:
- Cada componente del índice integral se expresa como porcentaje 0-100
  y se topa en 100 (cap_index).
- IAA: promedio crudo sobre IAA_MAX (35) -> porcentaje.
- Índice integral: promedio simple de los 4 componentes (COMPONENTS).
  Si falta alguno no hay índice integral.
- Índice final: promedio del índice integral y el índice de coevaluación
  docente (teacherIndex). Si falta alguno no hay índice final.
- Premio: primer nivel de AWARD_LEVELS cuyo minPercentage sea <= índice final;
  por debajo de 40 no hay premio.
"""
from __future__ import division

IAA_MAX = 35
COMPONENTS = ["iaa", "wordsPerMin", "multiplicationsPerMin", "operationsPerMin"]
COMPONENT_LABELS = {
    "iaa": u"IAA",
    "wordsPerMin": u"PPM",
    "multiplicationsPerMin": u"M2M",
    "operationsPerMin": u"60LM",
    "teacherIndex": u"Coevaluación",
}
AWARD_LEVELS = [
    {"code": "gold", "label": u"Escuela HQS – Nivel ORO", "minPercentage": 80},
    {"code": "silver", "label": u"Escuela HQS – Nivel PLATA", "minPercentage": 60},
    {"code": "bronze", "label": u"Escuela HQS – Nivel BRONCE", "minPercentage": 40},
]
NO_AWARD_LABEL = u"Sin premio"
INCOMPLETE_LABEL = u"Datos incompletos"


def cap_index(value):
    """Topa el valor entre 0 y 100 y lo redondea a 2 decimales."""
    if value is None:
        return None
    return round(min(100.0, max(0.0, float(value))), 2)


def iaa_percentage(rawAverage):
    """Convierte el promedio crudo de IAA a porcentaje (tope 100)."""
    if rawAverage is None:
        return None
    return cap_index(rawAverage * 100 / IAA_MAX)


def integral_index(components):
    """Devuelve (índice integral, faltantes) a partir de {clave: valor o None}."""
    missing = [key for key in COMPONENTS if components.get(key) is None]
    if missing:
        return None, missing
    total = sum(components[key] for key in COMPONENTS)
    return round(total / len(COMPONENTS), 2), []


def final_index(integral, teacherIndex):
    """Promedio del índice integral y el índice docente; None si falta alguno."""
    if integral is None or teacherIndex is None:
        return None
    return round((integral + teacherIndex) / 2, 2)


def get_award(finalIndex):
    """Devuelve el nivel de premio alcanzado o None."""
    if finalIndex is None:
        return None
    for level in AWARD_LEVELS:
        if finalIndex >= level["minPercentage"]:
            return level
    return None
