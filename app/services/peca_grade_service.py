# app/services/peca_grade_service.py

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
                olympicsType = jsonData.get('olympicsType', 'math')

                if olympicsType == 'reading':
                    olympics_lapse = peca['lapse{}'.format(jsonData["lapse"])].readingOlympics
                else:
                    olympics_lapse = peca['lapse{}'.format(jsonData["lapse"])].olympics

                if not olympics_lapse:
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
                        
                        olympics = olympics_lapse
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
                            if olympicsType == 'reading':
                                peca['lapse{}'.format(jsonData["lapse"])].readingOlympics = olympics
                            else:
                                peca['lapse{}'.format(jsonData["lapse"])].olympics = olympics
                            peca.save()
                            peca.reload()
                            
                        except Exception as e:
                            return {'status': 0, 'message': str(e)},400
                        
                        if olympicsType == 'reading':
                            olympics_data = peca['lapse{}'.format(jsonData["lapse"])].readingOlympics
                        else:
                            olympics_data = peca['lapse{}'.format(jsonData["lapse"])].olympics

                        classified = olympics_data.students.filter(status="3")
                        classifiedNational = olympics_data.students.filter(statusNational="2")
                        
                        if olympicsType == 'reading':
                            school.olympicsReadingSummary.inscribed = len(olympics_data.students)
                            school.olympicsReadingSummary.participant = len([s for s in olympics_data.students if s.status in ["2", "3"]])
                            school.olympicsReadingSummary.classified = len(olympics_data.students.filter(status="3"))
                            
                            school.olympicsReadingSummary.participantRegional = len([s for s in olympics_data.students if s.statusRegional in ["1", "2"]])
                            school.olympicsReadingSummary.classifiedRegional = len(olympics_data.students.filter(statusRegional="2"))
                            
                            school.olympicsReadingSummary.medalsGold = len(olympics_data.students.filter(result="1", statusRegional="2"))
                            school.olympicsReadingSummary.medalsSilver = len(olympics_data.students.filter(result="2", statusRegional="2"))
                            school.olympicsReadingSummary.medalsBronze = len(olympics_data.students.filter(result="3", statusRegional="2"))
                            
                            school.olympicsReadingSummary.inscribedNational = len(olympics_data.students.filter(result="1"))
                            school.olympicsReadingSummary.classifiedNational = len(classifiedNational)
                            school.olympicsReadingSummary.medalsGoldNational = len(olympics_data.students.filter(resultNational="1", statusNational="2"))
                            school.olympicsReadingSummary.medalsSilverNational = len(olympics_data.students.filter(resultNational="2", statusNational="2"))
                            school.olympicsReadingSummary.medalsBronzeNational = len(olympics_data.students.filter(resultNational="3", statusNational="2"))
                        else:
                            school.olympicsSummary.inscribed = len(olympics_data.students)
                            school.olympicsSummary.participant = len([s for s in olympics_data.students if s.status in ["2", "3"]])
                            school.olympicsSummary.classified = len(olympics_data.students.filter(status="3"))
                            
                            school.olympicsSummary.participantRegional = len([s for s in olympics_data.students if s.statusRegional in ["1", "2"]])
                            school.olympicsSummary.classifiedRegional = len(olympics_data.students.filter(statusRegional="2"))
                            
                            school.olympicsSummary.medalsGold = len(olympics_data.students.filter(result="1", statusRegional="2"))
                            school.olympicsSummary.medalsSilver = len(olympics_data.students.filter(result="2", statusRegional="2"))
                            school.olympicsSummary.medalsBronze = len(olympics_data.students.filter(result="3", statusRegional="2"))

                            school.olympicsSummary.inscribedNational = len(olympics_data.students.filter(result="1"))
                            school.olympicsSummary.classifiedNational = len(classifiedNational)
                            school.olympicsSummary.medalsGoldNational = len(olympics_data.students.filter(resultNational="1", statusNational="2"))
                            school.olympicsSummary.medalsSilverNational = len(olympics_data.students.filter(resultNational="2", statusNational="2"))
                            school.olympicsSummary.medalsBronzeNational = len(olympics_data.students.filter(resultNational="3", statusNational="2"))
                
                        school.save()
                        school.reload()
                                    
                    return {'status': 201, 'message': "Se registraron los estudiantes exitosamente"},201
                else:
                    return {'status': 400, 'message': "Debe enviar los grados a inscribir"},201
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            return {'status': 400, 'message': "El proyecto peca no existe"},201
                
    def deleteStudent(self, pecaId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).only("project", "school", "lapse1", "lapse2", "lapse3").first()

        if peca:
            try:
                schema = StudentSchema()
                olympicsType = jsonData.get('olympicsType', 'math')

                if olympicsType == 'reading':
                    olympics_lapse = peca['lapse{}'.format(jsonData["lapse"])].readingOlympics
                else:
                    olympics_lapse = peca['lapse{}'.format(jsonData["lapse"])].olympics

                if not olympics_lapse:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"olympics lapse: ": jsonData["lapse"]})
                
                # olympics = olympics_lapse # Use this reference
                # Need to be careful with reference updates in MongoEngine, easier to modify the list in place if possible
                
                for studentId in jsonData["students"]:
                    found = False
                    # We need to iterate over the correct list
                    students_list = olympics_lapse.students
                    for student in students_list:
                        if student.id == studentId:
                            found = True
                            students_list.remove(student)
                            break
                
                try:
                    peca.save()
                    peca.reload()
                except Exception as e:
                     return {'status': 0, 'message': str(e)},400

                if olympicsType == 'reading':
                     olympics_data = peca['lapse{}'.format(jsonData["lapse"])].readingOlympics
                else:
                     olympics_data = peca['lapse{}'.format(jsonData["lapse"])].olympics
                
                classified = olympics_data.students.filter(status="3")
                classifiedNational = olympics_data.students.filter(statusNational="2")

                school = SchoolUser.objects(
                    id=peca.project.school.id, isDeleted=False).first()
                
                if olympicsType == 'reading':
                    school.olympicsReadingSummary.inscribed = len(olympics_data.students)
                    school.olympicsReadingSummary.participant = len([s for s in olympics_data.students if s.status in ["2", "3"]])
                    school.olympicsReadingSummary.classified = len(olympics_data.students.filter(status="3"))
                    
                    school.olympicsReadingSummary.participantRegional = len([s for s in olympics_data.students if s.statusRegional in ["1", "2"]])
                    school.olympicsReadingSummary.classifiedRegional = len(olympics_data.students.filter(statusRegional="2"))
                    
                    school.olympicsReadingSummary.medalsGold = len(olympics_data.students.filter(result="1", statusRegional="2"))
                    school.olympicsReadingSummary.medalsSilver = len(olympics_data.students.filter(result="2", statusRegional="2"))
                    school.olympicsReadingSummary.medalsBronze = len(olympics_data.students.filter(result="3", statusRegional="2"))
                    
                    school.olympicsReadingSummary.inscribedNational = len(olympics_data.students.filter(result="1"))
                    school.olympicsReadingSummary.classifiedNational = len(classifiedNational)
                    school.olympicsReadingSummary.medalsGoldNational = len(olympics_data.students.filter(resultNational="1", statusNational="2"))
                    school.olympicsReadingSummary.medalsSilverNational = len(olympics_data.students.filter(resultNational="2", statusNational="2"))
                    school.olympicsReadingSummary.medalsBronzeNational = len(olympics_data.students.filter(resultNational="3", statusNational="2"))
                    school.save()

                elif olympicsType == 'math':
                    school.olympicsSummary.inscribed = len(olympics_data.students)
                    school.olympicsSummary.participant = len([s for s in olympics_data.students if s.status in ["2", "3"]])
                    school.olympicsSummary.classified = len(olympics_data.students.filter(status="3"))
                    
                    school.olympicsSummary.participantRegional = len([s for s in olympics_data.students if s.statusRegional in ["1", "2"]])
                    school.olympicsSummary.classifiedRegional = len(olympics_data.students.filter(statusRegional="2"))
                    
                    school.olympicsSummary.medalsGold = len(olympics_data.students.filter(result="1", statusRegional="2"))
                    school.olympicsSummary.medalsSilver = len(olympics_data.students.filter(result="2", statusRegional="2"))
                    school.olympicsSummary.medalsBronze = len(olympics_data.students.filter(result="3", statusRegional="2"))

                    school.olympicsSummary.inscribedNational = len(olympics_data.students.filter(result="1"))
                    school.olympicsSummary.classifiedNational = len(classifiedNational)
                    school.olympicsSummary.medalsGoldNational = len(olympics_data.students.filter(resultNational="1", statusNational="2"))
                    school.olympicsSummary.medalsSilverNational = len(olympics_data.students.filter(resultNational="2", statusNational="2"))
                    school.olympicsSummary.medalsBronzeNational = len(olympics_data.students.filter(resultNational="3", statusNational="2"))
                    school.save()

                return {"status": 201, "message": "Se han eliminado los estudiantes con éxito"}, 201
                
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            return {'status': 400, 'message': "El proyecto peca no existe"},201
    
    def changeStatus(self, pecaId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).only("project", "school", "lapse1", "lapse2", "lapse3").first()

        if peca:
            try:
                schema = StudentSchema()
                olympicsType = jsonData.get('olympicsType', 'math')

                if olympicsType == 'reading':
                    olympics_lapse = peca['lapse{}'.format(jsonData["lapse"])].readingOlympics
                else:
                    olympics_lapse = peca['lapse{}'.format(jsonData["lapse"])].olympics

                if not olympics_lapse:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"olympics lapse: ": jsonData["lapse"]})
                
                for studentId in jsonData["students"]:
                    for student in olympics_lapse.students:
                        if student.id == studentId:
                            student.status = jsonData["status"]
                            break
                
                peca.save()
                peca.reload()
                
                if olympicsType == 'reading':
                     olympics_data = peca['lapse{}'.format(jsonData["lapse"])].readingOlympics
                else:
                     olympics_data = peca['lapse{}'.format(jsonData["lapse"])].olympics

                classified = olympics_data.students.filter(status="3")
                classifiedNational = olympics_data.students.filter(statusNational="2")

                school = SchoolUser.objects(
                    id=peca.project.school.id, isDeleted=False).first()
                
                if olympicsType == 'reading':
                    school.olympicsReadingSummary.inscribed = len(olympics_data.students)
                    school.olympicsReadingSummary.participant = len([s for s in olympics_data.students if s.status in ["2", "3"]])
                    school.olympicsReadingSummary.classified = len(olympics_data.students.filter(status="3"))
                    
                    school.olympicsReadingSummary.participantRegional = len([s for s in olympics_data.students if s.statusRegional in ["1", "2"]])
                    school.olympicsReadingSummary.classifiedRegional = len(olympics_data.students.filter(statusRegional="2"))
                    
                    school.olympicsReadingSummary.medalsGold = len(olympics_data.students.filter(result="1", statusRegional="2"))
                    school.olympicsReadingSummary.medalsSilver = len(olympics_data.students.filter(result="2", statusRegional="2"))
                    school.olympicsReadingSummary.medalsBronze = len(olympics_data.students.filter(result="3", statusRegional="2"))
                    
                    school.olympicsReadingSummary.inscribedNational = len(olympics_data.students.filter(result="1"))
                    school.olympicsReadingSummary.classifiedNational = len(classifiedNational)
                    school.olympicsReadingSummary.medalsGoldNational = len(olympics_data.students.filter(resultNational="1", statusNational="2"))
                    school.olympicsReadingSummary.medalsSilverNational = len(olympics_data.students.filter(resultNational="2", statusNational="2"))
                    school.olympicsReadingSummary.medalsBronzeNational = len(olympics_data.students.filter(resultNational="3", statusNational="2"))
                    school.save()

                elif olympicsType == 'math':
                    school.olympicsSummary.inscribed = len(olympics_data.students)
                    school.olympicsSummary.participant = len([s for s in olympics_data.students if s.status in ["2", "3"]])
                    school.olympicsSummary.classified = len(olympics_data.students.filter(status="3"))
                    
                    school.olympicsSummary.participantRegional = len([s for s in olympics_data.students if s.statusRegional in ["1", "2"]])
                    school.olympicsSummary.classifiedRegional = len(olympics_data.students.filter(statusRegional="2"))
                    
                    school.olympicsSummary.medalsGold = len(olympics_data.students.filter(result="1", statusRegional="2"))
                    school.olympicsSummary.medalsSilver = len(olympics_data.students.filter(result="2", statusRegional="2"))
                    school.olympicsSummary.medalsBronze = len(olympics_data.students.filter(result="3", statusRegional="2"))

                    school.olympicsSummary.inscribedNational = len(olympics_data.students.filter(result="1"))
                    school.olympicsSummary.classifiedNational = len(classifiedNational)
                    school.olympicsSummary.medalsGoldNational = len(olympics_data.students.filter(resultNational="1", statusNational="2"))
                    school.olympicsSummary.medalsSilverNational = len(olympics_data.students.filter(resultNational="2", statusNational="2"))
                    school.olympicsSummary.medalsBronzeNational = len(olympics_data.students.filter(resultNational="3", statusNational="2"))
                    school.save()
                    
                return {"status": 201, "message": "Se han cambiado el estatus de los estudiantes con éxito"}, 201
                
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            return {'status': 400, 'message': "El proyecto peca no existe"},201

        
def name_grade(grade):
    if grade == "0":
        return "Preescolar"
    if grade in ("1", "3"):
        return grade+"er Grado"
    if grade == "2":
        return "2do Grado"
    if grade in ("4", "5", "6"):
        return grade+"to Grado"
