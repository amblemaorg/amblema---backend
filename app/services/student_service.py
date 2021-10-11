# app/services/student_service.py


from flask import current_app
from marshmallow import ValidationError
from mongoengine.queryset.visitor import Q
from bson import ObjectId
from app.models.peca_project_model import PecaProject
from app.models.peca_student_model import Student, Diagnostic, StudentClass, SectionClass
from app.schemas.peca_student_schema import StudentSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.helpers.handler_messages import HandlerMessages


class StudentService():

    handlerMessages = HandlerMessages()

    def save(self, pecaId, sectionId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId).first()

        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if section:
                try:
                    schema = StudentSchema()
                    data = schema.load(jsonData)
                    student = Student()
                    for field in schema.dump(data).keys():
                        student[field] = data[field]
                    
                    for i in range(3):
                        student['lapse{}'.format(i+1)] = Diagnostic()
                    if self.checkForDuplicated(section, student):
                        raise ValidationError(
                            {"name": [{"status": "5",
                                       "msg": "Duplicated record found: {}".format(student.firstName)}]}
                        )
                    try:
                        
                        section_save = SectionClass()
                        section_save.id = section.id
                        section_save.grade = section.grade
                        section_save.name = section.name
                        section_save.schoolYear = peca.schoolYear
                        section_save.isDeleted = False
                        
                        nStudents = 1
                        for section in peca.school.sections.filter(isDeleted=False):
                            nStudents += len(section.students.filter(isDeleted=False))
                        PecaProject.objects(
                            id=pecaId,
                            school__sections__id=sectionId
                        ).update(
                            push__school__sections__S__students=student,
                            set__school__nStudents=nStudents)
                        SchoolUser.objects(id=peca.project.school.id).update(
                            set__nStudents=nStudents)
                        SchoolYear.objects(isDeleted=False, status="1").update(
                            inc__nStudents=1)

                        
                        
                        student_save = StudentClass()
                        student_save.id = student.id
                        student_save.firstName = student.firstName
                        student_save.lastName = student.lastName
                        student_save.cardId = student.cardId
                        student_save.cardType = student.cardType
                        student_save.birthdate = student.birthdate
                        student_save.gender = student.gender
                        student_save.isDeleted = False
                        student_save.sections = [section_save]
                        
                        school = SchoolUser.objects(id=peca.project.school.id).first()
                        school.students.append(student_save)
                        school.save()
                        return schema.dump(student), 200
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

    def update(self, pecaId, sectionId, studentId, jsonData):

        peca = PecaProject.objects.filter(
            id=pecaId,
            isDeleted=False
        ).first()

        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if section:
                student = section.students.filter(
                    isDeleted=False, id=studentId).first()
                if student:
                    try:
                        schema = StudentSchema()
                        data = schema.load(jsonData)

                        for field in schema.dump(data).keys():
                            student[field] = data[field]
                        if self.checkForDuplicated(section, student):
                            return {"status": "1", "msg": "Duplicated record found"}, 400
                        try:
                            peca.save()
                        
                            school = SchoolUser.objects(id=peca.project.school.id).first()
                            student_school = school.students.filter(id=ObjectId(studentId)).first()
                            if student_school:
                                student_school.firstName = student.firstName
                                student_school.lastName = student.lastName
                                student_school.cardId = student.cardId
                                student_school.cardType = student.cardType
                                student_school.birthdate = student.birthdate
                                student_school.gender = student.gender
                                school.save()
                            
                            return schema.dump(student), 200
                        except Exception as e:
                            return {'status': 0, 'message': str(e)}, 400

                    except ValidationError as err:
                        return err.normalized_messages(), 400
                else:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"studentId": studentId})
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"sectionId": sectionId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def delete(self, pecaId, sectionId, studentId):
        """
        Delete (change isDeleted to True) a record
        """
        peca = PecaProject.objects(
            id=pecaId,
            isDeleted=False
        ).first()
        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if section:
                student = section.students.filter(
                    isDeleted=False, id=studentId).first()
                if student:
                    entity = ''
                    # validate olympics
                    for lapse in [1, 2, 3]:
                        olympics = peca['lapse{}'.format(lapse)].olympics
                        if olympics:
                            enrolled = olympics.students.filter(
                                id=studentId).first()
                            if enrolled:
                                entity = 'OlympicsPeca'
                                break
                    if entity:
                        return {
                            'status': '0',
                            'entity': entity,
                            'msg': self.handlerMessages.getDeleteEntityMsg(entity)
                        }, 419

                    try:
                        schoolYear = peca.schoolYear.fetch()

                        if student.hasDiagnostics():
                            student.deleteDiagnostics(
                                [1, 2, 3],
                                ['wordsPerMin', 'multiplicationsPerMin', 'operationsPerMin'])
                            section.refreshDiagnosticsSummary()
                            peca.school.refreshDiagnosticsSummary()
                            schoolYear.refreshDiagnosticsSummary()

                        student.isDeleted = True
                        
                        student_school = school.students.filter(id=student.id).first()
                        sections_currents = []
                        for sect in student_school.sections:
                            if sect.id !=  section.id:
                                sections_currents.append(sect)
            
                        section = peca.school.sections.filter(id=peca.project.school.id).first()
                        student_school.sections = sections_currents
                        
                        peca.school.nStudents -= 1
                        peca.save()
                        school.save()
                        
                        SchoolUser.objects(id=peca.project.school.id).update(
                            dec__school__nStudents=1)
                        schoolYear.nStudents -= 1
                        schoolYear.save()
                        return "Record deleted successfully", 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400
                else:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"studentId": studentId})
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"sectionId": sectionId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

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

        '''section.students.filter(
            id__ne=newStudent.id,
            isDeleted=False,
            firstName=newStudent.firstName,
            lastName=newStudent.lastName,
            birthdate=newStudent.birthdate,
            gender=newStudent.gender
        ).first()
        if not students and newStudent.cardId:
            students = section.students.filter(
                isDeleted=False,
                cardId=newStudent.cardId,
                id__ne=newStudent.id
            ).first()

        if students:
            return True
        return False'''
