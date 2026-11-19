# -*- coding: utf-8 -*-
"""
Genera datos de PRUEBA para revisar el reporte "Premios Escuela HQS":
resultados de diagnóstico (PPM, M2M, 60LM) y evaluaciones del IAA, coherentes con las
coevaluaciones docentes que ya existan (ver seed_teacher_coevaluations.py).

Qué hace, por cada PECA del año escolar (por defecto "2026 - 2027"):
  1. Lee el Índice de Docentes HQS actual de la escuela (coevaluaciones completas).
  2. Reparte las escuelas entre Oro / Plata / Bronce / Sin premio de forma que sea
     alcanzable con ese Índice de Docentes: las escuelas con docentes en excelencia
     reciben diagnósticos buenos en unas (Oro) y más modestos en otras (Plata, Bronce),
     y las demás quedan repartidas en todos los rangos.
  3. Escribe los resultados de diagnóstico de CADA estudiante activo (lapsos 1, 2 y 3,
     con mejora de un lapso a otro) y recalcula los resúmenes igual que la aplicación.
  4. Crea evaluadores del IAA (2 por lapso) con sus resultados, usando el mismo
     servicio que la aplicación (`submit_evaluation`).
  5. Con --apply, vuelve a consultar el reporte de premios y compara con lo planificado.

Las escuelas sin coevaluaciones completas reciben igual diagnósticos e IAA, y en el
reporte quedan como "Datos incompletos" (falta Coevaluación). Las escuelas sin estudiantes
activos se omiten y se listan.

NO ENVÍA CORREOS: los evaluadores del IAA se crean directamente en la base de datos y
nunca se llama a `register_evaluator` (que es el que envía el correo).

ATENCIÓN: sobrescribe los diagnósticos de los estudiantes de esos PECA y marca como
borrados los evaluadores del IAA que ya tuvieran (los de una corrida anterior de este
script se eliminan). Solo para bases de prueba/locales. Haga un `mongodump` antes.

Por defecto es una SIMULACIÓN: no escribe nada. Para escribir: --apply y
--confirm-db <nombre de la base> (debe coincidir con la base activa).

Uso (dentro del contenedor del backend):
  docker exec amblema_development_back sh -c 'cd /home && python scripts/seed_hqs_award_data.py'
  docker exec amblema_development_back sh -c 'cd /home && python scripts/seed_hqs_award_data.py --apply --confirm-db amblema'

Opciones:
  --school-year "2026 - 2027"   nombre del año escolar
  --seed N                      semilla para repetir los mismos valores
  --set-missing-goals           si las metas del año están sin configurar (vacías o <= 1),
                                las completa con valores típicos antes de generar
"""
from __future__ import print_function
from __future__ import division

import argparse
import cProfile
import io
import os
import pstats
import random
import re
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta

# Add the app directory to sys.path
sys.path.append('/home')

from mongoengine.connection import get_db

from app import create_app
from app.helpers.coevaluation_helper import school_index
from app.helpers.hqs_award_helper import IAA_MAX
from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
from app.models.peca_project_model import PecaProject
from app.models.peca_student_model import Diagnostic
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.models.teacher_coevaluation_model import TeacherCoevaluation
from app.services.environmental_diagnostic_service import EnvironmentalDiagnosticService
from app.services.hqs_award_service import HqsAwardService

# Rango (con margen de 2 puntos) del promedio final que se busca en cada premio.
TIER_RANGE = {
    "gold": (82.0, 98.0),
    "silver": (62.0, 78.0),
    "bronze": (42.0, 58.0),
    "none": (10.0, 38.0),
}
TIER_ORDER = ["gold", "silver", "bronze", "none"]
# Rango de cada componente del Índice Integral (%): el mínimo evita IAA < 1 punto por
# indicador y el máximo evita depender del tope de 100.
COMPONENT_MIN, COMPONENT_MAX = 15.0, 98.0
# Escuelas con Índice de Docentes >= TOP_TEACHER_INDEX: "docentes con excelencia".
TOP_TEACHER_INDEX = 80.0
TOP_PATTERN = ["gold", "gold", "silver", "gold", "bronze", "silver"]
OTHER_PATTERN = ["silver", "bronze", "gold", "none", "silver", "bronze", "gold", "none",
                 "bronze", "silver"]

