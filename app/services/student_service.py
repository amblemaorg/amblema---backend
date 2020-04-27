# app/services/student_service.py


from flask import current_app
from marshmallow import ValidationError
from mongoengine.queryset.visitor import Q

from app.models.peca_project_model import PecaProject
from app.models.peca_project_model import Student, Diagnostic
from app.schemas.peca_project_schema import StudentSchema
from app.helpers.error_helpers import RegisterNotFound


class StudentService():

    def save(self, pecaId, sectionId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False).first()

        if peca:
            try:
                schema = StudentSchema()
                data = schema.load(jsonData)
                student = Student()
                for field in schema.dump(data).keys():
                    student[field] = data[field]

                for i in range(3):
                    student['lapse{}'.format(i+1)] = Diagnostic()
                if self.checkForDuplicated(peca.id, sectionId, student):
                    raise ValidationError(
                        {"name": [{"status": "5",
                                   "msg": "Duplicated record found: {}".format(student.firstName)}]}
                    )
                try:
                    PecaProject.objects(
                        id=pecaId,
                        school__sections__id=sectionId
                    ).update(push__school__sections__S__students=student)
                    return schema.dump(student), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId})

    def update(self, pecaId, sectionId, studentId, jsonData):

        peca = PecaProject.objects.filter(
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False,
            school__sections__students__id=studentId,
            school__sections__students__isDeleted=False
        ).only('school__sections').first()

        if peca:
            try:
                schema = StudentSchema()
                data = schema.load(jsonData)

                student = peca.school.sections.filter(
                    id=sectionId, isDeleted=False).first().students.filter(
                        id=studentId, isDeleted=False
                ).first()

                for field in schema.dump(data).keys():
                    student[field] = data[field]
                if self.checkForDuplicated(pecaId, sectionId, student):
                    raise ValidationError(
                        {"name": [{"status": "5",
                                   "msg": "Duplicated record found: {}".format(student.firstName)}]}
                    )
                try:
                    for section in peca.school.sections:
                        if str(section.id) == sectionId and not section.isDeleted:
                            for student in section.students:
                                if str(student.id) == studentId and not student.isDeleted:
                                    student = student
                    peca.save()
                    return schema.dump(student), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId, "studentId": studentId})

    def delete(self, pecaId, sectionId, studentId):
        """
        Delete (change isDeleted to True) a record
        """
        peca = PecaProject.objects.filter(
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False,
            school__sections__students__id=studentId,
            school__sections__students__isDeleted=False
        ).only('school__sections').first()

        if peca:

            try:
                for section in peca.school.sections:
                    if str(section.id) == sectionId and not section.isDeleted:
                        for student in section.students:
                            if str(student.id) == studentId and not student.isDeleted:
                                student.isDeleted = True
                peca.save()
                return "Record deleted successfully", 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId, "studentId": studentId})

    def checkForDuplicated(self, pecaId, sectionId, newStudent):
        student = PecaProject.objects((
            Q(id=pecaId)
            & Q(school__sections__isDeleted=False)
            & Q(school__sections__id=sectionId)
            & Q(school__sections__students__firstName=newStudent.firstName)
            & Q(school__sections__students__lastName=newStudent.lastName)
            & Q(school__sections__students__birthdate=newStudent.birthdate)
            & Q(school__sections__students__gender=newStudent.gender)
        ) |
            (
            Q(school__sections__students__cardId__exists=True)
            & Q(school__sections__students__cardId=newStudent.cardId)
        )).only('id').first()
        if student:
            return True
        return False
