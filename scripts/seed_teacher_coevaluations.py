# -*- coding: utf-8 -*-
"""
Genera coevaluaciones docentes de PRUEBA para todos los PECA de un año escolar,
para revisar el reporte "Coevaluación docentes HQS" con datos.

- Por cada docente activo de cada PECA crea la coevaluación completa: puntajes
  aleatorios 1-5 en los 15 ítems, tanto del coordinador como del docente.
- NO envía correos. Deja el rastro del enlace como si se hubiera enviado
  (emailSentAt / emailSentTo / emailSentCount); el token no se conserva, igual que
  en el flujo real (se elimina cuando el docente guarda).
- Distribución para probar el criterio de excelencia (> 80 %, es decir total >= 61/75):
    * ~20 % de todas las coevaluaciones son de excelencia (--excellence-ratio).
    * Al menos 6 escuelas (--strong-schools) tienen TODOS sus docentes en excelencia
      (--strong-fraction 1.0). Se eligen entre las escuelas con más docentes.
    * Las demás escuelas no llegan a mayoría de excelencia, para que el resultado se
      pueda contrastar sin ambigüedad.
    * ~20 % de los docentes quedan en "En inicio" (< 30 pts; --beginning-ratio).
    * El resto es aleatorio 1-5 entre 30 y 60 pts (En avance / Compromiso).
- Por defecto es una SIMULACIÓN: no escribe nada. Para escribir hay que pasar
  --apply y --confirm-db <nombre de la base> (debe coincidir con la base activa).
- --reset BORRA primero todas las coevaluaciones de ese año escolar (necesita --apply).
  Sin --reset se respetan las que ya existen completas.

Uso (dentro del contenedor del backend):
  docker exec amblema_development_back sh -c 'cd /home && python scripts/seed_teacher_coevaluations.py --reset'
  docker exec amblema_development_back sh -c 'cd /home && python scripts/seed_teacher_coevaluations.py --reset --apply --confirm-db amblema'

Opciones:
  --school-year "2026 - 2027"   nombre del año escolar (por defecto 2026 - 2027)
  --seed N                      semilla para repetir los mismos valores
  --excellence-ratio 0.20       proporción global de coevaluaciones de excelencia
  --strong-schools 6            escuelas con (casi) todos los docentes en excelencia
  --strong-fraction 1.0         parte de los docentes de esas escuelas en excelencia
  --beginning-ratio 0.20        proporción global de docentes en "En inicio"
  --reset                       borra antes las coevaluaciones del año escolar
"""
from __future__ import print_function

import argparse
import math
import os
import random
import re
import sys
from collections import Counter
from datetime import datetime, timedelta

# Add the app directory to sys.path
sys.path.append('/home')

from mongoengine.connection import get_db

from app import create_app
from app.helpers.coevaluation_helper import N_ITEMS, MAX_TOTAL, LEVEL_CODES
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.models.teacher_coevaluation_model import TeacherCoevaluation
from app.services.teacher_coevaluation_service import TeacherCoevaluationService

LOW, HIGH = 1, 5
# Excelencia = más de 80 %: total >= 61 de 75 (el promedio por ítem es (t + c) // 2).
EXCELLENCE_MIN_TOTAL = int(MAX_TOTAL * 0.8) + 1
BEGINNING_MAX_TOTAL = 29  # "En inicio": < 30 pts


def normalize(name):
    """'2026 - 2027' == '2026-2027' == '2026 – 2027'."""
    return re.sub(u"[\\s\\-–—]+", u"", name or u"")


