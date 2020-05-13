# app/services/peca_amblecoins_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_olympics_model import Olympics, Student
from app.schemas.peca_olympics_schema import OlympicsSchema, StudentSchema
from app.helpers.error_helpers import RegisterNotFound


class OlympicsService():

    def getOlympics(self, pecaId, lapse):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = OlympicsSchema()
            olympics = peca['lapse{}'.format(
                lapse)].olympics
            return schema.dump(olympics), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def saveStudent(self, pecaId, lapse, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = StudentSchema()

                if not peca['lapse{}'.format(lapse)].olympics:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"olympics lapse: ": lapse})
                if "section" in jsonData:
                    section = peca.school.sections.filter(
                        id=jsonData['section'], isDeleted=False).first()
                    if not section:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"section: ": jsonData["section"]})
                if "student" in jsonData and section:
                    student = section.students.filter(
                        id=jsonData['student']).first()
                    if not student:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"student: ": jsonData["student"]})
                    jsonData['id'] = str(student.id)
                    jsonData['name'] = student.firstName + \
                        ' ' + student.lastName
                    jsonData['section'] = {
                        "id": str(section.id),
                        "name": section.name,
                        "grade": section.grade}

                data = schema.load(jsonData)

                olympics = peca['lapse{}'.format(
                    lapse)].olympics

                student = Student()
                for field in data.keys():
                    student[field] = data[field]

                olympics['students'].append(student)
                try:
                    peca['lapse{}'.format(
                        lapse)].olympics = olympics
                    peca.save()
                    return schema.dump(olympics), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def updateStudent(self, pecaId, lapse, studentId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = StudentSchema()
                if not peca['lapse{}'.format(lapse)].olympics:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"olympics lapse: ": lapse})

                data = schema.load(jsonData, partial=True)
                record = peca['lapse{}'.format(
                    lapse)].olympics.students.filter(id=studentId).first()
                if not record:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"student: ": studentId})
                has_changed = False
                for field in data.keys():
                    if data[field] != record[field]:
                        record[field] = data[field]
                        if field == 'result' and data[field]:
                            record['status'] = '2'
                        has_changed = True
                if has_changed:
                    for student in peca['lapse{}'.format(lapse)].olympics.students:
                        if student.id == studentId:
                            student = record
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

    def deleteStudent(self, pecaId, lapse, studentId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            if not peca['lapse{}'.format(lapse)].olympics:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"olympics lapse: ": lapse})

            record = peca['lapse{}'.format(
                lapse)].olympics.students.filter(id=studentId).first()
            if not record:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"olympics lapse: ": lapse})
            found = False
            for student in peca['lapse{}'.format(lapse)].olympics.students:
                if student.id == studentId:
                    found = True
                    peca['lapse{}'.format(
                        lapse)].olympics.students.remove(student)
                    break

            if found:
                try:
                    peca.save()
                    return {"message": "Record deleted successfully"}, 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"olympics lapse: ": lapse})

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
