# -*- coding: utf-8 -*-
# app/helpers/coevaluation_helper.py
"""
Instrumento de Co-evaluación Docente AmbLeMa HQS (versión 1).

Fuente única del catálogo de ítems, la escala y el cálculo de resultados:
el front y el backoffice lo reciben desde la API, no lo duplican.
"""

from __future__ import division

import hashlib
import binascii
import os


INSTRUMENT_VERSION = 1
MIN_SCORE = 0
MAX_SCORE = 5

DIMENSIONS = [
    {"code": "A", "name": u"Aplicación de las estrategias ordinarias de AmbLeMa"},
    {"code": "B", "name": u"Herramientas Pedagógicas"},
    {"code": "C", "name": u"Organización, Participación y Eventos Especiales"},
]

ITEMS = [
    {"number": 1, "dimension": "A", "title": u"Hora TAL",
     "question": u"¿Aplica y mantiene la estrategia de la Hora TAL todos los días en el aula y en sintonía con el resto de la escuela?"},
    {"number": 2, "dimension": "A", "title": u"Momento X",
     "question": u"¿Planifica y desarrolla, a diario, el Momento X con sus estudiantes?"},
    {"number": 3, "dimension": "A", "title": u"Ingenio Matemático",
     "question": u"¿Promueve y ejercita el momento de Ingenio Matemático cada día?"},
    {"number": 4, "dimension": "A", "title": u"Actividades de formación docente",
     "question": u"¿Participa activamente en alguna o algunas de las propuestas formativas a lo largo del año? Por ejemplo, Programa Papagayo, Khan Academy, JumpMath u otras."},
    {"number": 5, "dimension": "A", "title": u"Módulo ambiental",
     "question": u"¿Propone y participa en estrategias o actividades que mejoren los indicadores del IAA (Índice Ambiental AmbLeMa) de la escuela? (Limpieza de la escuela, separación de desechos, cuidado de la biodiversidad, buen uso del agua e impacto en la limpieza de la comunidad)"},
    {"number": 6, "dimension": "A", "title": u"ProAmb (Proyecto Ambiental AmbLeMa)",
     "question": u"¿Planifica y desarrolla, con sus estudiantes, los diferentes EcoTemas del ProAmb del año escolar? (Bosque de Chocolate, Venezuela Megadiversa o Feria Científica)"},
    {"number": 7, "dimension": "B", "title": u"Uso del Vademécum",
     "question": u"¿Consulta y utiliza el Vademécum AmbLeMa como guía de sus actividades?"},
    {"number": 8, "dimension": "B", "title": u"Conocer y comunicar diagnósticos",
     "question": u"¿Conoce, analiza y tiene presentes los resultados de los diagnósticos de sus estudiantes?"},
    {"number": 9, "dimension": "B", "title": u"Mejora en diagnósticos",
     "question": u"¿Conoce las metas propuestas para su grado y busca estrategias para que sus estudiantes mejoren en los resultados?"},
    {"number": 10, "dimension": "B", "title": u"AAA (Aula Activa AmbLeMa)",
     "question": u"¿Planifica y prepara con anticipación la participación de su grupo de estudiantes en la AAA?"},
    {"number": 11, "dimension": "C", "title": u"Actividad especial 2do lapso",
     "question": u"¿Apoya y colabora activamente en la organización de la actividad especial del 2do lapso?"},
    {"number": 12, "dimension": "C", "title": u"Feriamblema",
     "question": u"¿Prepara y participa con su grupo en la realización de la Feriamblema?"},
    {"number": 13, "dimension": "C", "title": u"Amblemonedas",
     "question": u"¿Implementa el sistema de Amblemonedas como incentivo pedagógico en el grupo?"},
    {"number": 14, "dimension": "C", "title": u"Bodega AmbLeMa",
     "question": u"¿Participa y aporta ideas para el buen desarrollo de las Bodegas AmbLeMa?"},
    {"number": 15, "dimension": "C", "title": u"Asistencia",
     "question": u"¿Mantiene una asistencia constante y puntual a las actividades escolares y de AmbLeMa?"},
]

N_ITEMS = len(ITEMS)
MAX_TOTAL = N_ITEMS * MAX_SCORE  # 75

SCALE = [
    {"score": 0, "label": u"No iniciado / No",
     "description": u"No se ejecuta la práctica o no hay evidencia."},
    {"score": 1, "label": u"Inicial",
     "description": u"Se realiza en forma muy ocasional o esporádica."},
    {"score": 2, "label": u"En proceso",
     "description": u"Se aplica con cierta frecuencia, pero requiere más constancia o acompañamiento."},
    {"score": 3, "label": u"Aceptable / Consolidándose",
     "description": u"Se cumple regularmente siguiendo los lineamientos básicos."},
    {"score": 4, "label": u"Avanzado",
     "description": u"Cumplimiento constante, con alto nivel de compromiso e integración."},
    {"score": 5, "label": u"Excelente / Modélico",
     "description": u"Aplicación continua, sobresaliente, autónoma e innovadora."},
]

