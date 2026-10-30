# app/tests/integration/section_import_test.py


import unittest
import json
from datetime import datetime

from app import create_app

from app.models.school_year_model import SchoolYear
from app.models.school_user_model import SchoolUser
from app.models.peca_project_model import PecaProject
from app.models.peca_section_model import Section
from app.models.peca_student_model import Student, Diagnostic
from app.models.role_model import Role
from app.models.peca_setting_model import ReadingOlympics
from app.models.state_model import State, Municipality
from app.models.peca_project_model import Lapse
from app.models.peca_olympics_model import (
    Olympics, Student as OlympicsStudent, Section as OlympicsSection)


class SectionImportTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.dbName = self.db.get_db().name
        # Nunca correr estas pruebas fuera de la BD de pruebas
        self.assertTrue(self.dbName.endswith("_testing"), self.dbName)
        # Limpia antes y después (addCleanup corre aunque falle el setUp)
        self.db.connection.drop_database(self.dbName)
        self.addCleanup(self.db.connection.drop_database, self.dbName)
        self.client = self.app.test_client

        self.schoolYear = SchoolYear(
            name="Test",
            startDate="2020-02-14",
            endDate="2020-09-14")
        self.schoolYear.initFirstPecaSetting()
        # initFirstPecaSetting no crea readingOlympics y el pre_save del PECA lo exige
        for i in range(3):
            self.schoolYear.pecaSetting['lapse{}'.format(i + 1)].readingOlympics = ReadingOlympics()
        self.schoolYear.save()

        self.role = Role(name="School", devName="school")
        self.role.save()

        self.state = State(name="Lara")
        self.state.save()
        self.municipality = Municipality(state=self.state, name="Iribarren")
        self.municipality.save()

        self.school = SchoolUser(
            name="School",
            code="0002",
            phone="02343432323",
            schoolType="1",
            principalFirstName="Danel",
            principalLastName="Ortega",
            principalEmail="testemail@test.com",
            principalPhone="04244664646",
            schoolShift="1",
            email="someschoolemail@test.com",
            password="12345678",
            userType="3",
            role=self.role,
            addressState=self.state,
            addressMunicipality=self.municipality
        )
        self.school.save()

        self.section1A = Section(grade="1", name="A")
        self.section2B = Section(grade="2", name="B")
        self.sectionDeleted = Section(grade="3", name="C", isDeleted=True)

        self.pecaProject = PecaProject(
            schoolYear=self.schoolYear,
            schoolYearName=self.schoolYear.name,
            school={
                "name": self.school.name,
                "code": self.school.code,
                "addressState": str(self.state.id),
                "addressMunicipality": str(self.municipality.id),
                "principalFirstName": self.school.principalFirstName,
                "principalLastName": self.school.principalLastName,
                "principalEmail": self.school.principalEmail,
                "principalPhone": self.school.principalPhone,
                "sections": [self.section1A, self.section2B, self.sectionDeleted]
            }
        )
        self.pecaProject.save()

    def post(self, body):
        return self.client().post(
            '/section/load/{}'.format(str(self.pecaProject.id)),
            data=json.dumps(body),
            content_type='application/json')

    def student(self, name, lastName, cardId, section=None, row=None):
        data = {
            "nombre": name,
            "apellido": lastName,
            "tipo_de_documento": "1",
            "documento_de_identidad": cardId,
            "fecha_de_nacimiento": "15-03-2015",
            "genero": "F",
        }
        if section is not None:
            data["section"] = section
        if row is not None:
            data["fila"] = row
        return data

    def activeStudents(self, peca, sectionId):
        section = peca.school.sections.filter(id=sectionId).first()
        return [s for s in section.students if not s.isDeleted]

    def test_import_single_section(self):
        res = self.post({
            "action": "import",
            "section": str(self.section1A.id),
            "students": [self.student("ana", "perez", "V-30111222")]
        })
        self.assertEqual(res.status_code, 201)

        peca = PecaProject.objects.get(id=self.pecaProject.id)
        students = self.activeStudents(peca, self.section1A.id)
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].cardId, "30111222")
        self.assertEqual(peca.school.nStudents, 1)

        school = SchoolUser.objects.get(id=self.school.id)
        self.assertEqual(len(school.students), 1)
        self.assertEqual(str(school.students[0].sections[0].id), str(self.section1A.id))

    def test_import_multiple_sections(self):
        res = self.post({
            "action": "import_multiple",
            "students": [
                self.student("Ana", "Perez", "30111222", str(self.section1A.id), 2),
                self.student("Luis", "Gomez", "30111333", str(self.section2B.id), 3),
                self.student("Maria", "Rojas", "30111444", str(self.section2B.id), 4),
            ]
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(json.loads(res.data.decode())["sections"], 2)

        peca = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(
            [s.cardId for s in self.activeStudents(peca, self.section1A.id)], ["30111222"])
        self.assertEqual(
            sorted(s.cardId for s in self.activeStudents(peca, self.section2B.id)),
            ["30111333", "30111444"])
        self.assertEqual(peca.school.nStudents, 3)

        school = SchoolUser.objects.get(id=self.school.id)
        self.assertEqual(school.nStudents, 3)
        sectionsByCard = dict(
            (s.cardId, str(s.sections[0].id)) for s in school.students)
        self.assertEqual(sectionsByCard["30111333"], str(self.section2B.id))

        schoolYear = SchoolYear.objects.get(id=self.schoolYear.id)
        self.assertEqual(schoolYear.nStudents, 3)

    def test_import_multiple_reuses_existing_student(self):
        self.post({
            "action": "import",
            "section": str(self.section1A.id),
            "students": [self.student("Ana", "Perez", "30111222")]
        })
        res = self.post({
            "action": "import_multiple",
            "students": [
                self.student("Ana Maria", "Perez", "30111222", str(self.section1A.id)),
                self.student("Luis", "Gomez", "30111333", str(self.section2B.id)),
            ]
        })
        self.assertEqual(res.status_code, 201)

        peca = PecaProject.objects.get(id=self.pecaProject.id)
        students1A = self.activeStudents(peca, self.section1A.id)
        self.assertEqual(len(students1A), 1)
        self.assertEqual(students1A[0].firstName, "Ana Maria")
        self.assertEqual(len(SchoolUser.objects.get(id=self.school.id).students), 2)

    def test_import_multiple_rejects_unregistered_sections(self):
        res = self.post({
            "action": "import_multiple",
            "students": [
                self.student("Ana", "Perez", "30111222", str(self.section1A.id), 2),
                self.student("Luis", "Gomez", "30111333", str(self.sectionDeleted.id), 3),
                self.student("Maria", "Rojas", "30111444", None, 4),
            ]
        })
        self.assertEqual(res.status_code, 400)
        body = json.loads(res.data.decode())
        self.assertEqual(len(body["errors"]), 2)
        self.assertTrue(body["errors"][0].startswith("Fila 3"))

        # Todo o nada: no se guarda ningún estudiante
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(len(self.activeStudents(peca, self.section1A.id)), 0)
        self.assertEqual(len(SchoolUser.objects.get(id=self.school.id).students), 0)

    def test_import_multiple_without_students(self):
        res = self.post({"action": "import_multiple", "students": []})
        self.assertEqual(res.status_code, 400)

    def test_import_multiple_moves_student_to_new_section(self):
        self.post({
            "action": "import",
            "section": str(self.section1A.id),
            "students": [self.student("Ana", "Perez", "30111222")]
        })
        # Diagnóstico y olimpíada registrados en la sección anterior (1A)
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        previous = self.activeStudents(peca, self.section1A.id)[0]
        studentId = str(previous.id)
        previous.lapse1.wordsPerMin = 50
        if peca.lapse1 is None:
            peca.lapse1 = Lapse()
        peca.lapse1.olympics = Olympics(students=[OlympicsStudent(
            id=studentId, name="Ana Perez",
            section=OlympicsSection(id=str(self.section1A.id), name="A", grade="1"))])
        peca.save()

        res = self.post({
            "action": "import_multiple",
            "students": [self.student("Ana", "Perez", "30111222", str(self.section2B.id))]
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(json.loads(res.data.decode())["moved"], 1)

        peca = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(len(self.activeStudents(peca, self.section1A.id)), 0)
        moved = self.activeStudents(peca, self.section2B.id)
        self.assertEqual([str(s.id) for s in moved], [studentId])
        self.assertEqual(moved[0].lapse1.wordsPerMin, 50)
        # Índice recalculado con la meta de 2do grado (wordsPerMin=1 en el setUp)
        self.assertEqual(float(moved[0].lapse1.wordsPerMinIndex), 5000.0)
        self.assertEqual(peca.lapse1.olympics.students[0].section.id, str(self.section2B.id))
        self.assertEqual(peca.school.nStudents, 1)

        school = SchoolUser.objects.get(id=self.school.id)
        self.assertEqual(len(school.students), 1)
        self.assertEqual(
            [str(s.id) for s in school.students[0].sections], [str(self.section2B.id)])

    def test_move_back_keeps_latest_diagnostics_and_olympics_result(self):
        # 1A -> 2B -> 1A: la copia de 1A se revive con datos viejos; deben ganar los de 2B
        importTo = lambda section: self.post({
            "action": "import_multiple",
            "students": [self.student("Ana", "Perez", "30111222", str(section.id))]
        })
        importTo(self.section1A)
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        student = self.activeStudents(peca, self.section1A.id)[0]
        studentId = str(student.id)
        student.lapse1.wordsPerMin = 10
        student.lapse1.readingDate = datetime(2026, 1, 10)
        if peca.lapse1 is None:
            peca.lapse1 = Lapse()
        peca.lapse1.olympics = Olympics(students=[OlympicsStudent(
            id=studentId, name="Ana Perez", result="1",
            section=OlympicsSection(id=str(self.section1A.id), name="A", grade="1"))])
        peca.save()

        importTo(self.section2B)
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        student = self.activeStudents(peca, self.section2B.id)[0]
        self.assertEqual(student.lapse1.wordsPerMin, 10)
        # Nuevos diagnósticos en 2B, incluido un 0 (valor válido)
        student.lapse1.wordsPerMin = 40
        student.lapse1.readingDate = datetime(2026, 3, 1)
        student.lapse2.multiplicationsPerMin = 0
        student.lapse2.mathDate = datetime(2026, 3, 1)
        peca.save()

        res = importTo(self.section1A)
        self.assertEqual(json.loads(res.data.decode())["moved"], 1)
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(len(self.activeStudents(peca, self.section2B.id)), 0)
        back = self.activeStudents(peca, self.section1A.id)
        self.assertEqual([str(s.id) for s in back], [studentId])
        self.assertEqual(back[0].lapse1.wordsPerMin, 40)
        self.assertEqual(back[0].lapse2.multiplicationsPerMin, 0)
        enrolled = peca.lapse1.olympics.students[0]
        self.assertEqual(enrolled.section.id, str(self.section1A.id))
        self.assertEqual(enrolled.result, "1")

    def test_move_merges_partial_diagnostics(self):
        # Origen con lapso 1 y destino con lapso 2: se conservan ambos
        self.post({
            "action": "import",
            "section": str(self.section1A.id),
            "students": [self.student("Ana", "Perez", "30111222")]
        })
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        previous = self.activeStudents(peca, self.section1A.id)[0]
        previous.lapse1.operationsPerMin = 5
        target = self.section2B
        section = peca.school.sections.filter(id=target.id).first()
        stale = Student(id=previous.id, firstName="Ana", lastName="Perez", cardId="30111222",
                        cardType="1", birthdate=previous.birthdate, gender="1", isDeleted=True,
                        lapse1=Diagnostic(), lapse2=Diagnostic(wordsPerMin=30), lapse3=Diagnostic())
        section.students.append(stale)
        peca.save()

        self.post({
            "action": "import_multiple",
            "students": [self.student("Ana", "Perez", "30111222", str(target.id))]
        })
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        moved = self.activeStudents(peca, target.id)
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0].lapse1.operationsPerMin, 5)
        self.assertEqual(moved[0].lapse2.wordsPerMin, 30)

    def test_import_single_moves_student_to_new_section(self):
        self.post({
            "action": "import",
            "section": str(self.section1A.id),
            "students": [self.student("Ana", "Perez", "30111222")]
        })
        res = self.post({
            "action": "import",
            "section": str(self.section2B.id),
            "students": [self.student("Ana", "Perez", "30111222")]
        })
        self.assertEqual(json.loads(res.data.decode())["moved"], 1)
        peca = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(len(self.activeStudents(peca, self.section1A.id)), 0)
        self.assertEqual(len(self.activeStudents(peca, self.section2B.id)), 1)
        self.assertEqual(peca.school.nStudents, 1)

    def test_reimport_same_file_does_not_duplicate(self):
        # Incluye un estudiante sin cédula: se empareja por nombre y fecha de nacimiento
        rows = [
            self.student("Ana", "Perez", "30111222", str(self.section1A.id)),
            self.student("Luis", "Gomez", "", str(self.section2B.id)),
            self.student("Maria", "Rojas", "30111444", str(self.section2B.id)),
        ]
        for _ in range(2):
            res = self.post({"action": "import_multiple", "students": [dict(r) for r in rows]})
            self.assertEqual(res.status_code, 201)
        for _ in range(2):
            res = self.post({
                "action": "import",
                "section": str(self.section1A.id),
                "students": [self.student("Ana", "Perez", "30111222")]
            })
            self.assertEqual(json.loads(res.data.decode())["moved"], 0)

        peca = PecaProject.objects.get(id=self.pecaProject.id)
        self.assertEqual(len(self.activeStudents(peca, self.section1A.id)), 1)
        self.assertEqual(len(self.activeStudents(peca, self.section2B.id)), 2)
        self.assertEqual(peca.school.nStudents, 3)
        school = SchoolUser.objects.get(id=self.school.id)
        self.assertEqual(len(school.students), 3)
        self.assertEqual(school.nStudents, 3)


if __name__ == "__main__":
    unittest.main()