DIAGNOSTICS = [
    # (clave del índice, campo del estudiante, campo de fecha)
    ("wordsPerMin", "wordsPerMin", "readingDate"),
    ("multiplicationsPerMin", "multiplicationsPerMin", "mathDate"),
    ("operationsPerMin", "operationsPerMin", "logicDate"),
]
IAA_INDICATORS = [
    ("cleanlinessAndCareOfSpaces", ["1.1", "1.2", "1.3"]),
    ("wasteManagement", ["2.1", "2.2", "2.3"]),
    ("biodiversityConservation", ["3.1", "3.2", "3.3"]),
    ("waterUse", ["4.1", "4.2", "4.3"]),
    ("communityRelations", ["5.1", "5.2"]),
]
# Metas típicas por grado (solo con --set-missing-goals).
DEFAULT_GOALS = {
    "wordsPerMin": [40, 60, 80, 100, 120, 140],
    "multiplicationsPerMin": [20, 25, 30, 35, 40, 45],
    "operationsPerMin": [6, 8, 10, 12, 14, 16],
}
# Antigüedad aproximada (días) de cada lapso y variación.
LAPSE_AGE_DAYS = {1: 100, 2: 55, 3: 10}
# Las metas del año existen solo de 1.º a 6.º grado: preescolar ("0") no tiene meta.
GOAL_GRADES = ("1", "2", "3", "4", "5", "6")
EVALUATORS_PER_LAPSE = 2
EVALUATOR_NAME_PREFIX = u"Evaluador Prueba"


def say(*parts):
    """print con vaciado inmediato: con `docker exec` sin TTY Python acumula la salida."""
    print(*parts)
    sys.stdout.flush()


def normalize(name):
    """'2026 - 2027' == '2026-2027' == '2026 – 2027'."""
    return re.sub(u"[\\s\\-–—]+", u"", name or u"")


def find_school_year(name):
    wanted = normalize(name)
    for year in SchoolYear.objects(isDeleted=False):
        if normalize(year.name) == wanted:
            return year
    return None


# ----------------------------------------------------------------- planificación

def feasible_range(tier, teacherIndex):
    """
    Intervalo del promedio final F = (Integral + Docentes) / 2 que cae en el premio
    `tier`, dado que cada componente (y por tanto el Integral) va de COMPONENT_MIN a
    COMPONENT_MAX. None si el premio no es alcanzable con ese Índice de Docentes.
    """
    low, high = TIER_RANGE[tier]
    low = max(low, (COMPONENT_MIN + teacherIndex) / 2.0)
    high = min(high, (COMPONENT_MAX + teacherIndex) / 2.0)
    if low > high:
        return None
    return low, high


def choose_tier(wanted, teacherIndex):
    """El premio pedido si es alcanzable; si no, el alcanzable más cercano en TIER_ORDER."""
    position = TIER_ORDER.index(wanted)
    candidates = sorted(TIER_ORDER, key=lambda t: abs(TIER_ORDER.index(t) - position))
    for tier in candidates:
        if feasible_range(tier, teacherIndex):
            return tier
    return None


