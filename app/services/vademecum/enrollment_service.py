# -*- coding: utf-8 -*-
# app/services/vademecum/enrollment_service.py
"""Matrícula vigente de un docente (regla de GES-04).

Solo lectura: no escribe en `users` ni en `peca_project` y no guarda nada en la cuenta.
Ver Vademecum/docs/GES-04/2026-11-10-vademecum-teacher-enrollment-rule.md.
"""

import logging

from bson import ObjectId
from bson.errors import InvalidId

from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.models.user_model import User

logger = logging.getLogger(__name__)

SCHOOL_USER_CLS = "User.SchoolUser"
# Índice de users.teachers.email sin distinguir mayúsculas (los emails de docentes no
# están normalizados en la BD). Las consultas deben usar la misma collation para usarlo.
TEACHER_EMAIL_INDEX = "vademecum_teachers_email_ci"
CASE_INSENSITIVE = {"locale": "en", "strength": 2}
GRADE_ORDER = ("0", "1", "2", "3", "4", "5", "6")


def normalize_email(email):
    return (email or "").strip().lower()


def ensure_teacher_email_index():
    """Crea el índice de users.teachers.email (idempotente)."""
    User._get_collection().create_index(
        [("teachers.email", 1)], name=TEACHER_EMAIL_INDEX, collation=CASE_INSENSITIVE)


def _as_object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def _key(value):
    """Id como texto, sea ObjectId o string (las secciones guardan el id como texto)."""
    return "" if value is None else str(value)


def _sorted_grades(grades):
    return sorted(set(grades), key=lambda g: GRADE_ORDER.index(g) if g in GRADE_ORDER else 99)


class Enrollment(object):
    """Resultado: año vigente y escuelas con sus grados. `schools` vacío = sin matrícula."""

    def __init__(self, schoolYear=None, schools=None):
        self.schoolYear = schoolYear
        self.schools = schools or []

    @property
    def is_enrolled(self):
        return bool(self.schools)

    @property
    def grades(self):
        return _sorted_grades(g for s in self.schools for g in s["grades"])

    def school(self, schoolId):
        """La escuela de la matrícula con ese id, o None (error 110 en la API)."""
        for s in self.schools:
            if s["id"] == _key(schoolId):
                return s
        return None

    def to_dict(self):
        return {
            "schoolYear": ({"id": str(self.schoolYear.id), "name": self.schoolYear.name}
                           if self.schoolYear else None),
            "schools": [dict(s, grades=list(s["grades"])) for s in self.schools],
            "grades": self.grades,
        }


class EnrollmentService(object):

    def current_school_year(self):
        """Año con status "1" sin borrar; solo cuenta el status, no las fechas."""
        years = list(SchoolYear.objects(status="1", isDeleted=False).order_by("-startDate"))
        if len(years) > 1:
            logger.warning("Vademecum: %s school years with status 1; using %s",
                           len(years), years[0].name)
        return years[0] if years else None

    def resolve(self, email, schoolYear=None):
        """Escuelas y grados del email en el año vigente (o el año dado)."""
        email = normalize_email(email)
        schoolYear = schoolYear or self.current_school_year()
        if not email or not schoolYear:
            return Enrollment(schoolYear)

        # 1. Escuelas activas que tienen al menos un docente vigente con ese email
        schoolsCursor = User._get_collection().find(
            {"_cls": SCHOOL_USER_CLS, "status": "1", "isDeleted": False,
             "teachers.email": email},
            {"name": 1, "code": 1, "teachers.id": 1, "teachers.email": 1,
             "teachers.status": 1, "teachers.isDeleted": 1},
            collation=CASE_INSENSITIVE)
        teacherIdsBySchool = {}
        schoolInfo = {}
        for school in schoolsCursor:
            ids = set(
                _key(t.get("id")) for t in school.get("teachers") or []
                if normalize_email(t.get("email")) == email
                and t.get("status") == "1" and not t.get("isDeleted"))
            if ids:
                teacherIdsBySchool[_key(school["_id"])] = ids
                schoolInfo[_key(school["_id"])] = school
        if not teacherIdsBySchool:
            return Enrollment(schoolYear)

        # 2. Solo escuelas con PecaProject vigente; los grados salen de sus secciones.
        # schoolYear se busca como ObjectId y como texto (hay proyectos antiguos con texto).
        pecas = PecaProject._get_collection().find(
            {"schoolYear": {"$in": [schoolYear.id, str(schoolYear.id)]}, "isDeleted": False,
             "project.school.id": {"$in": list(teacherIdsBySchool)}},
            {"project.school.id": 1, "school.sections.grade": 1,
             "school.sections.isDeleted": 1, "school.sections.teacher.id": 1})
        gradesBySchool = {}
        for peca in pecas:
            schoolId = _key(((peca.get("project") or {}).get("school") or {}).get("id"))
            teacherIds = teacherIdsBySchool.get(schoolId)
            if teacherIds is None:
                continue
            grades = gradesBySchool.setdefault(schoolId, [])
            for section in (peca.get("school") or {}).get("sections") or []:
                teacher = section.get("teacher") or {}
                if (not section.get("isDeleted") and section.get("grade")
                        and _key(teacher.get("id")) in teacherIds):
                    grades.append(section["grade"])

        schools = []
        for schoolId, grades in gradesBySchool.items():
            info = schoolInfo[schoolId]
            schools.append({"id": schoolId, "name": info.get("name"), "code": info.get("code"),
                            "grades": _sorted_grades(grades)})
        schools.sort(key=lambda s: (s["name"] or "").lower())
        return Enrollment(schoolYear, schools)

    def is_enrolled(self, email, schoolYear=None):
        return self.resolve(email, schoolYear).is_enrolled
