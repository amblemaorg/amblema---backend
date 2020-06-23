# app/services/diagnostic_service.py


from datetime import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.models.peca_student_model import Diagnostic
from app.schemas.peca_student_schema import DiagnosticSchema
from app.schemas.peca_section_schema import DiagnosticsSchema
from app.helpers.error_helpers import RegisterNotFound


class DiagnosticService():

    def save(self, diagnosticType, lapse, pecaId, sectionId, studentId, jsonData):

        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()

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
                    schema = DiagnosticSchema(
                        only=('wordsPerMin', 'wordsPerMinIndex', 'readingDate'))
                elif diagnosticType == "math":
                    schema = DiagnosticSchema(
                        only=(
                            'multiplicationsPerMin',
                            'multiplicationsPerMinIndex',
                            'operationsPerMin',
                            'operationsPerMinIndex',
                            'mathDate',
                            'logicDate'))
                data = schema.load(jsonData)

                grade = peca.school.sections.filter(
                    id=sectionId, isDeleted=False).first().grade
                setting = schoolYear.pecaSetting.goalSetting['grade{}'.format(
                    grade)]

                diagnostic = peca.school.sections.filter(
                    id=sectionId, isDeleted=False).first().students.filter(
                    id=studentId, isDeleted=False
                ).first()['lapse{}'.format(lapse)]

                for field in schema.dump(data).keys():
                    diagnostic[field] = data[field]

                if diagnosticType == "reading":
                    diagnostic.readingDate = datetime.utcnow()
                elif diagnosticType == "math":
                    if diagnostic.multiplicationsPerMin and not diagnostic.mathDate:
                        diagnostic.mathDate = datetime.utcnow()
                    if diagnostic.operationsPerMin and not diagnostic.logicDate:
                        diagnostic.logicDate = datetime.utcnow()
                diagnostic.calculateIndex(setting)

                for section in peca.school.sections:
                    if str(section.id) == sectionId and not section.isDeleted:
                        for student in section.students:
                            if str(student.id) == studentId and not student.isDeleted:
                                student['lapse{}'.format(
                                    lapse)] = diagnostic
                                section.refreshDiagnosticsSummary()
                                peca.save()
                                return {
                                    "student": schema.dump(diagnostic),
                                    "sectionSummary": DiagnosticsSchema().dump(section.diagnostics)}, 200

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
        ).only('school__sections').first()

        if peca:
            try:
                for section in peca.school.sections:
                    if str(section.id) == sectionId and not section.isDeleted:
                        for student in section.students:
                            if str(student.id) == studentId and not student.isDeleted:
                                if diagnosticType == "reading":
                                    student['lapse{}'.format(
                                        lapse)].wordsPerMin = None
                                    student['lapse{}'.format(
                                        lapse)].wordsPerMinIndex = None
                                elif diagnosticType == "math":
                                    student['lapse{}'.format(
                                        lapse)].multiplicationsPerMin = None
                                    student['lapse{}'.format(
                                        lapse)].multiplicationsPerMinIndex = None
                                    student['lapse{}'.format(
                                        lapse)].operationsPerMin = None
                                    student['lapse{}'.format(
                                        lapse)].operationsPerMinIndex = None
                                section.refreshDiagnosticsSummary()
                                peca.save()
                                return "Record deleted successfully", 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId, "studentId": studentId})
