# app/services/teacher_service.py


from flask import current_app
from marshmallow import ValidationError
from mongoengine.queryset.visitor import Q

from app.models.peca_project_model import PecaProject
from app.models.peca_project_model import Teacher
from app.schemas.peca_project_schema import TeacherSchema
from app.helpers.error_helpers import RegisterNotFound


class TeacherService():

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                schema = TeacherSchema()
                data = schema.load(jsonData)
                teacher = Teacher()
                for field in schema.dump(data).keys():
                    teacher[field] = data[field]
                duplicated = self.checkForDuplicated(pecaId, teacher)
                if duplicated:
                    raise ValidationError(
                        {duplicated: [{"status": "5",
                                       "msg": "Duplicated record found"}]}
                    )
                try:
                    peca.school.teachers.append(teacher)
                    peca.save()
                    return schema.dump(teacher), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def update(self, pecaId, teacherId, jsonData):

        peca = PecaProject.objects.filter(
            id=pecaId,
            school__teachers__id=teacherId,
            school__teachers__isDeleted=False
        ).only('school__teachers').first()

        if peca:
            try:
                schema = TeacherSchema()
                data = schema.load(jsonData)

                teacher = peca.school.teachers.filter(
                    id=teacherId, isDeleted=False).first()

                for field in schema.dump(data).keys():
                    teacher[field] = data[field]
                duplicated = self.checkForDuplicated(pecaId, teacher)
                if duplicated:
                    raise ValidationError(
                        {duplicated: [{"status": "5",
                                       "msg": "Duplicated record found"}]}
                    )
                try:
                    PecaProject.objects(
                        id=pecaId,
                        school__teachers__id=teacherId,
                        school__teachers__isDeleted=False,
                    ).update(set__school__teachers__S=teacher)
                    return schema.dump(teacher), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "teacherId": teacherId})

    def delete(self, pecaId, teacherId):
        """
        Delete (change isDeleted to True) a record
        """

        peca = PecaProject.objects(
            Q(id=pecaId)
            & Q(school__teachers__isDeleted__ne=True)
            & Q(school__teachers__id=teacherId)
        ).only('school__teachers').first()

        if peca:
            try:
                teacher = peca.school.teachers.filter(id=teacherId).first()
                teacher.isDeleted = True
                try:
                    PecaProject.objects(
                        id=pecaId,
                        school__teachers__id=teacherId,
                        school__teachers__isDeleted__ne=True
                    ).update(set__school__teachers__S__isDeleted=True)
                    return "Record deleted successfully", 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "teacherId": teacherId})

    def checkForDuplicated(self, pecaId, newTeacher):
        peca = PecaProject.objects(
            Q(id=pecaId)
            & Q(school__teachers__isDeleted__ne=True)
        ).only('school__teachers').first()

        if peca:
            for teacher in peca.school.teachers:
                if teacher.email == newTeacher.email and teacher.id != newTeacher.id:
                    return 'email'
                elif teacher.cardId == newTeacher.cardId and teacher.cardType == newTeacher.cardType and teacher.id != newTeacher.id:
                    return 'cardId'

        return False
