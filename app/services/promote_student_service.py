# app/services/cron_student_service.py

from datetime import datetime

from flask import current_app
from marshmallow import ValidationError
from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.peca_student_model import SectionClass, Student, Diagnostic
from app.models.peca_student_model import StudentClass

from bson import ObjectId
class PromoteStudentService():
    def getList(self, school_code, id_section):
        try:
            
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            schoolYearPrevius = SchoolYear.objects(isDeleted=False, status="2").order_by('-createdAt').first()
            school = SchoolUser.objects(code=school_code, isDeleted=False).first()
            peca = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYearPrevius.id, school__code=school_code).first()
            peca_actual = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYear.id).first()
            if peca:
                section_peca = peca.school.sections.filter(isDeleted=False, id=id_section).first()
                students_list = []
                if section_peca:
                    for student in section_peca.students.filter(isDeleted=False):
                        st = school.students.filter(isDeleted=False, id=student.id).first()
                        if st:
                            valid = True
                            for nt in st.sections:
                                if nt.schoolYear.id == schoolYear.id:
                                    valid = False
                            if valid:
                                students_list.append({"id":str(student.id), "firstName": student.firstName, "lastName": student.lastName, "cardId": student.cardId, "cardType": student.cardType, "birthdate": str(student.birthdate), "gender": student.gender})
                return {"status":200, "msg": "Exito", "students": students_list},200
            else:
                return {"status":400, "msg": "No tiene data de periodos anteriores"},200
                
        except Exception as e:   
            return {'status': 0, 'message': str(e)}, 400
    
    def promoteStudents(self, school_code, data):
        try:
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            peca_actual = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYear.id, school__code=school_code).first()
            section = peca_actual.school.sections.filter(
                    isDeleted=False, id=data["id_section_current"]).first()
            school = SchoolUser.objects(code=school_code, isDeleted=False).first()
            pecaId = peca_actual.id
            if section:
                for student in data["students"]:
                    student_save = Student()
                    student_save.id = student["id"]
                    student_save.firstName = student["firstName"]
                    student_save.lastName = student["lastName"]
                    student_save.cardId = student["cardId"]
                    student_save.cardType = student["cardType"]
                    student_save.birthdate = student["birthdate"]
                    student_save.gender = student["gender"]
                    student_save.isDeleted = False
                    student_save.lapse1 = Diagnostic()
                    student_save.lapse2 = Diagnostic()
                    student_save.lapse3 = Diagnostic()

                    section_save = SectionClass()
                    section_save.name = section.name
                    section_save.grade = section.grade
                    section_save.isDeleted = False
                    section_save.schoolYear = schoolYear.id
                    section_save.id = section.id
                    
                            
                    PecaProject.objects(
                                id=pecaId,
                                school__code=school_code,
                                school__sections__id=data["id_section_current"]
                            ).update(
                                push__school__sections__S__students=student_save)
                    
                    for est in school.students:
                        if est.id == ObjectId(student["id"]):
                            valid = True
                            for sect in est.sections:
                                if sect.schoolYear.id == schoolYear.id:
                                    valid = False
                            if valid:
                                est.sections.append(section_save)                                
                
                nStudents = 0
                peca_actual.reload()
                for section in peca_actual.school.sections.filter(isDeleted=False):
                    nStudents += len(section.students.filter(isDeleted=False))
                peca_actual.school.nStudents = nStudents
                peca_actual.save()
                school.nStudents = nStudents
                school.save()

                schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
                pecas = PecaProject.objects(
                    schoolYear=schoolYear.id, isDeleted=False).only('school', 'project')
                
                nStudents = 0
                
                for peca in pecas:
                    schoolUser = SchoolUser.objects(isDeleted=False, id=peca.project.school.id).first()
                    peca.school.nStudents = 0
                    for section in peca.school.sections.filter(isDeleted=False):
                        peca.school.nStudents += len(section.students.filter(isDeleted=False))
                    schoolUser.nStudents = peca.school.nStudents
                    peca.save()
                    schoolUser.save()
                    nStudents += peca.school.nStudents
                schoolYear.nStudents = nStudents
                schoolYear.save()

                return {"status":201, "msg": "Estudiantes promovidos con exito"},201
            else:
                return {"status":400, "msg": "La sección no existe"},201
        except Exception as e:
            
            return {'status': 0, 'message': str(e)}, 400

class SectionsPromoteStudentService():
    def getSections(self, school_code):
        try:
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            schoolYearPrevius = SchoolYear.objects(isDeleted=False, status="2").order_by('-createdAt').first()
            peca_actual = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYear.id, school__code=school_code).first()
            peca_previus = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYearPrevius.id, school__code=school_code).first()
            if peca_previus:
                if peca_actual:
                    sections_peca_actual = peca_actual.school.sections.filter(isDeleted=False)
                    sections_list_actual = []
                    for section in sections_peca_actual:
                        sections_list_actual.append({"id":str(section.id), "grade": section.grade, "name": section.name})

                    sections_peca_previus = peca_previus.school.sections.filter(isDeleted=False)
                    sections_list_previus = []
                    for section in sections_peca_previus:
                        sections_list_previus.append({"id":str(section.id), "grade": section.grade, "name": section.name})
                    
                    return {"status": 200, "section_previus": sections_list_previus, "section_current": sections_list_actual},200
                else:
                    return {"status": 400, "msg": "La escuela no tiene proyecto actual"},200
            else:
                return {"status": 400, "msg": "La escuela no tiene proyecto anterior"},200
                
        except Exception as e:
            
            return {'status': 0, 'message': str(e)}, 400        

