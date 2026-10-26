# app/tests/integration/promote_students_test.py


import unittest
import json
from datetime import datetime

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.models.peca_project_model import PecaProject
from app.models.peca_section_model import Section
from app.models.peca_student_model import Student, StudentClass, SectionClass, Diagnostic
from app.models.project_model import Project
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear


class PromoteStudentsTest(unittest.TestCase):
    """Promoción de estudiantes del PECA del año anterior al año activo."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        seed_base()
        state, municipality = create_location()

        # Año anterior con su PECA y una sección con tres estudiantes
        self.previousYear = create_school_year(
            name="2024 - 2025", start=datetime(2024, 9, 1), end=datetime(2025, 7, 31))
        self.school = create_school(state, municipality, code="OD0001")
        self.project = Project(
            coordinator=create_coordinator(state, municipality),
            sponsor=create_sponsor(state, municipality),
            school=self.school, phase="2")
        self.project.save()
        self.project.createPeca()
        self.previousPeca = PecaProject.objects(schoolYear=self.previousYear.id).first()

        self.students = [
            Student(firstName="José", lastName="Ñúñez", cardId="1", cardType="1", gender="1",
                    birthdate=datetime(2015, 1, 1)),
            Student(firstName="Ana", lastName="Álvarez", cardId="2", cardType="1", gender="2",
                    birthdate=datetime(2015, 2, 1)),
            Student(firstName="Luis", lastName="Nava", cardId="3", cardType="1", gender="1",
                    birthdate=datetime(2015, 3, 1)),
        ]
        self.previousSection = Section(grade="1", name="A", students=self.students)
        self.previousPeca.school.sections = [self.previousSection]
        self.previousPeca.save()
        previousSectionRef = SectionClass(id=self.previousSection.id, grade="1", name="A",
                                          schoolYear=self.previousYear)
        self.school.students = [
            StudentClass(id=s.id, firstName=s.firstName, lastName=s.lastName, cardId=s.cardId,
                         cardType=s.cardType, gender=s.gender, birthdate=s.birthdate,
                         sections=[previousSectionRef])
            for s in self.students]
        self.school.save()

        # Cambio de año: el anterior queda cerrado y el PECA nuevo tiene una sección vacía
        SchoolYear.objects(id=self.previousYear.id).update(status="2")
        self.currentYear = create_school_year(
            name="2025 - 2026", start=datetime(2025, 9, 1), end=datetime(2026, 7, 31))
        self.project.reload()
        self.project.createPeca()
        self.currentPeca = PecaProject.objects(schoolYear=self.currentYear.id).first()
        self.currentSection = Section(grade="2", name="A")
        self.currentPeca.school.sections = [self.currentSection]
        self.currentPeca.save()

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    def promote(self, studentIds, sectionId=None):
        return self.client().post(
            '/promote/students/OD0001',
            data=json.dumps({
                "id_section_current": str(sectionId or self.currentSection.id),
                "students": [{"id": str(i)} for i in studentIds]}),
            content_type='application/json')

    def test_sections_of_both_years(self):
        res = self.client().get('/init/promote/students/OD0001')
        body = self.json(res)
        self.assertEqual(body['section_previus'], [
            {"id": str(self.previousSection.id), "grade": "1", "name": "A"}])
        self.assertEqual(body['section_current'], [
            {"id": str(self.currentSection.id), "grade": "2", "name": "A"}])

    def test_list_sorted_by_last_name_ignoring_accents(self):
        res = self.client().get('/promote/students/OD0001/{}'.format(self.previousSection.id))
        self.assertEqual(res.status_code, 200)
        # Á se ordena como A y Ñ va después de N
        self.assertEqual([s['lastName'] for s in self.json(res)['students']],
                         ["Álvarez", "Nava", "Ñúñez"])

    def test_promote_moves_students_and_updates_counts(self):
        res = self.promote([self.students[0].id, self.students[1].id])
        self.assertEqual(res.status_code, 201)

        self.currentPeca.reload()
        promoted = self.currentPeca.school.sections[0].students
        self.assertEqual(sorted(s.lastName for s in promoted), ["Álvarez", "Ñúñez"])
        self.assertTrue(all(s.lapse1 is not None for s in promoted))
        self.assertEqual(self.currentPeca.school.nStudents, 2)

        self.school.reload()
        enrolled = [s for s in self.school.students
                    if any(sec.schoolYear.id == self.currentYear.id for sec in s.sections)]
        self.assertEqual(len(enrolled), 2)
        self.assertEqual(self.school.nStudents, 2)
        self.currentYear.reload()
        self.assertEqual(self.currentYear.nStudents, 2)

        # Ya inscritos en el año actual: no aparecen en la lista ni se duplican
        res = self.client().get('/promote/students/OD0001/{}'.format(self.previousSection.id))
        self.assertEqual([s['lastName'] for s in self.json(res)['students']], ["Nava"])
        self.promote([self.students[0].id])
        self.currentPeca.reload()
        self.assertEqual(len(self.currentPeca.school.sections[0].students), 2)

    def test_inactive_students_are_not_promoted(self):
        school = SchoolUser.objects(id=self.school.id).first()
        school.students[2].isDeleted = True
        school.save()
        self.promote([self.students[2].id])
        self.currentPeca.reload()
        self.assertEqual(self.currentPeca.school.sections[0].students, [])

    def test_promote_to_unknown_section(self):
        res = self.promote([self.students[0].id], sectionId="5f0000000000000000000000")
        self.assertEqual(self.json(res)['msg'], "La sección no existe")


if __name__ == "__main__":
    unittest.main()
