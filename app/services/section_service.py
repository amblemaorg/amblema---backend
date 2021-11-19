# app/services/section_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_section_model import Section
from app.models.peca_amblecoins_model import AmbleSection
from app.schemas.peca_school_schema import SectionSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.helpers.handler_messages import HandlerMessages
from app.models.peca_student_model import SectionClass, Student, Diagnostic, StudentClass
from app.schemas.peca_student_schema import StudentSchema
from datetime import datetime


class SectionService():

    handlerMessages = HandlerMessages()

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                school = SchoolUser.objects(
                    id=peca.project.school.id, isDeleted=False).first()
                schema = SectionSchema()
                if "teacher" in jsonData:

                    teacher = school.teachers.filter(
                        id=jsonData['teacher'], isDeleted=False).first()
                    if not teacher:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"teacher": jsonData['teacher']})
                    else:
                        jsonData['teacher'] = {
                            'id': str(teacher.id),
                            'firstName': teacher.firstName,
                            'lastName': teacher.lastName
                        }
                data = schema.load(jsonData)

                section = Section()
                for field in schema.dump(data).keys():
                    section[field] = data[field]
                if self.checkForDuplicated(peca, section):
                    raise ValidationError(
                        {"name": [{"status": "5",
                                   "msg": "Duplicated record found: {}".format(section.name)}]}
                    )
                try:
                    schoolYear = peca.schoolYear.fetch()
                    if section.grade != "0":
                        section.goals = schoolYear.pecaSetting.goalSetting['grade{}'.format(
                            section.grade)]
                    peca.school.sections.append(section)

                    for i in range(1, 4):
                        if peca['lapse{}'.format(i)].ambleCoins:
                            peca['lapse{}'.format(i)].ambleCoins.sections.append(
                                AmbleSection(
                                    id=str(section.id),
                                    name=section.name,
                                    grade=section.grade
                                )
                            )
                    peca.school.nSections += 1
                    grades = []
                    for section in peca.school.sections:
                        if section.grade not in grades:
                            grades.append(section.grade)
                    peca.school.nGrades = len(grades)
                    school.nSections = peca.school.nSections
                    school.nGrades = peca.school.nGrades
                    school.save()

                    peca.save()
                    return schema.dump(section), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def update(self, pecaId, sectionId, jsonData):

        peca = PecaProject.objects.filter(
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False
        ).first()

        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if sectionId:
                try:
                    schema = SectionSchema()
                    school = SchoolUser.objects(
                        id=peca.project.school.id, isDeleted=False).first()
                    if "teacher" in jsonData:
                        teacher = school.teachers.filter(
                            id=jsonData['teacher'], isDeleted=False).first()
                        if not teacher:
                            raise RegisterNotFound(message="Record not found",
                                                   status_code=404,
                                                   payload={"teacher": jsonData['teacher']})
                        else:
                            jsonData['teacher'] = {
                                'id': str(teacher.id),
                                'firstName': teacher.firstName,
                                'lastName': teacher.lastName
                            }
                    data = schema.load(jsonData)

                    section = peca.school.sections.filter(
                        id=sectionId, isDeleted=False).first()

                    for field in schema.dump(data).keys():
                        if section[field] != data[field]:
                            section[field] = data[field]
                            if field == 'grade':
                                section.goals = peca.schoolYear.fetch(
                                ).pecaSetting.goalSetting['grade{}'.format(section.grade)]
                    if self.checkForDuplicated(peca, section):
                        raise ValidationError(
                            {"name": [{"status": "5",
                                       "msg": "Duplicated record found: {}".format(section.name)}]}
                        )
                    try:
                        for oldSection in peca.school.sections:
                            if str(oldSection.id) == sectionId:
                                oldSection = section
                        for i in range(1, 4):
                            if peca['lapse{}'.format(i)].ambleCoins:
                                for oldSection in peca['lapse{}'.format(i)].ambleCoins.sections:
                                    if oldSection.id == sectionId:
                                        oldSection.name = section.name
                                        oldSection.grade = section.grade
                        peca.save()
                        return schema.dump(section), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

                except ValidationError as err:
                    return err.normalized_messages(), 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"sectionId": sectionId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def delete(self, pecaId, sectionId):
        """
        Delete (change isDeleted to True) a record
        """

        peca = PecaProject.objects.filter(
            id=pecaId,
            isDeleted=False
        ).first()

        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if section:
                school = SchoolUser.objects(
                    id=peca.project.school.id, isDeleted=False).first()

                students = section.students.filter(isDeleted=False)
                if students:
                    return {
                        'status': '0',
                        'entity': 'Student',
                        'msg': self.handlerMessages.getDeleteEntityMsg('Student')
                    }, 419

                try:
                    section.isDeleted = True

                    for i in range(1, 4):
                        if peca['lapse{}'.format(i)].ambleCoins:
                            for oldSection in peca['lapse{}'.format(i)].ambleCoins.sections:
                                if oldSection.id == sectionId:
                                    peca['lapse{}'.format(i)].ambleCoins.sections.remove(
                                        oldSection)
                    peca.school.nSections -= 1
                    grades = []
                    for section in peca.school.sections:
                        if section.grade not in grades:
                            grades.append(section.grade)
                    peca.school.nGrades = len(grades)
                    peca.save()
                    school.nSections = peca.school.nSections
                    school.nGrades = peca.school.nGrades
                    school.save()
                    return "Record deleted successfully", 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"sectionId": sectionId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def checkForDuplicated(self, peca, newSection):

        for section in peca.school.sections.filter(isDeleted=False):
            if section.id != newSection.id and section.grade == newSection.grade and section.name == newSection.name:
                return True
        return False

        """
        section = PecaProject.objects.filter(
            id=peca.id,
            school__sections__isDeleted=False,
            school__sections__grade=newSection.grade,
            school__sections__name=newSection.name
        ).fields(id=1, school__sections={'$elemMatch': {'name': newSection.name, 'grade': newSection.grade}}).first()
        if section:
            return True
        return False
        """

