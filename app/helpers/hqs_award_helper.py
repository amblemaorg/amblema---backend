# -*- coding: utf-8 -*-
# app/helpers/hqs_award_helper.py
"""Cálculo del premio Escuela HQS (fuente única de las reglas — Metodología 26-11).

Reglas:
- Cada componente del índice integral se expresa como porcentaje 0-100
  y se topa en 100 (cap_index).
- IAA: promedio crudo sobre IAA_MAX (35) -> porcentaje (sin ajuste < 40).
- PPM, M2M y 60LM: índice por grado ponderado por participantes, con ajuste
  para grados con índice < 40 (peso atenuado 0.5).
- Índice integral: promedio simple de los 4 componentes (COMPONENTS).
  Si falta alguno no hay índice integral.
- Puntaje Global HQS (final_index): ponderación 40/40/20:
  (Índice Integral * 40 %) + (Índice Docentes HQS * 40 %) + (Valoración Coordinador * 20 %).
- Condición indispensable (sine qua non): AmbLeMario habilitado/entregado
  (yearbookDownloadEnabled == True).
- Premio: ORO >= 80, PLATA >= 60, BRONCE >= 40 sobre el Puntaje Global HQS
  (siempre que cumpla AmbLeMario); < 40 no hay premio.
"""
from __future__ import division

IAA_MAX = 35
LOW_GRADE_THRESHOLD = 40.0
LOW_GRADE_WEIGHT = 0.5

INTEGRAL_WEIGHT = 0.40
TEACHER_WEIGHT = 0.40
COORDINATOR_WEIGHT = 0.20

COMPONENTS = ["iaa", "wordsPerMin", "multiplicationsPerMin", "operationsPerMin"]
COMPONENT_LABELS = {
    "iaa": u"IAA",
    "wordsPerMin": u"PPM",
    "multiplicationsPerMin": u"M2M",
    "operationsPerMin": u"60LM",
    "teacherIndex": u"Coevaluación",
    "coordinatorIndex": u"Valoración Coord.",
    "yearbook": u"AmbLeMario",
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
    """Convierte el promedio crudo de IAA a porcentaje (tope 100, sin ajuste < 40)."""
    if rawAverage is None:
        return None
    return cap_index(rawAverage * 100 / IAA_MAX)


def adjusted_area_index(gradeStats, threshold=LOW_GRADE_THRESHOLD, lowWeight=LOW_GRADE_WEIGHT):
    """
    Índice ajustado de un área diagnóstica a partir de [(indice_grado, participantes), ...].
    Los grados con índice < threshold reciben peso lowWeight (0.5); los demás peso 1.0.
    Ignora grados sin participantes o sin índice. Devuelve valor topado 0-100 o None.
    """
    weightedSum = 0.0
    weightTotal = 0.0
    for gradeIndex, participants in (gradeStats or []):
        if gradeIndex is None or participants is None or participants <= 0:
            continue
        idx = float(gradeIndex)
        count = float(participants)
        factor = lowWeight if idx < threshold else 1.0
        weightedSum += idx * count * factor
        weightTotal += count * factor
    if weightTotal <= 0:
        return None
    return cap_index(weightedSum / weightTotal)


def sections_area_index(sections, indexField, countField, lapseKey="lapse3"):
    """
    Agrupa secciones activas por grado, calcula el índice ponderado de cada grado
    y aplica el ajuste < 40 (peso 0.5). Devuelve None si no hay secciones con datos.
    """
    gradeSums = {}
    gradeCounts = {}
    for section in (sections or []):
        if section.get("isDeleted", False):
            continue
        grade = section.get("grade")
        if grade is None or grade == "":
            continue
        lapseData = (section.get("diagnostics") or {}).get(lapseKey) or {}
        idx = lapseData.get(indexField)
        count = lapseData.get(countField)
        if idx is None or count is None or count <= 0:
            continue
        gradeSums[grade] = gradeSums.get(grade, 0.0) + float(idx) * float(count)
        gradeCounts[grade] = gradeCounts.get(grade, 0.0) + float(count)

    if not gradeCounts:
        return None
    gradeStats = [
        (gradeSums[grade] / gradeCounts[grade], gradeCounts[grade])
        for grade in gradeCounts
    ]
    return adjusted_area_index(gradeStats)


def integral_index(components):
    """Devuelve (índice integral, faltantes) a partir de {clave: valor o None}."""
    missing = [key for key in COMPONENTS if components.get(key) is None]
    if missing:
        return None, missing
    total = sum(components[key] for key in COMPONENTS)
    return round(total / len(COMPONENTS), 2), []


def final_index(integral, teacherIndex, coordinatorIndex):
    """
    Puntaje Global HQS ponderado (40 % Integral + 40 % Docentes + 20 % Coordinador).
    Devuelve None si falta alguno de los tres indicadores.
    """
    if integral is None or teacherIndex is None or coordinatorIndex is None:
        return None
    score = (
        float(integral) * INTEGRAL_WEIGHT
        + float(teacherIndex) * TEACHER_WEIGHT
        + float(coordinatorIndex) * COORDINATOR_WEIGHT
    )
    return round(score, 2)


def get_award(finalIndex, yearbookDownloadEnabled=True):
    """
    Primer nivel que cumple el Puntaje Global HQS (>= 80 / 60 / 40),
    siempre que se cumpla el requisito obligatorio de AmbLeMario.
    """
    if not yearbookDownloadEnabled or finalIndex is None:
        return None
    for level in AWARD_LEVELS:
        if finalIndex >= level["minPercentage"]:
            return level
    return None
