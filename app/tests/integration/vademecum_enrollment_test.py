# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_enrollment_test.py
"""Matrícula vigente (API-02) con los casos C1-C8 de GES-04.

Escuelas y proyectos PECA se insertan con la forma real de la BD (ids de sección como texto,
emails sin normalizar) para no depender de los servicios de PECA.
"""

import unittest
from datetime import datetime

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import create_school_year


def teacher(email, status="1", isDeleted=False, firstName="Ana"):
    return {"id": ObjectId(), "firstName": firstName, "lastName": "Docente", "email": email,
            "status": status, "isDeleted": isDeleted}


def section(grade, teacherRow=None, isDeleted=False):
    data = {"id": ObjectId(), "grade": grade, "name": "A", "isDeleted": isDeleted}
    if teacherRow is not None:
        data["teacher"] = {"id": str(teacherRow["id"]), "firstName": teacherRow["firstName"],
                           "lastName": teacherRow["lastName"]}
    return data


class VademecumEnrollmentTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.models.user_model import User
        from app.models.peca_project_model import PecaProject
        self.users = User._get_collection()
        self.pecas = PecaProject._get_collection()
        self.year = create_school_year(name="2026 - 2027", start=datetime(2026, 10, 14),
                                       end=datetime(2027, 8, 31), status="1")
        self.oldYear = create_school_year(name="2025 - 2026", start=datetime(2025, 9, 29),
                                          end=datetime(2026, 10, 14), status="2")

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    def school(self, name, teachers, sections=(), status="1", isDeleted=False, year=None,
               pecaDeleted=False, withPeca=True, yearAsText=False):
        schoolId = self.users.insert_one({
            "_cls": "User.SchoolUser", "name": name, "code": name[:4].upper(),
            "email": "{}@escuela.test".format(name.lower().replace(" ", "")),
            "status": status, "isDeleted": isDeleted, "teachers": list(teachers),
        }).inserted_id
        if withPeca:
            yearId = (year or self.year).id
            self.pecas.insert_one({
                "schoolYear": str(yearId) if yearAsText else yearId,
                "project": {"id": str(ObjectId()),
                            "school": {"id": str(schoolId), "name": name, "code": "X"}},
                "school": {"name": name, "sections": list(sections)},
                "isDeleted": pecaDeleted,
            })
        return str(schoolId)

    def resolve(self, email):
        from app.services.vademecum.enrollment_service import EnrollmentService
        return EnrollmentService().resolve(email)

    # --- Regla básica ---

    def test_active_teacher_gets_school_and_grades_from_sections(self):
        ana = teacher("ana@test.com")
        schoolId = self.school("Escuela Uno", [ana], [section("3", ana), section("1", ana)])
        enrollment = self.resolve("ana@test.com")
        self.assertTrue(enrollment.is_enrolled)
        self.assertEqual(enrollment.to_dict(), {
            "schoolYear": {"id": str(self.year.id), "name": "2026 - 2027"},
            "schools": [{"id": schoolId, "name": "Escuela Uno", "code": "ESCU",
                         "grades": ["1", "3"]}],
            "grades": ["1", "3"],
        })

    def test_unknown_email_is_not_enrolled(self):
        self.school("Escuela Uno", [teacher("ana@test.com")])
        enrollment = self.resolve("otra@test.com")
        self.assertFalse(enrollment.is_enrolled)
        self.assertEqual(enrollment.to_dict()["schools"], [])

    def test_without_current_school_year_nobody_is_enrolled(self):
        self.school("Escuela Uno", [teacher("ana@test.com")])
        self.year.status = "2"
        self.year.save()
        enrollment = self.resolve("ana@test.com")
        self.assertFalse(enrollment.is_enrolled)
        self.assertIsNone(enrollment.to_dict()["schoolYear"])

    def test_school_year_dates_do_not_matter(self):
        # El año vigente ya venció por fecha, pero su status sigue en "1"
        self.year.endDate = datetime(2020, 1, 1)
        self.year.save()
        self.school("Escuela Uno", [teacher("ana@test.com")])
        self.assertTrue(self.resolve("ana@test.com").is_enrolled)

    def test_only_projects_of_the_current_year_count(self):
        ana = teacher("ana@test.com")
        self.school("Escuela Vieja", [ana], [section("2", ana)], year=self.oldYear)
        self.assertFalse(self.resolve("ana@test.com").is_enrolled)

    def test_deleted_peca_project_does_not_count(self):
        self.school("Escuela Uno", [teacher("ana@test.com")], pecaDeleted=True)
        self.assertFalse(self.resolve("ana@test.com").is_enrolled)

    def test_school_without_peca_project_does_not_count(self):
        self.school("Escuela Uno", [teacher("ana@test.com")], withPeca=False)
        self.assertFalse(self.resolve("ana@test.com").is_enrolled)

    def test_peca_project_with_school_year_stored_as_text_counts(self):
        # Riesgo de GES-04: hay proyectos con schoolYear guardado como texto
        self.school("Escuela Uno", [teacher("ana@test.com")], yearAsText=True)
        self.assertTrue(self.resolve("ana@test.com").is_enrolled)

    def test_grades_are_not_stored_in_the_teacher_account(self):
        from app.models.vademecum import VademecumTeacherAccount
        ana = teacher("ana@test.com")
        self.school("Escuela Uno", [ana], [section("4", ana)])
        self.resolve("ana@test.com")
        self.assertEqual(VademecumTeacherAccount.objects.count(), 0)
        self.assertNotIn("grades", VademecumTeacherAccount._fields)
        self.assertNotIn("school", VademecumTeacherAccount._fields)

    # --- Casos de GES-04 ---

    def test_c1_duplicated_rows_in_same_school_merge_grades(self):
        first, second = teacher("rep@test.com"), teacher("rep@test.com")
        schoolId = self.school("Escuela Uno", [first, second],
                               [section("3", first), section("4", first)])
        enrollment = self.resolve("rep@test.com")
        self.assertEqual(len(enrollment.schools), 1)
        self.assertEqual(enrollment.school(schoolId)["grades"], ["3", "4"])

    def test_c2_shared_email_with_different_names_merges_grades(self):
        luis = teacher("compartido@test.com", firstName="Luis")
        maria = teacher("compartido@test.com", firstName="María")
        self.school("Escuela Uno", [luis, maria], [section("2", luis), section("1", maria)])
        self.assertEqual(self.resolve("compartido@test.com").grades, ["1", "2"])

    def test_c3_teacher_in_two_schools_lists_each_school_with_its_grades(self):
        rowA, rowB = teacher("dos@test.com"), teacher("dos@test.com")
        schoolA = self.school("Escuela A", [rowA], [section("0", rowA)])
        schoolB = self.school("Escuela B", [rowB], [section("5", rowB)])
        enrollment = self.resolve("dos@test.com")
        self.assertEqual([s["id"] for s in enrollment.schools], [schoolA, schoolB])
        self.assertEqual(enrollment.school(schoolA)["grades"], ["0"])
        self.assertEqual(enrollment.school(schoolB)["grades"], ["5"])
        self.assertEqual(enrollment.grades, ["0", "5"])
        self.assertIsNone(enrollment.school(str(ObjectId())))

    def test_c4_teacher_without_section_is_enrolled_without_grades(self):
        schoolId = self.school("Escuela Uno", [teacher("sin@test.com")])
        enrollment = self.resolve("sin@test.com")
        self.assertTrue(enrollment.is_enrolled)
        self.assertEqual(enrollment.school(schoolId)["grades"], [])
        self.assertEqual(enrollment.grades, [])

    def test_c5_sections_of_inactive_rows_and_deleted_sections_add_no_grades(self):
        active = teacher("mix@test.com")
        inactive = teacher("mix@test.com", status="2")
        self.school("Escuela Uno", [active, inactive],
                    [section("1", active), section("2", inactive),
                     section("3", active, isDeleted=True), section("6")])
        self.assertEqual(self.resolve("mix@test.com").grades, ["1"])

    def test_c6_email_is_compared_without_case_or_spaces(self):
        self.school("Escuela Uno", [teacher("Ana.Perez@Gmail.com")])
        self.assertTrue(self.resolve("  ana.perez@gmail.com ").is_enrolled)
        self.assertTrue(self.resolve("ANA.PEREZ@GMAIL.COM").is_enrolled)

    def test_c7_inactive_or_deleted_teacher_is_not_enrolled(self):
        self.school("Escuela Uno", [teacher("inactivo@test.com", status="2"),
                                    teacher("borrado@test.com", isDeleted=True)])
        self.assertFalse(self.resolve("inactivo@test.com").is_enrolled)
        self.assertFalse(self.resolve("borrado@test.com").is_enrolled)

    def test_c8_inactive_or_deleted_school_does_not_count(self):
        self.school("Escuela Inactiva", [teacher("ana@test.com")], status="2")
        self.school("Escuela Borrada", [teacher("ana@test.com")], isDeleted=True)
        self.assertFalse(self.resolve("ana@test.com").is_enrolled)

    # --- Índice ---

    def test_teacher_email_index_is_case_insensitive_and_used(self):
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes
        from app.services.vademecum.enrollment_service import (
            CASE_INSENSITIVE, TEACHER_EMAIL_INDEX)
        ensure_vademecum_indexes()
        ensure_vademecum_indexes()  # idempotente
        index = self.users.index_information()[TEACHER_EMAIL_INDEX]
        self.assertEqual(index["key"], [("teachers.email", 1)])
        self.assertEqual(index["collation"]["strength"], 2)
        plan = self.users.find({"teachers.email": "x@test.com"},
                               collation=CASE_INSENSITIVE).explain()
        self.assertIn(TEACHER_EMAIL_INDEX, str(plan["queryPlanner"]["winningPlan"]))


if __name__ == "__main__":
    unittest.main()