class SectionsExport():
    handlerMessages = HandlerMessages()
    def getSections(self, pecaId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                school_code = peca.school.code
                school = SchoolUser.objects(code=school_code, isDeleted=False).first()

                if "action" in jsonData:
                    if  jsonData["action"] == "export":
                        if "sections" in jsonData:
                            list = []
                            for section in jsonData["sections"]:
                                section_peca = peca.school.sections.filter(isDeleted=False, id=section).first()
                                if section_peca:
                                    section_list = {"name": section_peca.name, "grade": section_peca.grade, "id": str(section_peca.id), "students": []}
                                    for student in section_peca.students.filter(isDeleted=False):
                                        section_list["students"].append({"id":str(student.id), "firstName": student.firstName, "lastName": student.lastName, "cardId": student.cardId, "cardType": student.cardType, "birthdate": str(student.birthdate), "gender": student.gender})
                                    list.append(section_list)
                            return {"status_code":201, "message": "Exito", "sections": list},201
                        else:
                            return {"status_code":404, "message": "Debe enviar secciones a exportar"},201

                    if jsonData["action"] == "import":
                        if ("section" in jsonData) and ("students" in jsonData):    
                            section_peca = peca.school.sections.filter(isDeleted=False, id=jsonData["section"]).first()
                            if section_peca:
                                for student in jsonData["students"]:
                                    if student["nombre"] and student["apellido"] and student["documento_de_identidad"] and student["tipo_de_documento"] and student["fecha_de_nacimiento"] and student["genero"]:
                                        student["genero"] = "1" if student["genero"] == "F" else "2"
                                        student["tipo_de_documento"] = "1" if student["tipo_de_documento"] == "V" else "2"
                                        student["fecha_de_nacimiento"] = datetime.strftime(datetime.strptime(student["fecha_de_nacimiento"], "%d-%m-%Y"), "%Y-%m-%d")
                                        student["fecha_de_nacimiento"] = str(student["fecha_de_nacimiento"])+"T00:00:00.000Z"
                                        student_format = {}
                                        student_format["firstName"] = student["nombre"]
                                        student_format["lastName"] = student["apellido"]
                                        student_format["cardId"] = student["documento_de_identidad"]
                                        student_format["cardType"] = student["tipo_de_documento"]
                                        student_format["birthdate"] = student["fecha_de_nacimiento"]
                                        student_format["gender"] = student["genero"]
                                        
                                        student_find = school.students.filter(isDeleted=False, firstName=student_format["firstName"], lastName=student_format["lastName"], gender=student_format["gender"]).first()
                                        schema = StudentSchema()
                                        data = schema.load(student_format)
                                        student_save = Student()
                                        for field in schema.dump(data).keys():
                                            student_save[field] = data[field]
                                        
                                        for i in range(3):
                                            student_save['lapse{}'.format(i+1)] = Diagnostic()
                                        
                                        if student_find:
                                            student_save.id = student_find.id
                                                
                                        
                                        if not self.checkForDuplicated(section_peca, student_save):
                                            in_section = False
                                            if student_find:
                                                for sec in student_find.sections.filter():
                                                    if sec.schoolYear.id == peca.schoolYear.id:
                                                        in_section = True
                                            if not in_section:
                                                section_save = SectionClass()
                                                section_save.name = section_peca.name
                                                section_save.grade = section_peca.grade
                                                section_save.isDeleted = False
                                                section_save.schoolYear = peca.schoolYear.id
                                                section_save.id = section_peca.id

                                                PecaProject.objects(
                                                    id=pecaId,
                                                    school__code=school_code,
                                                    school__sections__id=section_peca.id
                                                ).update(
                                                    push__school__sections__S__students=student_save)

                                                if student_find:
                                                    for est in school.students:
                                                        if est.id == student_save.id:
                                                            valid = True
                                                            for sect in est.sections:
                                                                if sect.schoolYear.id == peca.schoolYear.id:
                                                                    valid = False
                                                            if valid:
                                                                est.sections.append(section_save)
                                                else:
                                                    student_class = StudentClass()
                                                    student_class.id = student_save.id
                                                    student_class.firstName = student_save.firstName
                                                    student_class.lastName = student_save.lastName
                                                    student_class.cardId = student_save.cardId
                                                    student_class.cardType = student_save.cardType
                                                    student_class.birthdate = student_save.birthdate
                                                    student_class.gender = student_save.gender
                                                    student_class.isDeleted = False
                                                    student_class.sections = [section_save]
                                                    
                                                    school.students.append(student_class)
                                school.save()

                                return {"status_code":201, "message": "Estudiantes importados con éxito"},201                
                            else:
                                return {"status_code":404, "message": "Debe enviar una sección válida a importar"},201

                        else:
                            return {"status_code":404, "message": "Debe enviar una sección a importar"},201

                else:
                    raise RegisterNotFound(message="Debe escoger una acción a realizar",
                                   status_code=404)
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def checkForDuplicated(self, section, newStudent):
        for s in section.students.filter(isDeleted=False):
            if newStudent.cardId != "" and newStudent.cardId != None:
                if (
                    (
                        s.id != newStudent.id
                        and s.firstName == newStudent.firstName
                        and s.lastName == newStudent.lastName
                        and s.birthdate == newStudent.birthdate
                        and s.gender == newStudent.gender
                    ) or
                    (
                        s.id != newStudent.id
                        and s.cardId == newStudent.cardId
                        and s.cardType == newStudent.cardType
                    )
                ):
                    return True
            else:
                if (
                    (
                        s.id != newStudent.id
                        and s.firstName == newStudent.firstName
                        and s.lastName == newStudent.lastName
                        and s.birthdate == newStudent.birthdate
                        and s.gender == newStudent.gender
                    )
                ):
                    return True
        return False