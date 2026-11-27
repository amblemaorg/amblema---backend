# -*- coding: utf-8 -*-
"""
Puebla la BD local con datos de prueba para todos los escenarios de la
Metodología AmbLeMa HQS (26-11):
  1. ORO (Global >= 80 %, AmbLeMario habilitado)
  2. PLATA (Global 60-79.99 %, incluyendo escuelas con grados < 40 para verificar peso 0.5)
  3. BRONCE (Global 40-59.99 %)
  4. SIN PREMIO (Global < 40 % con todos los datos y AmbLeMario habilitado)
  5. BLOQUEADO POR AMBLEMARIO (Global alto, pero yearbookDownloadEnabled=False)
  6. INCOMPLETO POR FALTA DE VALORACIÓN DEL COORDINADOR
  7. INCOMPLETO POR FALTA DE COEVALUACIÓN DOCENTE
  8. INCOMPLETO POR FALTA DE DIAGNÓSTICOS / IAA

NO envía correos. Solo para entornos locales/prueba.

Uso (dentro del contenedor del backend):
  docker exec amblema_development_back sh -c 'cd /home && python scripts/seed_hqs_scenarios.py'
  docker exec amblema_development_back sh -c 'cd /home && python scripts/seed_hqs_scenarios.py --apply --confirm-db amblema'
"""
from __future__ import print_function
from __future__ import division

import argparse
import os
import random
import re
import sys
import uuid
from datetime import datetime, timedelta

sys.path.append('/home')

from mongoengine.connection import get_db

from app import create_app
from app.helpers.coevaluation_helper import N_ITEMS
from app.models.coordinator_evaluation_model import (
    CoordinatorEvaluation, CoordinatorEvaluationCoordinator)
from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.models.teacher_coevaluation_model import TeacherCoevaluation
from app.services.hqs_award_service import HqsAwardService
from app.services.teacher_coevaluation_service import TeacherCoevaluationService


def normalize(name):
    return re.sub(u"[\\s\\-–—]+", u"", name or u"")


def find_school_year(name):
    wanted = normalize(name)
    for year in SchoolYear.objects(isDeleted=False):
        if normalize(year.name) == wanted:
            return year
    return SchoolYear.objects(status="1", isDeleted=False).first()


def make_scores(target_avg):
    """Genera pares (docente, coordinador) en escala 0-7 cuyo promedio entero ronda target_avg."""
    t_scores, c_scores = [], []
    for _ in range(N_ITEMS):
        base = max(0, min(7, int(round(target_avg + random.uniform(-0.8, 0.8)))))
        t = max(0, min(7, base + random.choice((0, 0, 1))))
        c = max(0, min(7, base + random.choice((0, 0, 1))))
        # Evitar superar 7 o bajar de 0
        t_scores.append(t)
        c_scores.append(c)
    return t_scores, c_scores


def create_iaa_evaluators(peca_id, target_raw_index):
    """Crea 2 evaluadores válidos del lapso 3 cuyo promedio es target_raw_index (0-35)."""
    now = datetime.utcnow()
    delta = min(1.5, target_raw_index, 35.0 - target_raw_index)
    vals = [round(target_raw_index - delta, 2), round(target_raw_index + delta, 2)]
    for i, val in enumerate(vals, 1):
        ev = EnvironmentalDiagnosticEvaluator(
            pecaId=peca_id,
            lapse="3",
            name=u"Evaluador HQS {}".format(i),
            email="eval_hqs_{}@test.local".format(i),
            phone="04140000000",
            token=uuid.uuid4().hex,
            hasEvaluated=True,
            index=val,
            evaluatedAt=now - timedelta(days=5 + i),
            isDeleted=False,
        )
        ev.save()