class ChangeSectionStudentsService():
    def changeSection(self, data, pecaID):
        try:
            peca = PecaProject.objects(
                isDeleted=False,
                id=pecaID).first()
            if peca:
                school_code = peca.school.code
                school = SchoolUser.objects(code=school_code, isDeleted=False).first()
                section = peca.school.sections.filter(id=data["section_previus"]).first()
                if section:
                    section_new = peca.school.sections.filter(id=data["section_new"]).first()
                    if section_new:
                        for student in data["students"]:
                            st = section.students.filter(
                        isDeleted=False, id=student["id"]).first()
                            st.isDeleted = True
                            student_save = Student()
                            student_save.id = student["id"]
                            student_save.firstName = student["firstName"]
                            student_save.lastName = student["lastName"]
                            student_save.cardId = student["cardId"]
                            student_save.cardType = student["cardType"]
                            student_save.birthdate = student["birthdate"]
                            student_save.gender = student["gender"]
                            student_save.isDeleted = False
                            student_save.lapse1 = Diagnostic()
                            student_save.lapse2 = Diagnostic()
                            student_save.lapse3 = Diagnostic()

                            section_new.students.append(student_save)

                            student_school = school.students.filter(id=ObjectId(student["id"])).first()
                            if student_school:
                                sections_currents = []
                                for sect in student_school.sections:
                                    if sect.id !=  section.id:
                                        sections_currents.append(sect)
                                
                                student_school.sections = sections_currents
                        
                                section_save = SectionClass()
                                section_save.name = section_new.name
                                section_save.grade = section_new.grade
                                section_save.isDeleted = False
                                section_save.schoolYear = peca.schoolYear
                                section_save.id = section_new.id

                                student_school.sections.append(section_save)
                        
                        nStudents = 0
                        for section in peca.school.sections.filter(isDeleted=False):
                            nStudents += len(section.students.filter(isDeleted=False))
                        peca.school.nStudents = nStudents
                        peca.save()
                        school.nStudents = nStudents
                        school.save()
            
                        
                        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
                        pecas = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False).only('school', 'project')
                        
                        nStudents = 0
                        
                        for peca in pecas:
                            schoolUser = SchoolUser.objects(isDeleted=False, id=peca.project.school.id).first()
                            peca.school.nStudents = 0
                            for section in peca.school.sections.filter(isDeleted=False):
                                peca.school.nStudents += len(section.students.filter(isDeleted=False))
                            schoolUser.nStudents = peca.school.nStudents
                            peca.save()
                            schoolUser.save()
                            nStudents += peca.school.nStudents
                        schoolYear.nStudents = nStudents
                        schoolYear.save()
        
                        return {"status": 201, "msg": "Estudiantes cambiados con éxito"},201    
                    else:
                        return {"status": 400, "msg": "No se encontro la sección nueva"},200
                
                else:
                    return {"status": 400, "msg": "No se encontro la sección anterior"},200
                    
            else:
                return {"status": 400, "msg": "No se encontro el proyecto"},200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

    def deleteStudentForSection(self, data, pecaId):
        try:
            peca = PecaProject.objects(
                isDeleted=False,
                id=pecaId).first()
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            
            if peca:
                school_code = peca.school.code
                school = SchoolUser.objects(code=school_code, isDeleted=False).first()
                section = peca.school.sections.filter(id=data["section"]).first()
                if section:
                    for student in data["students"]:
                        st = section.students.filter(
                    isDeleted=False, id=student["id"]).first()
                        st.isDeleted = True
                        
                        student_school = school.students.filter(id=ObjectId(student["id"])).first()
                        if student_school:
                            sections_currents = []
                            for sect in student_school.sections:
                                if sect.id !=  section.id and sect.schoolYear.id != schoolYear.id:
                                    sections_currents.append(sect)
                                
                            student_school.sections = sections_currents
                    nStudents = 0
                    for section in peca.school.sections.filter(isDeleted=False):
                        nStudents += len(section.students.filter(isDeleted=False))
                    peca.school.nStudents = nStudents
                    
                    school.nStudents = nStudents
                            
                    peca.save()
                    school.save()
        
                    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
                    pecas = PecaProject.objects(
                        schoolYear=schoolYear.id, isDeleted=False).only('school', 'project')
                    
                    nStudents = 0
                    
                    for peca in pecas:
                        schoolUser = SchoolUser.objects(isDeleted=False, id=peca.project.school.id).first()
                        peca.school.nStudents = 0
                        for section in peca.school.sections.filter(isDeleted=False):
                            peca.school.nStudents += len(section.students.filter(isDeleted=False))
                        schoolUser.nStudents = peca.school.nStudents
                        peca.save()
                        schoolUser.save()
                        nStudents += peca.school.nStudents
                    schoolYear.nStudents = nStudents
                    schoolYear.save()
    
                    return {"status": 201, "msg": "Estudiantes eliminados con éxito"},201    
                else:
                    return {"status": 400, "msg": "No se encontro la sección"},200
            else:
                return {"status": 400, "msg": "No se encontro el proyecto"},200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400