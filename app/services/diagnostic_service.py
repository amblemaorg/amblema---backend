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
from app.helpers.peca_yearbook_helper import update_yearbook_data_in_approval


class DiagnosticService():

    def save(self, diagnosticType, lapse, pecaId, sectionId, studentId, jsonData):

        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId).first()

        if peca:
            section = peca.school.sections.filter(
                id=sectionId, isDeleted=False).first()
            if section:
                student = section.students.filter(
                    id=studentId, isDeleted=False).first()
                if student:
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

                        grade = section.grade
                        setting = schoolYear.pecaSetting.goalSetting['grade{}'.format(
                            grade)]

                        diagnostic = student['lapse{}'.format(lapse)]

                        for field in schema.dump(data).keys():
                            diagnostic[field] = data[field]

                        if diagnosticType == "reading":
                            diagnostic.readingDate = datetime.utcnow()
                        elif diagnosticType == "math":
                            if diagnostic.multiplicationsPerMin != None and not diagnostic.mathDate:
                                diagnostic.mathDate = datetime.utcnow()
                            if diagnostic.operationsPerMin != None and not diagnostic.logicDate:
                                diagnostic.logicDate = datetime.utcnow()
                        diagnostic.calculateIndex(setting)
                        section.refreshDiagnosticsSummary()
                        peca.school.refreshDiagnosticsSummary()
                        update_yearbook_data_in_approval(peca)
                        peca.save()
                        schoolYear = peca.schoolYear.fetch()
                        schoolYear.refreshDiagnosticsSummary()
                        schoolYear.save()
                        return {
                            "student": schema.dump(diagnostic),
                            "sectionSummary": DiagnosticsSchema().dump(section.diagnostics)}, 200

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
        ).only('school__sections', 'school__diagnostics', 'schoolYear').first()

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
                                peca.school.refreshDiagnosticsSummary()
                                update_yearbook_data_in_approval(peca)
                                peca.school.diagnostics.lapse1.wordsPerMinIndex = 0
                                peca.save()
                                schoolYear = peca.schoolYear.fetch()
                                schoolYear.refreshDiagnosticsSummary()
                                schoolYear.save()
                                return "Record deleted successfully", 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId, "studentId": studentId})

    def _changedDiagnosticPaths(self, peca, lapse, changed_students, affected_sections):
        """
        $set paths for the imported diagnostics: each changed student's lapse,
        the summary of the affected sections and the school summary. Positions
        are resolved by identity on the loaded document.
        """
        updates = {}
        lapseKey = 'lapse{}'.format(lapse)
        sectionPos = {id(section): i for i, section in enumerate(peca.school.sections)}
        for section, student in changed_students:
            i = sectionPos[id(section)]
            j = next(pos for pos, st in enumerate(section.students) if st is student)
            updates['school.sections.{}.students.{}.{}'.format(i, j, lapseKey)] = \
                student[lapseKey].to_mongo()
        for i, section in enumerate(peca.school.sections):
            if section.id in affected_sections:
                updates['school.sections.{}.diagnostics'.format(i)] = section.diagnostics.to_mongo()
        updates['school.diagnostics'] = peca.school.diagnostics.to_mongo()
        return updates

    def importData(self, lapse, pecaId, students, diagnosticType):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId).only('school', 'schoolYear').first()
        
        affected_sections = set()
        # (section, student) whose diagnostic changed, to write only those paths
        changed_students = []

        if peca:
            for student_f in students:
                section = peca.school.sections.filter(
                    grade=student_f["grado"], name=student_f["seccion"], isDeleted=False).first()
                if section:
                    affected_sections.add(section.id)

                    student = section.students.filter(
                    firstName=student_f["nombre"], lastName=student_f["apellido"], gender=student_f["genero"], isDeleted=False).first()
                    if student:
                        try:
                            jsonData = {}
                            if diagnosticType == "reading":
                                schema = DiagnosticSchema(
                                    only=('wordsPerMin', 'wordsPerMinIndex', 'readingDate'))
                                jsonData = {
                                    "wordsPerMin": student_f["resultado"] if student_f["resultado"] != '' else None, 
                                }
                            elif diagnosticType == "math":
                                schema = DiagnosticSchema(
                                    only=(
                                        'multiplicationsPerMin',
                                        'multiplicationsPerMinIndex',
                                        'operationsPerMin',
                                        'operationsPerMinIndex',
                                        'mathDate',
                                        'logicDate'))
                                jsonData = {
                                    "multiplicationsPerMin": student_f["resultado_mult"].strip() if student_f["resultado_mult"].strip() != '' else None, 
                                    "operationsPerMin": student_f["resultado_log"].strip() if student_f["resultado_log"].strip() != '' else None, 
                                }
                                
                            data = schema.load(jsonData)
                            grade = section.grade
                            setting = schoolYear.pecaSetting.goalSetting['grade{}'.format(
                                grade)]

                            diagnostic = student['lapse{}'.format(lapse)]

                            for field in schema.dump(data).keys():
                                diagnostic[field] = data[field]
                            
                            if diagnosticType == "reading":
                                diagnostic.readingDate = datetime.utcnow()
                            elif diagnosticType == "math":
                                if diagnostic.multiplicationsPerMin != None and not diagnostic.mathDate:
                                    diagnostic.mathDate = datetime.utcnow()
                                if diagnostic.operationsPerMin != None and not diagnostic.logicDate:
                                    diagnostic.logicDate = datetime.utcnow()
                            diagnostic.calculateIndex(setting)
                            changed_students.append((section, student))

                        except ValidationError as err:
                            return err.normalized_messages(), 400

            for section in peca.school.sections:
                if section.id in affected_sections:
                    section.refreshDiagnosticsSummary()

            peca.school.refreshDiagnosticsSummary()
            update_yearbook_data_in_approval(peca)

            # peca.save() / schoolYear.save() diff the whole document (every section
            # and student) to find the changes, which takes minutes on big schools:
            # write only the changed diagnostics and summaries instead
            now = datetime.utcnow()
            updates = self._changedDiagnosticPaths(peca, lapse, changed_students, affected_sections)
            if not current_app.config.get("TESTING"):
                updates['updatedAt'] = now
            PecaProject._get_collection().update_one({'_id': peca.id}, {'$set': updates})

            schoolYear = SchoolYear.objects(id=peca.schoolYear.id).only('diagnostics').first()
            schoolYear.refreshDiagnosticsSummary()
            SchoolYear._get_collection().update_one(
                {'_id': schoolYear.id},
                {'$set': {'diagnostics': schoolYear.diagnostics.to_mongo(), 'updatedAt': now}})

            return {"error": "false", "message": "Resutados guardados exitosamente"},201