def total_of(teacherScores, coordinatorScores):
    return sum((t + c) // 2 for t, c in zip(teacherScores, coordinatorScores))


def random_pair(profile):
    """(puntajes docente, puntajes coordinador) según el perfil: excellence | beginning | other."""
    while True:
        if profile == "excellence":
            # 4 o 5 en todos los ítems: cada promedio es >= 4 y el total >= 60.
            teacher = [random.choice((4, 5)) for _ in range(N_ITEMS)]
            coordinator = [random.choice((4, 5)) for _ in range(N_ITEMS)]
        else:
            teacher = [random.randint(LOW, HIGH) for _ in range(N_ITEMS)]
            coordinator = [random.randint(LOW, HIGH) for _ in range(N_ITEMS)]
        total = total_of(teacher, coordinator)
        if profile == "excellence":
            ok = total >= EXCELLENCE_MIN_TOTAL
        elif profile == "beginning":
            ok = total <= BEGINNING_MAX_TOTAL
        else:
            ok = BEGINNING_MAX_TOTAL < total < EXCELLENCE_MIN_TOTAL
        if ok:
            return teacher, coordinator


def find_school_year(name):
    wanted = normalize(name)
    for year in SchoolYear.objects(isDeleted=False):
        if normalize(year.name) == wanted:
            return year
    return None


def majority(n):
    """Mínimo de docentes para que sean 'la mayoría' (más de la mitad)."""
    return n // 2 + 1


def plan_levels(groups, ratio, strongCount, strongFraction, beginningRatio):
    """
    groups: {pecaId: [teacherId, ...]} (solo lo que se va a generar).
    Devuelve (excelencia, [pecaId escuelas fuertes], objetivo, inicio); los conjuntos son
    de (pecaId, teacherId).
    """
    total = sum(len(v) for v in groups.values())
    target = int(round(total * ratio))

    # Escuelas fuertes: entre las de más docentes (mínimo 3 si es posible), al azar.
    candidates = [p for p, v in groups.items() if len(v) >= 3] or list(groups.keys())
    random.shuffle(candidates)
    strong = candidates[:strongCount]

    chosen = set()
    for pecaId in strong:
        teachers = groups[pecaId]
        # strongFraction de la escuela (1.0 = todos), y siempre más de la mitad.
        k = max(majority(len(teachers)), int(math.ceil(len(teachers) * strongFraction)))
        for teacherId in random.sample(teachers, min(k, len(teachers))):
            chosen.add((pecaId, teacherId))

    target = max(target, len(chosen))
    # Resto de excelencias: en las demás escuelas, sin llegar nunca a la mayoría.
    pool = []
    for pecaId, teachers in groups.items():
        if pecaId in strong:
            continue
        cap = len(teachers) // 2  # máximo sin alcanzar la mayoría
        picks = random.sample(teachers, cap) if cap else []
        pool.extend((pecaId, t) for t in picks)
    random.shuffle(pool)
    chosen.update(pool[:max(0, target - len(chosen))])

    # "En inicio": entre los docentes que no son de excelencia.
    rest = [(p, t) for p, v in groups.items() for t in v if (p, t) not in chosen]
    random.shuffle(rest)
    beginning = set(rest[:int(round(total * beginningRatio))])
    return chosen, strong, target, beginning


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--school-year", default="2026 - 2027")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-db", default=None)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--excellence-ratio", type=float, default=0.20)
    parser.add_argument("--strong-schools", type=int, default=6)
    parser.add_argument("--strong-fraction", type=float, default=1.0)
    parser.add_argument("--beginning-ratio", type=float, default=0.20)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    app = create_app(os.getenv('INSTANCE'))
    with app.app_context():
        dbName = get_db().name
        print("Base de datos: {0}".format(dbName))
        if args.apply and args.confirm_db != dbName:
            print("ABORTADO: --confirm-db debe ser '{0}' para escribir.".format(dbName))
            return 1
        print("Modo: {0}".format("ESCRITURA" if args.apply else "SIMULACION (use --apply para escribir)"))

        schoolYear = find_school_year(args.school_year)
        if not schoolYear:
            print("No se encontró el año escolar '{0}'.".format(args.school_year))
            return 1
        print("Año escolar: {0} ({1})".format(schoolYear.name, schoolYear.id))

        existingCount = TeacherCoevaluation.objects(schoolYearId=str(schoolYear.id)).count()
        if args.reset:
            print("Coevaluaciones actuales del año escolar a BORRAR: {0}".format(existingCount))
            if args.apply:
                TeacherCoevaluation.objects(schoolYearId=str(schoolYear.id)).delete()
                print("Borradas.")

        service = TeacherCoevaluationService()
        pecas = {}
        groups = {}
        stats = Counter()
        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
            stats["pecas"] += 1
            school = service._get_school(peca)
            if not school:
                stats["noSchool"] += 1
                continue
            pending = []
            for teacher in school.teachers:
                if not service._is_active(teacher):
                    stats["inactive"] += 1
                    continue
                if not args.reset:
                    existing = TeacherCoevaluation.objects(
                        pecaId=str(peca.id), teacherId=str(teacher.id)).first()
                    if existing and existing.coordinatorSubmittedAt and existing.teacherSubmittedAt:
                        stats["skipped"] += 1
                        continue
                pending.append((teacher.id, teacher, school))
            if pending:
                groups[str(peca.id)] = [str(t[0]) for t in pending]
                pecas[str(peca.id)] = (peca, school, dict((str(t[0]), t[1]) for t in pending))

        excellent, strong, target, beginning = plan_levels(
            groups, args.excellence_ratio, args.strong_schools,
            args.strong_fraction, args.beginning_ratio)
        total = sum(len(v) for v in groups.values())
        print("-" * 50)
        print("Coevaluaciones a generar: {0} | de excelencia: {1} ({2:.1f} %)".format(
            total, len(excellent), (len(excellent) * 100.0 / total) if total else 0))
        print("En inicio planificados: {0} ({1:.1f} %)".format(
            len(beginning), (len(beginning) * 100.0 / total) if total else 0))
        print("Escuelas fuertes (excelencia): {0}".format(len(strong)))
        if len(strong) < args.strong_schools:
            print("AVISO: solo hay {0} escuelas con docentes activos.".format(len(strong)))

        levels = Counter()
        strongRows = []
        for pecaId, teacherIds in groups.items():
            peca, school, teachersById = pecas[pecaId]
            coordinator = peca.project.coordinator if peca.project else None
            nExcellent = 0
            for teacherId in teacherIds:
                isExcellent = (pecaId, teacherId) in excellent
                profile = ("excellence" if isExcellent else
                           "beginning" if (pecaId, teacherId) in beginning else "other")
                teacherScores, coordinatorScores = random_pair(profile)
                if isExcellent:
                    nExcellent += 1
                if not args.apply:
                    levels[profile] += 1
                    continue

                teacher = teachersById[teacherId]
                coevaluation = service._get_or_create(peca, school, teacher)
                service._refresh_snapshot(coevaluation, peca, school, teacher)

                # Fechas coherentes: enlace enviado -> docente; el coordinador, en cualquier orden.
                now = datetime.utcnow()
                sentAt = now - timedelta(days=random.randint(2, 10), minutes=random.randint(0, 600))
                teacherAt = sentAt + timedelta(hours=random.randint(1, 48))
                coordinatorAt = now - timedelta(days=random.randint(0, 10), minutes=random.randint(0, 600))

                coevaluation.coordinatorScores = coordinatorScores
                coevaluation.coordinatorSubmittedAt = coordinatorAt
                coevaluation.coordinatorSubmittedBy = str(coordinator.id) if coordinator else None
                coevaluation.teacherScores = teacherScores
                coevaluation.teacherSubmittedAt = teacherAt
                coevaluation.tokenHash = None  # el token se elimina al guardar el docente
                coevaluation.completedAt = max(teacherAt, coordinatorAt)

                email = (teacher.email or "").strip()
                if email:
                    coevaluation.emailSentAt = sentAt
                    coevaluation.emailSentTo = email
                    coevaluation.emailSentCount = 1
                else:
                    stats["noEmail"] += 1

                coevaluation.save()  # clean() calcula promedios, total, % y nivel
                levels[coevaluation.level] += 1
                stats["created"] += 1
            if pecaId in strong:
                strongRows.append((school.name, nExcellent, len(teacherIds)))

        print("Escuelas fuertes (escuela: excelencia / docentes):")
        for name, nExc, n in sorted(strongRows):
            print("  - {0}: {1} / {2}".format(name.encode("utf-8") if str is bytes else name, nExc, n))
        if args.apply:
            print("Por nivel: " + ", ".join(
                "{0}={1}".format(code, levels.get(code, 0)) for code in LEVEL_CODES))
        print("PECA procesados:             {0}".format(stats["pecas"]))
        print("PECA sin escuela:            {0}".format(stats["noSchool"]))
        print("Coevaluaciones creadas:      {0}".format(stats["created"]))
        print("Ya completas (respetadas):   {0}".format(stats["skipped"]))
        print("Docentes inactivos omitidos: {0}".format(stats["inactive"]))
        print("Docentes sin correo (sin rastro de envío): {0}".format(stats["noEmail"]))
        if not args.apply:
            print("Por perfil (plan): " + ", ".join(
                "{0}={1}".format(k, v) for k, v in sorted(levels.items())))
            print("Simulación: no se escribió ni se borró nada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