def write_diagnostics_lapse3(peca_col, peca_doc, ppm_by_grade, m2m_by_grade, lm_by_grade):
    """
    Actualiza school.sections.i.diagnostics.lapse3 y school.diagnostics.lapse3
    directamente con $set (sin tocar estudiantes).
    """
    sections = (peca_doc.get("school") or {}).get("sections") or []
    updates = {}
    totals = {
        "wordsPerMin": [0.0, 0],
        "multiplicationsPerMin": [0.0, 0],
        "operationsPerMin": [0.0, 0],
    }

    has_active_sections = False
    for idx, sec in enumerate(sections):
        if sec.get("isDeleted", False):
            continue
        grade = str(sec.get("grade") or "")
        if grade == "0" or grade == "":
            continue
        has_active_sections = True
        count = max(10, len(sec.get("students") or []) or random.randint(15, 30))

        ppm = ppm_by_grade.get(grade, ppm_by_grade.get("default"))
        m2m = m2m_by_grade.get(grade, m2m_by_grade.get("default"))
        lm = lm_by_grade.get(grade, lm_by_grade.get("default"))

        lapse3 = {}
        if ppm is not None:
            lapse3["wordsPerMinIndex"] = round(ppm, 2)
            lapse3["wordsPerMinCount"] = count
            totals["wordsPerMin"][0] += ppm * count
            totals["wordsPerMin"][1] += count
        if m2m is not None:
            lapse3["multiplicationsPerMinIndex"] = round(m2m, 2)
            lapse3["multiplicationsPerMinCount"] = count
            totals["multiplicationsPerMin"][0] += m2m * count
            totals["multiplicationsPerMin"][1] += count
        if lm is not None:
            lapse3["operationsPerMinIndex"] = round(lm, 2)
            lapse3["operationsPerMinCount"] = count
            totals["operationsPerMin"][0] += lm * count
            totals["operationsPerMin"][1] += count

        updates["school.sections.{}.diagnostics.lapse3".format(idx)] = lapse3

    school_lapse3 = {}
    for key, (weighted_sum, total_count) in totals.items():
        if total_count > 0:
            school_lapse3[key + "Index"] = round(weighted_sum / total_count, 2)
            school_lapse3[key + "Count"] = total_count
        elif not has_active_sections:
            # Fallback si la escuela no tiene secciones cargadas
            default_map = {
                "wordsPerMin": ppm_by_grade.get("default"),
                "multiplicationsPerMin": m2m_by_grade.get("default"),
                "operationsPerMin": lm_by_grade.get("default"),
            }
            if default_map[key] is not None:
                school_lapse3[key + "Index"] = round(default_map[key], 2)
                school_lapse3[key + "Count"] = 20

    updates["school.diagnostics.lapse3"] = school_lapse3
    peca_col.update_one({"_id": peca_doc["_id"]}, {"$set": updates})


def create_coevaluations(service, peca, target_avg, partial_only=False):
    school = service._get_school(peca)
    if not school:
        return 0
    active_teachers = [t for t in school.teachers if service._is_active(t)]
    if not active_teachers:
        return 0
    coordinator = peca.project.coordinator if peca.project else None
    now = datetime.utcnow()
    created = 0
    for i, teacher in enumerate(active_teachers):
        coev = service._get_or_create(peca, school, teacher)
        service._refresh_snapshot(coev, peca, school, teacher)
        t_scores, c_scores = make_scores(target_avg)
        coev.coordinatorScores = c_scores
        coev.coordinatorSubmittedAt = now - timedelta(days=3)
        coev.coordinatorSubmittedBy = str(coordinator.id) if coordinator else None
        if not partial_only:
            coev.teacherScores = t_scores
            coev.teacherSubmittedAt = now - timedelta(days=2)
            coev.completedAt = now - timedelta(days=2)
        email = (teacher.email or "").strip()
        if email:
            coev.emailSentAt = now - timedelta(days=5)
            coev.emailSentTo = email
            coev.emailSentCount = 1
        coev.tokenHash = None
        coev.save()
        created += 1
        if partial_only and i >= 1:
            break
    return created


def create_coordinator_eval(peca, options):
    project_school = peca.project.school if peca.project else None
    project_coord = peca.project.coordinator if peca.project else None
    ev = CoordinatorEvaluation(
        pecaId=str(peca.id),
        schoolYearId=str(peca.schoolYear.id),
        schoolYearName=peca.schoolYearName,
        schoolId=str(project_school.id) if project_school else "",
        schoolName=project_school.name if project_school else None,
        schoolCode=project_school.code if project_school else None,
        coordinator=CoordinatorEvaluationCoordinator(
            id=project_coord.id if project_coord else None,
            name=project_coord.name if project_coord else None),
        answers=options,
        submittedAt=datetime.utcnow() - timedelta(days=1),
        submittedBy=str(project_coord.id) if project_coord else None,
    )
    ev.save()


