# app/services/diagnostic_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_project_model import Diagnostic
from app.schemas.peca_project_schema import DiagnosticSchema
from app.helpers.error_helpers import RegisterNotFound


class DiagnosticService():

    def save(self, diagnosticType, lapse, pecaId, sectionId, studentId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False,
            school__sections__students__id=studentId,
            school__sections__students__isDeleted=False).first()

        if peca:
            try:
                if diagnosticType == "reading":
                    schema = DiagnosticSchema(only=('wordsPerMin',))
                elif diagnosticType == "math":
                    schema = DiagnosticSchema(
                        only=('multitplicationsPerMin', 'operationsPerMin'))
                data = schema.load(jsonData)

                if lapse == "1":
                    diagnostic = peca.school.sections.filter(
                        id=sectionId, isDeleted=False).first().students.filter(
                            id=studentId, isDeleted=False
                    ).first().lapse1
                elif lapse == "2":
                    diagnostic = peca.school.sections.filter(
                        id=sectionId, isDeleted=False).first().students.filter(
                            id=studentId, isDeleted=False
                    ).first().lapse2
                elif lapse == "3":
                    diagnostic = peca.school.sections.filter(
                        id=sectionId, isDeleted=False).first().students.filter(
                            id=studentId, isDeleted=False
                    ).first().lapse3

                for field in schema.dump(data).keys():
                    diagnostic[field] = data[field]

                try:
                    for section in peca.school.sections:
                        if str(section.id) == sectionId and not section.isDeleted:
                            for student in section.students:
                                if str(student.id) == studentId and not student.isDeleted:
                                    if lapse == "1":
                                        student.lapse1 = diagnostic
                                    elif lapse == "2":
                                        student.lapse2 = diagnostic
                                    elif lapse == "3":
                                        student.lapse3 = diagnostic

                                    peca.save()
                                    return schema.dump(diagnostic), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId, "studentId": studentId})

    def delete(self, diagnosticType, lapse, pecaId, sectionId, studentId):
        """
        Delete value of diagnostic
        """
        peca = PecaProject.objects.filter(
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False,
            school__sections__students__id=studentId,
            school__sections__students__isDeleted=False
        ).only('school__sections__students').first()

        if peca:

            try:
                for section in peca.school.sections:
                    if str(section.id) == sectionId and not section.isDeleted:
                        for student in section.students:
                            if str(student.id) == studentId and not student.isDeleted:
                                if lapse == "1":
                                    if diagnosticType == "reading":
                                        student.lapse1.wordsPerMin = None
                                    elif diagnosticType == "math":
                                        student.lapse1.multitplicationsPerMin = None
                                        student.lapse1.operationsPerMin = None
                                elif lapse == "2":
                                    if diagnosticType == "reading":
                                        student.lapse2.wordsPerMin = None
                                    elif diagnosticType == "math":
                                        student.lapse2.multitplicationsPerMin = None
                                        student.lapse2.operationsPerMin = None
                                elif lapse == "3":
                                    if diagnosticType == "reading":
                                        student.lapse3.wordsPerMin = None
                                    elif diagnosticType == "math":
                                        student.lapse3.multitplicationsPerMin = None
                                        student.lapse3.operationsPerMin = None
                                peca.save()
                                return "Record deleted successfully", 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId, "studentId": studentId})
