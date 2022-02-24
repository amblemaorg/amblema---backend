# app/services/peca_initial_workshop_service.py

from flask import current_app
from marshmallow import ValidationError
import os
import os.path
import copy

from app.models.peca_project_model import PecaProject
from app.models.peca_olympics_model import Olympics, Student
from app.schemas.peca_olympics_schema import OlympicsSchema, StudentSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser

class PecaGradeService():
    def get(self, pecaId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).only("school").first()

        if peca:
            grades = []
            for grade in sorted(peca.school.sections, key = lambda i: (i["grade"], i["name"])):
                if not grade.isDeleted:
                    exist = False
                    for ngrade in grades:
                        if ngrade["grade"] == grade.grade:
                            exist = True
                    if not exist:
                        grades.append({"grade": grade.grade, "name": name_grade(grade.grade)})
            return {"status": 200, "msg": "Grados", "data": grades}, 200
        else:
            return {"status": 400, "msg": "No existe el peca project"}, 200
    
    def post(self, pecaId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).only("project", "school", "lapse1", "lapse2", "lapse3").first()

        if peca:
            try:
                schema = StudentSchema()

                if not peca['lapse{}'.format(jsonData["lapse"])].olympics:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"olympics lapse: ": jsonData["lapse"]})
                if "grades" in jsonData:
                    for grade in jsonData['grades']:
                        sections = peca.school.sections.filter(
                            grade=grade, isDeleted=False)
                        if not sections:
                            raise RegisterNotFound(message="Record not found",
                                                status_code=404,
                                                payload={"grades: ": grade})
                        olympics = peca['lapse{}'.format(
                            jsonData["lapse"])].olympics
                        school = SchoolUser.objects(
                                    id=peca.project.school.id, isDeleted=False).first()
                                
                        for section in sections:
                            for student in section.students.filter(isDeleted=False):
                                isStudent = False
                                for enrolledStudent in olympics.students:
                                    if enrolledStudent.id == str(student.id):
                                        isStudent = True
                                if not isStudent:
                                    dataJson = {}
                                    dataJson['id'] = str(student.id)
                                    dataJson['name'] = student.firstName + \
                                        ' ' + student.lastName
                                    dataJson['section'] = {
                                        "id": str(section.id),
                                        "name": section.name,
                                        "grade": section.grade}

                                    data = schema.load(dataJson)

                                    student = Student()
                                    for field in data.keys():
                                        student[field] = data[field]

                                    olympics['students'].append(student)
                                    try:
                                        peca['lapse{}'.format(
                                            jsonData["lapse"])].olympics = olympics
                                        peca.save()
                                        peca.reload()
                                        school.olympicsSummary.inscribed += 1
                                        if student.status == "2":
                                            school.olympicsSummary.classified += 1
                                            if student.result:
                                                if student.result == "1":
                                                    school.olympicsSummary.medalsGold += 1
                                                elif student.result == "2":
                                                    school.olympicsSummary.medalsSilver += 1
                                                elif student.result == "3":
                                                    school.olympicsSummary.medalsBronze += 1
                                        school.save()
                                        school.reload()
                                    
                                    except Exception as e:
                                        return {'status': 0, 'message': str(e)},400
                        return {'status': 201, 'message': "Se registraron los estudiantes exitosamente"},201
                else:
                    return {'status': 400, 'message': "Debe enviar los grados a inscribir"},201
            except ValidationError as err:
                return err.normalized_messages(), 400
def name_grade(grade):
    if grade == "0":
        return "Preescolar"
    if grade in ("1", "3"):
        return grade+"er Grado"
    if grade == "2":
        return "2do Grado"
    if grade in ("4", "5", "6"):
        return grade+"to Grado"