def assign_scenarios(n):
    """Distribuye escenarios variados entre los n PECA disponibles."""
    plan = (
        ["gold"] * 8
        + ["silver_low_grade"] * 4
        + ["silver"] * 6
        + ["bronze"] * 10
        + ["none"] * 6
        + ["blocked_yearbook_gold"] * 3
        + ["blocked_yearbook_silver"] * 2
        + ["missing_coordinator"] * 4
        + ["missing_coevaluation"] * 4
        + ["missing_diagnostics"] * 6
    )
    while len(plan) < n:
        plan.append(random.choice(["gold", "silver", "bronze", "none"]))
    return plan[:n]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--school-year", default="2026 - 2027")
    parser.add_argument("--seed", type=int, default=20261127)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-db", default=None)
    args = parser.parse_args()

    random.seed(args.seed)

    app = create_app(os.getenv('INSTANCE'))
    with app.app_context():
        db = get_db()
        print("Base de datos:", db.name)
        if args.apply and args.confirm_db != db.name:
            print("ABORTADO: --confirm-db debe ser '{}'.".format(db.name))
            return 1

        school_year = find_school_year(args.school_year)
        if not school_year:
            print("No se encontró el año escolar.")
            return 1
        print("Año escolar:", school_year.name, school_year.id)

        pecas = list(PecaProject.objects(schoolYear=school_year.id, isDeleted=False))
        pecas.sort(key=lambda p: ((p.project.school.name if p.project and p.project.school else "") or "").lower())
        scenarios = assign_scenarios(len(pecas))

        print("PECA encontrados:", len(pecas))
        if not args.apply:
            from collections import Counter
            print("Distribución planificada:", dict(Counter(scenarios)))
            print("Simulación: use --apply --confirm-db {} para escribir.".format(db.name))
            return 0

        peca_ids = [str(p.id) for p in pecas]
        # Limpiar datos de prueba previos del año escolar
        TeacherCoevaluation.objects(schoolYearId=str(school_year.id)).delete()
        CoordinatorEvaluation.objects(schoolYearId=str(school_year.id)).delete()
        EnvironmentalDiagnosticEvaluator.objects(pecaId__in=peca_ids, lapse="3").delete()

        coev_service = TeacherCoevaluationService()
        peca_col = PecaProject._get_collection()
        raw_pecas = dict(
            (str(doc["_id"]), doc)
            for doc in peca_col.find({"_id": {"$in": [p.id for p in pecas]}})
        )

        for peca, scenario in zip(pecas, scenarios):
            peca_id = str(peca.id)
            raw_doc = raw_pecas[peca_id]

            if scenario == "gold":
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": random.uniform(84, 96)},
                                         {"default": random.uniform(82, 95)},
                                         {"default": random.uniform(80, 94)})
                create_iaa_evaluators(peca_id, random.uniform(30, 34.5))
                create_coevaluations(coev_service, peca, random.uniform(6.0, 6.8))
                create_coordinator_eval(peca, random.choice([
                    ["never", "never", "never", "never"],
                    ["never", "never", "never", "rarely"],
                ]))
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario == "silver_low_grade":
                # Escenario explícito de ajuste < 40 (peso 0.5): 1er y 2do grado < 40, 3ro-6to altos
                write_diagnostics_lapse3(
                    peca_col, raw_doc,
                    {"1": 12.0, "2": 24.0, "3": 35.0, "4": 68.0, "5": 82.0, "6": 90.0, "default": 70.0},
                    {"1": 18.0, "2": 45.0, "3": 22.0, "4": 64.0, "5": 75.0, "6": 86.0, "default": 65.0},
                    {"1": 50.0, "2": 55.0, "3": 62.0, "4": 74.0, "5": 70.0, "6": 82.0, "default": 68.0},
                )
                create_iaa_evaluators(peca_id, 25.89)  # 73.97 % como el Excel
                create_coevaluations(coev_service, peca, 5.2)  # ~74 %
                create_coordinator_eval(peca, ["rarely", "rarely", "frequently", "never"])  # 66.67 %
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario == "silver":
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": random.uniform(62, 76)},
                                         {"default": random.uniform(60, 74)},
                                         {"default": random.uniform(62, 78)})
                create_iaa_evaluators(peca_id, random.uniform(22, 27))
                create_coevaluations(coev_service, peca, random.uniform(4.6, 5.4))
                create_coordinator_eval(peca, random.choice([
                    ["rarely", "rarely", "never", "rarely"],
                    ["rarely", "rarely", "frequently", "never"],
                ]))
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario == "bronze":
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": random.uniform(44, 58)},
                                         {"default": random.uniform(42, 56)},
                                         {"default": random.uniform(45, 58)})
                create_iaa_evaluators(peca_id, random.uniform(15, 20))
                create_coevaluations(coev_service, peca, random.uniform(3.2, 4.1))
                create_coordinator_eval(peca, random.choice([
                    ["frequently", "rarely", "frequently", "rarely"],
                    ["frequently", "frequently", "rarely", "rarely"],
                ]))
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario == "none":
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": random.uniform(18, 32)},
                                         {"default": random.uniform(15, 30)},
                                         {"default": random.uniform(20, 34)})
                create_iaa_evaluators(peca_id, random.uniform(6, 11))
                create_coevaluations(coev_service, peca, random.uniform(1.2, 2.4))
                create_coordinator_eval(peca, random.choice([
                    ["always", "always", "frequently", "always"],
                    ["always", "frequently", "always", "frequently"],
                ]))
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario in ("blocked_yearbook_gold", "blocked_yearbook_silver"):
                high = scenario == "blocked_yearbook_gold"
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": 88.0 if high else 70.0},
                                         {"default": 86.0 if high else 68.0},
                                         {"default": 85.0 if high else 72.0})
                create_iaa_evaluators(peca_id, 31.5 if high else 25.0)
                create_coevaluations(coev_service, peca, 6.3 if high else 5.0)
                create_coordinator_eval(peca, ["never", "never", "rarely", "never"] if high else ["rarely", "rarely", "frequently", "never"])
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": False}})

            elif scenario == "missing_coordinator":
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": 82.0}, {"default": 80.0}, {"default": 78.0})
                create_iaa_evaluators(peca_id, 29.0)
                create_coevaluations(coev_service, peca, 5.8)
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario == "missing_coevaluation":
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": 75.0}, {"default": 72.0}, {"default": 74.0})
                create_iaa_evaluators(peca_id, 26.0)
                create_coevaluations(coev_service, peca, 5.0, partial_only=True)
                create_coordinator_eval(peca, ["never", "rarely", "rarely", "never"])
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

            elif scenario == "missing_diagnostics":
                # Solo PPM, faltan M2M, 60LM e IAA
                write_diagnostics_lapse3(peca_col, raw_doc, {"default": 70.0}, {}, {})
                create_coevaluations(coev_service, peca, 5.2)
                create_coordinator_eval(peca, ["rarely", "never", "rarely", "never"])
                peca_col.update_one({"_id": peca.id}, {"$set": {"yearbookDownloadEnabled": True}})

        # Consultar el reporte real para verificar todos los escenarios
        report, status = HqsAwardService().report(str(school_year.id))
        print("-" * 70)
        print("Reporte Premios HQS generado (HTTP {}):".format(status))
        print("Conteos:", report["counts"])
        print("Muestra de escuelas por escenario:")
        shown = set()
        for s in report["schools"]:
            key = (s["award"] or s["status"], tuple(s["missing"]))
            if key in shown:
                continue
            shown.add(key)
            print("  * {:35s} | Int={:<6} Doc={:<6} Coord={:<6} Global={:<6} YB={} | {} {}".format(
                (s["name"] or "")[:35],
                str(s["integralIndex"]), str(s["teacherIndex"]),
                str(s["coordinatorIndex"]), str(s["finalIndex"]),
                "Si" if s["yearbookDownloadEnabled"] else "No",
                s["awardLabel"],
                ("(falta: " + ", ".join(s["missingLabels"]) + ")") if s["missingLabels"] else ""
            ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