# Ordenados de mayor a menor; minTotal en puntos sobre 75 (equivale a 80/60/40 %).
LEVELS = [
    {"code": "excellence", "label": u"Docente HQS con Excelencia", "minTotal": 60, "minPercentage": 80},
    {"code": "commitment", "label": u"Docente HQS con Compromiso", "minTotal": 45, "minPercentage": 60},
    {"code": "progress", "label": u"Docente HQS en Avance", "minTotal": 30, "minPercentage": 40},
    {"code": "beginning", "label": u"Docente HQS en Inicio", "minTotal": 0, "minPercentage": 0},
]
LEVEL_CODES = [level["code"] for level in LEVELS]

STATUS_NOT_STARTED = "not_started"
STATUS_PENDING_TEACHER = "pending_teacher"
STATUS_PENDING_COORDINATOR = "pending_coordinator"
STATUS_COMPLETED = "completed"
STATUS_LABELS = {
    STATUS_NOT_STARTED: u"Sin iniciar",
    STATUS_PENDING_TEACHER: u"Pendiente docente",
    STATUS_PENDING_COORDINATOR: u"Pendiente coordinador",
    STATUS_COMPLETED: u"Completada",
}

GRADE_NAMES = {
    "0": u"Preescolar",
    "1": u"1er Grado",
    "2": u"2do Grado",
    "3": u"3er Grado",
    "4": u"4to Grado",
    "5": u"5to Grado",
    "6": u"6to Grado",
}


def get_instrument():
    """Catálogo serializable que consumen front y backoffice."""
    return {
        "version": INSTRUMENT_VERSION,
        "minScore": MIN_SCORE,
        "maxScore": MAX_SCORE,
        "maxTotal": MAX_TOTAL,
        "dimensions": DIMENSIONS,
        "items": ITEMS,
        "scale": SCALE,
        "levels": LEVELS,
    }


def get_level(total):
    """Nivel según el puntaje total (0-75). None si no hay total."""
    if total is None:
        return None
    for level in LEVELS:
        if total >= level["minTotal"]:
            return level
    return LEVELS[-1]


def get_level_label(code):
    for level in LEVELS:
        if level["code"] == code:
            return level["label"]
    return None


def compute_results(teacherScores, coordinatorScores):
    """
    Promedio por ítem, total (sobre 75), porcentaje y nivel.
    El promedio de cada ítem es la parte entera de (docente + coordinador) / 2,
    por lo que el total también es entero. Devuelve None si falta algún lado.
    """
    if not teacherScores or not coordinatorScores:
        return None
    if len(teacherScores) != N_ITEMS or len(coordinatorScores) != N_ITEMS:
        return None
    # Puntajes enteros y no negativos: // equivale a truncar (p. ej. (4 + 3) // 2 = 3).
    averages = [int(t + c) // 2 for t, c in zip(teacherScores, coordinatorScores)]
    total = sum(averages)
    percentage = round(total * 100 / MAX_TOTAL, 2)
    level = get_level(total)
    return {
        "averages": averages,
        "totalScore": total,
        "percentage": percentage,
        "level": level["code"],
    }


def school_index(percentages):
    """Índice de Docentes HQS de la escuela: promedio de los % completados."""
    values = [p for p in percentages if p is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def sections_label(sections, teacherId):
    """Grados y secciones del PECA asignados al docente, p. ej. '3er Grado A, 4to Grado B'."""
    labels = []
    for section in sorted(sections, key=lambda s: (s.grade or "", s.name or "")):
        if getattr(section, "isDeleted", False):
            continue
        if section.teacher and str(section.teacher.id) == str(teacherId):
            labels.append(u"{} {}".format(
                GRADE_NAMES.get(section.grade, section.grade or ""), section.name or "").strip())
    return u", ".join(labels)


def generate_token():
    """Token aleatorio de 256 bits (hex). Compatible con Python 2.7 y 3."""
    token = binascii.hexlify(os.urandom(32))
    if not isinstance(token, str):
        token = token.decode("ascii")
    return token


def hash_token(token):
    """SHA-256 del token: en BD solo se guarda el hash."""
    if token is None:
        return None
    if not isinstance(token, bytes):
        token = token.encode("utf-8")
    return hashlib.sha256(token).hexdigest()