def plan_schools(teacherIndexes):
    """
    teacherIndexes: {pecaId: Índice de Docentes o None}.
    Devuelve {pecaId: {"tier": premio|None, "integral": float, "components": {...}}}.
    Las escuelas sin Índice de Docentes (tier None) quedan sin premio por datos incompletos.
    """
    plan = {}
    withIndex = sorted([(t, p) for p, t in teacherIndexes.items() if t is not None],
                       reverse=True)
    cursors = {"top": 0, "other": 0}
    for teacherIndex, pecaId in withIndex:
        group = "top" if teacherIndex >= TOP_TEACHER_INDEX else "other"
        pattern = TOP_PATTERN if group == "top" else OTHER_PATTERN
        wanted = pattern[cursors[group] % len(pattern)]
        cursors[group] += 1
        tier = choose_tier(wanted, teacherIndex)
        if tier is None:  # no debería ocurrir: siempre hay algún premio alcanzable
            plan[pecaId] = {"tier": None, "teacherIndex": teacherIndex,
                            "integral": random.uniform(45.0, 85.0)}
            continue
        low, high = feasible_range(tier, teacherIndex)
        final = random.uniform(low, high)
        integral = min(COMPONENT_MAX, max(COMPONENT_MIN, 2 * final - teacherIndex))
        plan[pecaId] = {"tier": tier, "teacherIndex": teacherIndex, "integral": integral}
    for pecaId, teacherIndex in teacherIndexes.items():
        if teacherIndex is None:
            plan[pecaId] = {"tier": None, "teacherIndex": None,
                            "integral": random.uniform(45.0, 85.0)}
    for item in plan.values():
        item["components"] = split_components(item["integral"])
    return plan


def split_components(integral):
    """
    4 componentes (IAA, PPM, M2M, 60LM, en %) cuyo promedio es `integral`, con variación
    entre ellos pero siempre dentro de [COMPONENT_MIN, COMPONENT_MAX].
    """
    spread = min(10.0, integral - COMPONENT_MIN, COMPONENT_MAX - integral)
    spread = max(spread, 0.0)
    noise = [random.uniform(-spread / 2.0, spread / 2.0) for _ in range(4)]
    mean = sum(noise) / 4.0
    values = [integral + n - mean for n in noise]
    return {"iaa": values[0], "wordsPerMin": values[1],
            "multiplicationsPerMin": values[2], "operationsPerMin": values[3]}


def lapse_targets(target):
    """Índices objetivo (%) de los lapsos 1, 2 y 3: el lapso 3 es `target` y hay mejora."""
    first = target * random.uniform(0.60, 0.75)
    second = first + (target - first) * random.uniform(0.40, 0.70)
    return {1: first, 2: second, 3: target}


def student_values(goal, target, count):
    """
    Valores (enteros) de `count` estudiantes para una meta `goal`, de modo que el índice
    promedio (valor / meta * 100) quede cerca de `target` (%). Cada estudiante varía ±12 %.
    """
    percents = [min(130.0, max(0.0, target + random.uniform(-12.0, 12.0))) for _ in range(count)]
    shift = target - sum(percents) / float(count)
    percents = [min(130.0, max(0.0, p + shift)) for p in percents]
    return [int(round(goal * p / 100.0)) for p in percents]


def iaa_raw_targets(iaaPercent):
    """Puntos IAA (0-35) objetivo de los lapsos 1, 2 y 3 a partir del % del lapso 3."""
    return dict((lapse, value * IAA_MAX / 100.0)
                for lapse, value in lapse_targets(iaaPercent).items())


def indicator_values(rawTarget):
    """
    5 valores (uno por indicador, entre 1.0 y 7.0, con un decimal) cuya suma es `rawTarget`
    (puntos IAA, 0-35). Se reparte parejo con variación y se compensa para conservar la suma.
    """
    rawTarget = min(35.0, max(5.0, rawTarget))
    base = rawTarget / 5.0
    noise = [random.uniform(-0.6, 0.6) for _ in range(5)]
    mean = sum(noise) / 5.0
    return [round(min(7.0, max(1.0, base + n - mean)), 1) for n in noise]


# ------------------------------------------------------------------- escritura

def ensure_goals(schoolYear, fill):
    """Metas del año por grado. Devuelve (ok, lista de problemas)."""
    problems = []
    goals = schoolYear.pecaSetting.goalSetting
    for grade in range(1, 7):
        setting = goals["grade{}".format(grade)]
        for key, defaults in DEFAULT_GOALS.items():
            current = setting[key] if setting is not None else None
            if current is None or current <= 1:
                if fill and setting is not None:
                    setting[key] = defaults[grade - 1]
                else:
                    problems.append("grado {} · {}".format(grade, key))
    return (not problems), problems


