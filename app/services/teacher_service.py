# app/services/teacher_service.py


from flask import current_app
from marshmallow import ValidationError
from mongoengine.queryset.visitor import Q

from app.models.school_user_model import SchoolUser
from app.models.teacher_model import Teacher
from app.schemas.teacher_schema import TeacherSchema
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.handler_messages import HandlerMessages


class TeacherService():

    handlerMessage = HandlerMessages()

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
        from app.models.peca_project_model import PecaProject
        from app.models.school_year_model import SchoolYear
        from app.blueprints.web_content.models.web_content import WebContent

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
                    school.nTeachers = len(school.teachers.filter(isDeleted=False, status="1"))
                    school.save()
                    period = SchoolYear.objects(
                        isDeleted=False, status="1").first()
                    if period:
                        PecaProject.objects(project__school__id=str(school.id), isDeleted=False, schoolYear=period.id).update(
                            set__school__nTeachers=school.nTeachers
                        )
                        period.nTeachers += 1
                        period.save()
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
        ).first()

        if school:
            teacher = school.teachers.filter(
                isDeleted=False, id=teacherId).first()
            if teacher:
                try:
                    schema = TeacherSchema()
                    data = schema.load(jsonData)

                    for field in schema.dump(data).keys():
                        teacher[field] = data[field]
                    duplicated = self.checkForDuplicated(schoolId, teacher)
                    if duplicated:
                        raise ValidationError(
                            {duplicated: [{"status": "5",
                                           "msg": "Duplicated record found"}]}
                        )
                    try:
                        school.save()
                        return schema.dump(teacher), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

                except ValidationError as err:
                    return err.normalized_messages(), 400
            else:
                RegisterNotFound(message="Record not found",
                                 status_code=404,
                                 payload={"teacherId": teacherId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId, "teacherId": teacherId})

    def delete(self, schoolId, teacherId):
        """
        Delete (change isDeleted to True) a record
        """
        from app.models.peca_project_model import PecaProject
        from app.models.school_year_model import SchoolYear
        from app.blueprints.web_content.models.web_content import WebContent

        school = SchoolUser.objects(
            Q(id=schoolId)
            & Q(teachers__isDeleted=False)
            & Q(teachers__id=teacherId)
        ).first()

        if school:
            teacher = school.teachers.filter(
                id=teacherId, isDeleted=False).first()
            if teacher:
                period = SchoolYear.objects(
                    isDeleted=False, status="1").first()
                if period:
                    peca = PecaProject.objects(
                        project__school__id=str(school.id), isDeleted=False, schoolYear=period.id).first()
                    if peca:
                        sections = [section for section in peca.school.sections.filter(
                            isDeleted=False) if section.teacher.id == teacherId]
                        if sections:
                            return {
                                'status': '0',
                                'entity': 'Section',
                                'msg': self.handlerMessage.getDeleteEntityMsg('Section')
                            }, 419

                teacher.isDeleted = True
                try:
                    school.teachers.filter(
                    id=teacherId, isDeleted=False).update(isDelete = True)
                    school.save()
                    school.nTeachers = len(school.teachers.filter(isDeleted=False, status="1"))
                    school.save()
                    """SchoolUser.objects(
                        id=schoolId,
                        teachers__id=teacherId,
                        teachers__isDeleted=False
                    ).update(
                        set__teachers__S__isDeleted=True,
                        set__nTeachers=len(school.teachers.filter(isDeleted=False)))
                    """

                    if period:
                        PecaProject.objects(project__school__id=str(school.id), isDeleted=False, schoolYear=period.id).update(
                            set__school__nTeachers=school.nTeachers
                        )
                        period.nTeachers -= 1
                        period.save()

                    return "Record deleted successfully", 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"teacherId": teacherId})
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
            for teacher in school.teachers.filter(isDeleted=False):
                if teacher.email == newTeacher.email and teacher.id != newTeacher.id:
                    return 'email'
                elif teacher.cardId == newTeacher.cardId and teacher.cardType == newTeacher.cardType and teacher.id != newTeacher.id:
                    return 'cardId'

        return False
