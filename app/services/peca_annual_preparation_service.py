# app/services/peca_annual_preparation_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.schemas.peca_annual_preparation_schema import AnnualPreparationSchema, TeachersSchema
from app.models.peca_annual_preparation_model import Teacher
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser


class AnnualPreparationService():

    def get(self, pecaId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = AnnualPreparationSchema()
            for i in range(1, 4):
                if peca['lapse{}'.format(i)].annualPreparation:
                    annualPreparation = peca['lapse{}'.format(
                        i)].annualPreparation
                    data = schema.dump(annualPreparation)
                    return schema.dump(data), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            school = SchoolUser.objects(
                id=peca.project.school.id, isDeleted=False).first()
            schema = TeachersSchema()
            teachersIds = jsonData['teachersIds']
            teachers = []
            for teacherId in teachersIds:
                teacher = school.teachers.filter(
                isDeleted=False, id=teacherId).first()
                if not teacher:
                    raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"teacher: ": teacherId})
                else:
                    teachers.append(teacher)
            for i in range(1, 4):
                if peca['lapse{}'.format(i)].annualPreparation:
                    annualPreparation = peca['lapse{}'.format(
                        i)].annualPreparation

                    enrolledTeachersIds = [] 
                    for enrl in annualPreparation.teachers:
                        enrolledTeachersIds.append(enrl.id)

                    for teacher in teachers:
                        if str(teacher.id) not in enrolledTeachersIds:
                            enrolledTeacher = Teacher(
                                id=str(teacher.id),
                                firstName=teacher.firstName,
                                lastName=teacher.lastName,
                                phone=teacher.phone,
                                email=teacher.email,
                                pecaId=pecaId
                            )
                            annualPreparation.teachers.append(
                                enrolledTeacher
                            )
                    for teacher in annualPreparation.teachers:
                        if str(teacher.id) not in teachersIds:
                            annualPreparation.teachers.remove(teacher)

                    try:
                        peca.save()
                        return schema.dump(annualPreparation.teachers, many=True), 200
                    except Exception as e:
                        return {'status': "0", 'message': str(e)}, 400
                    
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def update(self, pecaId, teacherId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = TeachersSchema(only=("annualPreparationStatus",))
                data = schema.load(jsonData, partial=True)

                for i in range(1, 4):
                    if peca['lapse{}'.format(i)].annualPreparation:
                        annualPreparation = peca['lapse{}'.format(
                            i)].annualPreparation
                        record = annualPreparation.teachers.filter(
                            id=teacherId).first()
                        if not record:
                            raise RegisterNotFound(message="Record not found",
                                                   status_code=404,
                                                   payload={"teacher: ": teacherId})

                        has_changed = False
                        for field in data.keys():
                            if data[field] != record[field]:
                                record[field] = data[field]
                                has_changed = True
                        if has_changed:
                            for teacher in annualPreparation.teachers:
                                if teacher.id == record.id:
                                    teacher = record
                                    break
                            try:
                                peca['lapse{}'.format(
                                    i)].annualPreparation = annualPreparation
                                peca.save()
                            except Exception as e:
                                return {'status': 0, 'message': str(e)}, 400
                        return schema.dump(record), 200

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    '''def delete(self, pecaId, teacherId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:

            for i in range(1, 4):
                if peca['lapse{}'.format(i)].annualPreparation:
                    annualPreparation = peca['lapse{}'.format(
                        i)].annualPreparation
                    record = annualPreparation.teachers.filter(
                        id=teacherId).first()
                    if not record:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"teacher: ": teacherId})

                    try:
                        peca['lapse{}'.format(
                            i)].annualPreparation.teachers.remove(record)
                        peca.save()
                        return {"message": "Record deleted successfully"}, 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
    '''