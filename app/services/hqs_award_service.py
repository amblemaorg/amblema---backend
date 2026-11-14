# -*- coding: utf-8 -*-
# app/services/hqs_award_service.py
"""
Reporte de premios Escuela HQS por año escolar.

Por cada PECA del año combina:
- Académicos: índices del lapso 3 del PECA (school.diagnostics.lapse3).
- IAA: promedio de los evaluadores válidos del lapso 3 del diagnóstico ambiental.
- Docentes: índice de las coevaluaciones completas (school_index).
Las reglas de cálculo viven en app.helpers.hqs_award_helper.
"""
from __future__ import division

from bson import ObjectId

from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
from app.models.teacher_coevaluation_model import TeacherCoevaluation
from app.helpers.coevaluation_helper import school_index
from app.helpers.hqs_award_helper import (
    AWARD_LEVELS, COMPONENT_LABELS, NO_AWARD_LABEL, INCOMPLETE_LABEL,
    cap_index, iaa_percentage, integral_index, final_index, get_award)


# Componente del índice integral -> campo del resumen de diagnósticos del lapso 3.
ACADEMIC_FIELDS = {
    "wordsPerMin": "wordsPerMinIndex",
    "multiplicationsPerMin": "multiplicationsPerMinIndex",
    "operationsPerMin": "operationsPerMinIndex",
}
STATUS_AWARDED = "awarded"
STATUS_NONE = "none"
STATUS_INCOMPLETE = "incomplete"


def _error(message, status_code, **extra):
    body = {"message": message}
    body.update(extra)
    return body, status_code


def average_iaa(indexes):
    """Promedio crudo (2 decimales) de los índices IAA no nulos; None si no hay."""
    values = [value for value in indexes if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def build_school_row(schoolId, name, pecaId, coordinator, lapse3,
                     iaaRaw, percentages):
    """
    Arma la fila de una escuela del reporte.
    lapse3: resumen de diagnósticos del lapso 3 (o None).
    percentages: porcentajes de las coevaluaciones completas.
    """
    components = {"iaa": iaa_percentage(iaaRaw)}
    for key, field in ACADEMIC_FIELDS.items():
        value = getattr(lapse3, field, None) if lapse3 is not None else None
        components[key] = cap_index(value)

    integral, missing = integral_index(components)
    teacherIndex = school_index(percentages)
    if teacherIndex is None:
        missing = missing + ["teacherIndex"]
    finalIdx = final_index(integral, teacherIndex)
    award = get_award(finalIdx)

    if award:
        status, awardLabel = STATUS_AWARDED, award["label"]
    elif missing:
        status, awardLabel = STATUS_INCOMPLETE, INCOMPLETE_LABEL
    else:
        status, awardLabel = STATUS_NONE, NO_AWARD_LABEL

    return {
        "schoolId": schoolId,
        "name": name,
        "pecaId": pecaId,
        "coordinator": coordinator,
        "iaaRaw": iaaRaw,
        "components": components,
        "integralIndex": integral,
        "teacherIndex": teacherIndex,
        "nCompletedCoevaluations": len([p for p in percentages if p is not None]),
        "finalIndex": finalIdx,
        "missing": missing,
        "missingLabels": [COMPONENT_LABELS[key] for key in missing],
        "status": status,
        "award": award["code"] if award else None,
        "awardLabel": awardLabel,
    }


def sort_schools(schools):
    """finalIndex descendente (None al final) y luego nombre sin mayúsculas."""
    schools.sort(key=lambda s: (
        s["finalIndex"] is None,
        -(s["finalIndex"] or 0),
        (s["name"] or "").lower()))
    return schools


def count_schools(schools):
    """Conteo por premio (gold/silver/bronze) y por estado (none/incomplete)."""
    counts = dict((level["code"], 0) for level in AWARD_LEVELS)
    counts[STATUS_NONE] = 0
    counts[STATUS_INCOMPLETE] = 0
    for school in schools:
        if school["award"]:
            counts[school["award"]] += 1
        elif school["status"] in (STATUS_NONE, STATUS_INCOMPLETE):
            counts[school["status"]] += 1
    return counts


class HqsAwardService():

    def report(self, schoolYearId, schoolId=None):
        if not ObjectId.is_valid(schoolYearId):
            return _error("School year not found", 404, schoolYearId=schoolYearId)
        schoolYear = SchoolYear.objects(id=schoolYearId, isDeleted=False).first()
        if not schoolYear:
            return _error("School year not found", 404, schoolYearId=schoolYearId)

        pecaFilter = {"schoolYear": schoolYear.id, "isDeleted": False}
        if schoolId:
            pecaFilter["project__school__id"] = schoolId
        # Solo lo necesario: sin school.sections (estudiantes embebidos, pesados).
        pecas = [peca for peca in PecaProject.objects(**pecaFilter).only(
            'id', 'project', 'school.diagnostics')
            if peca.project and peca.project.school]
        pecaIds = [str(peca.id) for peca in pecas]

        iaaByPeca = {}
        if pecaIds:
            for evaluator in EnvironmentalDiagnosticEvaluator.objects(
                    pecaId__in=pecaIds, lapse="3", isDeleted=False,
                    hasEvaluated=True).only('pecaId', 'index'):
                iaaByPeca.setdefault(evaluator.pecaId, []).append(evaluator.index)

        percentagesByPeca = {}
        if pecaIds:
            for coevaluation in TeacherCoevaluation.objects(
                    pecaId__in=pecaIds, teacherSubmittedAt__ne=None,
                    coordinatorSubmittedAt__ne=None).only('pecaId', 'percentage'):
                percentagesByPeca.setdefault(coevaluation.pecaId, []).append(
                    coevaluation.percentage)

        schools = []
        for peca in pecas:
            pecaId = str(peca.id)
            diagnostics = peca.school.diagnostics if peca.school else None
            lapse3 = diagnostics.lapse3 if diagnostics else None
            coordinator = peca.project.coordinator
            schools.append(build_school_row(
                schoolId=peca.project.school.id,
                name=peca.project.school.name,
                pecaId=pecaId,
                coordinator=coordinator.name if coordinator else None,
                lapse3=lapse3,
                iaaRaw=average_iaa(iaaByPeca.get(pecaId, [])),
                percentages=percentagesByPeca.get(pecaId, [])))

        sort_schools(schools)
        return {
            "schoolYear": {"id": str(schoolYear.id), "name": schoolYear.name,
                           "status": schoolYear.status},
            "levels": AWARD_LEVELS,
            "counts": count_schools(schools),
            "schools": schools,
        }, 200