def eligible_sections(peca):
    """(posición, sección) de las secciones activas de 1.º a 6.º (las únicas con metas)."""
    return [(i, s) for i, s in enumerate(peca.school.sections)
            if not s.isDeleted and s.grade in GOAL_GRADES]


def active_students(section):
    """(posición, estudiante) de los activos; la posición es la que tienen en la lista guardada."""
    return [(j, st) for j, st in enumerate(section.students) if not st.isDeleted]


def write_student_diagnostics(peca, schoolYear, plan, timings):
    """
    Escribe los diagnósticos de los estudiantes activos de 1.º a 6.º. Devuelve cuántos.
    `timings` (Counter) acumula los segundos de cada fase: calculo, resumenes, guardar_peca,
    guardar_escuela.

    No usa `peca.save()`: en un PECA grande MongoEngine tarda minutos solo en recorrer todos
    los documentos embebidos para limpiar los campos modificados (medido: 7.5 s en una escuela
    de 40 estudiantes). En su lugar se hace un único `$set` sobre las rutas que cambiaron.
    """
    goals = schoolYear.pecaSetting.goalSetting
    now = datetime.utcnow()
    written = 0
    updates = {}  # ruta de MongoDB -> documento embebido a guardar

    t = time.time()
    sections = eligible_sections(peca)
    for sectionPos, section in sections:
        students = active_students(section)
        if not students:
            continue
        setting = goals["grade{}".format(section.grade)]
        values = {}
        for indexKey, field, _ in DIAGNOSTICS:
            targets = lapse_targets(plan["components"][indexKey])
            goal = setting[field]
            for lapse in (1, 2, 3):
                values[(field, lapse)] = student_values(goal, targets[lapse], len(students))
        for position, (studentPos, student) in enumerate(students):
            for lapse in (1, 2, 3):
                diagnostic = student["lapse{}".format(lapse)]
                if diagnostic is None:
                    diagnostic = Diagnostic()
                    student["lapse{}".format(lapse)] = diagnostic
                date = now - timedelta(days=LAPSE_AGE_DAYS[lapse] + random.randint(-5, 5))
                for _, field, dateField in DIAGNOSTICS:
                    diagnostic[field] = values[(field, lapse)][position]
                    diagnostic[dateField] = date
                diagnostic.calculateIndex(setting)
                updates["school.sections.{0}.students.{1}.lapse{2}".format(
                    sectionPos, studentPos, lapse)] = diagnostic
            written += 1
    timings["calculo"] += time.time() - t

    t = time.time()
    for sectionPos, section in sections:
        section.refreshDiagnosticsSummary()
        updates["school.sections.{0}.diagnostics".format(sectionPos)] = section.diagnostics
    peca.school.refreshDiagnosticsSummary()
    updates["school.diagnostics"] = peca.school.diagnostics
    timings["resumenes"] += time.time() - t

    t = time.time()
    document = dict((path, value.to_mongo()) for path, value in updates.items())
    document["updatedAt"] = datetime.utcnow()
    PecaProject._get_collection().update_one({"_id": peca.id}, {"$set": document})
    timings["guardar_peca"] += time.time() - t

    t = time.time()
    schoolUser = SchoolUser.objects(id=peca.project.school.id).first()
    if schoolUser:
        schoolUser.diagnostics = peca.school.diagnostics
        schoolUser.save()
    timings["guardar_escuela"] += time.time() - t
    return written


