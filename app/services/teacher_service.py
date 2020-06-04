# app/services/teacher_service.py


from flask import current_app
from marshmallow import ValidationError
from mongoengine.queryset.visitor import Q

from app.models.school_user_model import SchoolUser
from app.models.teacher_model import Teacher
from app.schemas.teacher_schema import TeacherSchema
from app.helpers.error_helpers import RegisterNotFound


class TeacherService():

    def getAll(self, schoolId):

        school = SchoolUser.objects(
            isDeleted=False, id=schoolId).first()

        if school:
            return {"records": TeacherSchema().dump(school.teachers, many=True)}, 200

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": schoolId})

    def save(self, schoolId, jsonData):

        school = SchoolUser.objects(
            isDeleted=False, id=schoolId).first()

        if school:
            try:
                schema = TeacherSchema()
                data = schema.load(jsonData)
                teacher = Teacher()
                for field in schema.dump(data).keys():
                    teacher[field] = data[field]
                duplicated = self.checkForDuplicated(schoolId, teacher)
                if duplicated:
                    raise ValidationError(
                        {duplicated: [{"status": "5",
                                       "msg": "Duplicated record found"}]}
                    )
                try:
                    school.teachers.append(teacher)
                    school.save()
                    return schema.dump(teacher), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": schoolId})

    def update(self, schoolId, teacherId, jsonData):

        school = SchoolUser.objects.filter(
            id=schoolId,
            teachers__id=teacherId,
            teachers__isDeleted=False
        ).only('teachers').first()

        if school:
            try:
                schema = TeacherSchema()
                data = schema.load(jsonData)

                teacher = school.teachers.filter(
                    id=teacherId, isDeleted=False).first()

                for field in schema.dump(data).keys():
                    teacher[field] = data[field]
                duplicated = self.checkForDuplicated(schoolId, teacher)
                if duplicated:
                    raise ValidationError(
                        {duplicated: [{"status": "5",
                                       "msg": "Duplicated record found"}]}
                    )
                try:
                    SchoolUser.objects(
                        id=schoolId,
                        teachers__id=teacherId,
                        teachers__isDeleted=False,
                    ).update(set__teachers__S=teacher)
                    return schema.dump(teacher), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId, "teacherId": teacherId})

    def delete(self, schoolId, teacherId):
        """
        Delete (change isDeleted to True) a record
        """

        school = SchoolUser.objects(
            Q(id=schoolId)
            & Q(teachers__isDeleted__ne=True)
            & Q(teachers__id=teacherId)
        ).only('teachers').first()

        if school:
            try:
                teacher = school.teachers.filter(id=teacherId).first()
                teacher.isDeleted = True
                try:
                    SchoolUser.objects(
                        id=schoolId,
                        teachers__id=teacherId,
                        teachers__isDeleted__ne=True
                    ).update(set__teachers__S__isDeleted=True)
                    return "Record deleted successfully", 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId, "teacherId": teacherId})

    def checkForDuplicated(self, schoolId, newTeacher):
        school = SchoolUser.objects(
            Q(id=schoolId)
            & Q(teachers__isDeleted__ne=True)
        ).only('teachers').first()

        if school:
            for teacher in school.teachers:
                if teacher.email == newTeacher.email and teacher.id != newTeacher.id:
                    return 'email'
                elif teacher.cardId == newTeacher.cardId and teacher.cardType == newTeacher.cardType and teacher.id != newTeacher.id:
                    return 'cardId'

        return False
