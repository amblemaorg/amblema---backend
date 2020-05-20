# app/services/peca_annual_preparation_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_olympics_model import Olympics, Student
from app.schemas.peca_annual_preparation_schema import AnnualPreparationSchema, TeachersSchema
from app.helpers.error_helpers import RegisterNotFound


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
                    teachers = []
                    for teacher in peca.school.teachers:
                        if not teacher.isDeleted:
                            teachers.append({
                                "id": str(teacher.id),
                                "firstName": teacher.firstName,
                                "lastName": teacher.lastName,
                                "phone": teacher.phone,
                                "email": teacher.email,
                                "annualPreparationStatus": teacher.annualPreparationStatus
                            })

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
            schema = TeachersSchema()

            teacherId = jsonData['teacherId']
            teacher = peca.school.teachers.filter(
                isDeleted=False, id=teacherId).first()
            if not teacher:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"teacher: ": teacherId})
            if not teacher.annualPreparationStatus:
                teacher.annualPreparationStatus = "1"
                try:
                    for oldTeacher in peca.school.teachers:
                        if oldTeacher.id == teacher.id:
                            oldTeacher = teacher
                        peca.save()
                        break
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            return schema.dump(teacher), 200

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

                record = peca.school.teachers.filter(
                    isDeleted=False, id=teacherId).first()
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
                    for teacher in peca.school.teachers:
                        if teacher.id == record.id:
                            teacher = record
                            break
                    try:
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