def write_iaa(peca, iaaPercent, stats):
    """Reemplaza los evaluadores del IAA del PECA por evaluaciones de prueba (sin correos)."""
    pecaId = str(peca.id)
    seeded = EnvironmentalDiagnosticEvaluator.objects(
        pecaId=pecaId, name__startswith=EVALUATOR_NAME_PREFIX)
    stats["iaaDeleted"] += seeded.count()
    seeded.delete()
    others = EnvironmentalDiagnosticEvaluator.objects(pecaId=pecaId, isDeleted=False)
    stats["iaaSoftDeleted"] += others.count()
    others.update(set__isDeleted=True)

    service = EnvironmentalDiagnosticService()
    for lapse, rawTarget in iaa_raw_targets(iaaPercent).items():
        for number in range(1, EVALUATORS_PER_LAPSE + 1):
            # Un evaluador un poco por encima y otro por debajo: el promedio es el objetivo.
            delta = 0.8 if number == 1 else -0.8
            token = uuid.uuid4().hex
            EnvironmentalDiagnosticEvaluator(
                pecaId=pecaId, lapse=str(lapse),
                name=u"{} {}".format(EVALUATOR_NAME_PREFIX, number),
                email="evaluador{}.{}@example.com".format(number, pecaId[-6:]),
                phone="04140000000", token=token).save()
            results = {}
            for (key, subs), value in zip(IAA_INDICATORS, indicator_values(rawTarget + delta)):
                results[key] = {"subcriteria": dict((sub, {"value": value}) for sub in subs)}
            body, status = service.submit_evaluation(token, {"results": results})
            if status != 200:
                raise RuntimeError("submit_evaluation falló: {} {}".format(status, body))
            stats["iaaEvaluators"] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--school-year", default="2026 - 2027")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-db", default=None)
    parser.add_argument("--set-missing-goals", action="store_true")
    parser.add_argument("--only", default=None,
                        help="procesar solo las escuelas cuyo nombre contenga este texto")
    parser.add_argument("--profile", action="store_true",
                        help="perfila la primera escuela procesada y muestra las funciones más lentas")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    app = create_app(os.getenv('INSTANCE'))
    with app.app_context():
        dbName = get_db().name
        say("Base de datos: {0}".format(dbName))
        if args.apply and args.confirm_db != dbName:
            say("ABORTADO: --confirm-db debe ser '{0}' para escribir.".format(dbName))
            return 1
        say("Modo: {0}".format("ESCRITURA" if args.apply else "SIMULACION (use --apply para escribir)"))

        schoolYear = find_school_year(args.school_year)
        if not schoolYear:
            say("No se encontró el año escolar '{0}'.".format(args.school_year))
            return 1
        say("Año escolar: {0} ({1})".format(schoolYear.name, schoolYear.id))

        ok, problems = ensure_goals(schoolYear, args.set_missing_goals)
        if not ok:
            say("ABORTADO: metas del año escolar sin configurar (vacías o <= 1):")
            for problem in problems:
                say("  - {0}".format(problem))
            say("Configúrelas en el año escolar o use --set-missing-goals.")
            return 1
        if args.set_missing_goals and args.apply:
            schoolYear.save()

        say("Cargando los PECA del año (documentos completos, puede tardar)...")
        loadStart = time.time()
        pecas = [p for p in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False)
                 if p.project and p.project.school and p.school]
        say("Cargados {0} PECA en {1:.1f}s".format(len(pecas), time.time() - loadStart))
        withStudents, noStudents = [], []
        for peca in pecas:
            count = sum(len(active_students(s)) for _, s in eligible_sections(peca))
            (withStudents if count else noStudents).append((peca, count))

        if args.only:
            needle = args.only.lower()
            withStudents = [(p, c) for p, c in withStudents
                            if needle in (p.project.school.name or "").lower()]
            say("--only '{0}': {1} escuela(s)".format(args.only, len(withStudents)))

        teacherIndexes = {}
        for peca, _ in withStudents:
            percentages = [c.percentage for c in TeacherCoevaluation.objects(
                pecaId=str(peca.id), teacherSubmittedAt__ne=None,
                coordinatorSubmittedAt__ne=None).only('percentage')]
            teacherIndexes[str(peca.id)] = school_index(percentages)
        plan = plan_schools(teacherIndexes)

        say("-" * 60)
        say("PECA del año: {0} | con estudiantes activos (1.º a 6.º): {1} | sin ellos (omitidos): {2}".format(
            len(pecas), len(withStudents), len(noStudents)))
        for peca, _ in noStudents:
            say("  omitida (sin estudiantes de 1.º a 6.º): {0}".format(peca.project.school.name))
        planned = Counter(plan[str(p.id)]["tier"] or "incomplete" for p, _ in withStudents)
        say("Plan: " + ", ".join("{0}={1}".format(k, planned.get(k, 0))
                                   for k in TIER_ORDER + ["incomplete"]))
        say("{0:<38} {1:>5} {2:>9} {3:>9} {4:>9}".format(
            "Escuela", "Estud", "Docentes", "Integral", "Premio"))
        for peca, count in sorted(withStudents, key=lambda x: x[0].project.school.name or ""):
            item = plan[str(peca.id)]
            say("{0:<38} {1:>5} {2:>9} {3:>9.1f} {4:>9}".format(
                (peca.project.school.name or "")[:38], count,
                "—" if item["teacherIndex"] is None else "{0:.1f}".format(item["teacherIndex"]),
                item["integral"], item["tier"] or "incompleto"))

        if not args.apply:
            say("Simulación: no se escribió nada.")
            return 0

        stats = Counter()
        started = time.time()
        total = len(withStudents)
        say("Escribiendo {0} escuelas (una línea por escuela al terminar)...".format(total))
        profiler = cProfile.Profile() if args.profile else None
        for position, (peca, count) in enumerate(withStudents, 1):
            item = plan[str(peca.id)]
            timings = Counter()
            t0 = time.time()
            if profiler and position == 1:
                profiler.enable()
            stats["students"] += write_student_diagnostics(peca, schoolYear, item, timings)
            if profiler and position == 1:
                profiler.disable()
            t1 = time.time()
            write_iaa(peca, item["components"]["iaa"], stats)
            t2 = time.time()
            stats["pecas"] += 1
            say("[{0}/{1}] {2} · {3} estudiantes · {4:.1f}s (cálculo {5:.1f} · resúmenes {6:.1f} · "
                "guardar PECA {7:.1f} · guardar escuela {8:.1f}) · IAA {9:.1f}s · acumulado {10:.0f}s".format(
                    position, total, (peca.project.school.name or "")[:34], count, t1 - t0,
                    timings["calculo"], timings["resumenes"], timings["guardar_peca"],
                    timings["guardar_escuela"], t2 - t1, t2 - started))
            if profiler and position == 1:
                out = io.StringIO()
                pstats.Stats(profiler, stream=out).sort_stats("cumulative").print_stats(25)
                say("--- Perfil de la primera escuela (25 funciones más costosas) ---")
                say(out.getvalue())
        say("Actualizando el resumen del año escolar...")
        schoolYear.refreshDiagnosticsSummary()
        schoolYear.save()

        say("-" * 60)
        say("PECA actualizados:            {0}".format(stats["pecas"]))
        say("Estudiantes con diagnósticos: {0}".format(stats["students"]))
        say("Evaluadores IAA creados:      {0}".format(stats["iaaEvaluators"]))
        say("Evaluadores IAA previos: {0} borrados (de este script) y {1} marcados como borrados".format(
            stats["iaaDeleted"], stats["iaaSoftDeleted"]))

        report, _status = HqsAwardService().report(str(schoolYear.id))
        say("-" * 60)
        say("Reporte de premios (conteos): {0}".format(report["counts"]))
        mismatches = 0
        for row in report["schools"]:
            item = plan.get(row["pecaId"])
            if not item:
                continue
            expected = item["tier"] or None
            actual = row["award"] if row["status"] == "awarded" else (
                "none" if row["status"] == "none" else None)
            if expected != actual:
                mismatches += 1
                say("  DIFIERE {0}: planificado={1} reporte={2} (final={3})".format(
                    row["name"], expected or "incompleto", row["awardLabel"], row["finalIndex"]))
        say("Escuelas que no coinciden con lo planificado: {0}".format(mismatches))
    return 0


if __name__ == "__main__":
    sys.exit(main())
