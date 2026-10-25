# -*- coding: utf-8 -*-
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
        Also returns the id expected at each position, used as the update
        filter: if a section or student was added or removed meanwhile, the
        positions moved and nothing is written.
        """
        updates = {}
        conditions = {}
        lapseKey = 'lapse{}'.format(lapse)
        sectionPos = {id(section): i for i, section in enumerate(peca.school.sections)}
        for section, student in changed_students:
            i = sectionPos[id(section)]
            j = next(pos for pos, st in enumerate(section.students) if st is student)
            updates['school.sections.{}.students.{}.{}'.format(i, j, lapseKey)] = \
                student[lapseKey].to_mongo()
            conditions['school.sections.{}.students.{}.id'.format(i, j)] = student.id
        for i, section in enumerate(peca.school.sections):
            if section.id in affected_sections:
                updates['school.sections.{}.diagnostics'.format(i)] = section.diagnostics.to_mongo()
                conditions['school.sections.{}.id'.format(i)] = section.id
        updates['school.diagnostics'] = peca.school.diagnostics.to_mongo()
        return updates, conditions

    def _importRowInfo(self, row, student_f, reason):
        return {
            "fila": row,
            "nombre": student_f.get("nombre", ""),
            "apellido": student_f.get("apellido", ""),
            "grado": student_f.get("grado", ""),
            "seccion": student_f.get("seccion", ""),
            "motivo": reason,
        }

    def importData(self, lapse, pecaId, students, diagnosticType):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId).only('school', 'schoolYear').first()
        if not peca:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

        affected_sections = set()
        # (section, student) whose diagnostic changed, to write only those paths
        changed_students = []
        # Rows that don't match the school records, reported back instead of skipped silently
        notFound = []

        for index, student_f in enumerate(students):
            # Spreadsheet row sent by the client; fallback: header in row 1
            row = student_f.get("fila") or index + 2
            section = peca.school.sections.filter(
                grade=student_f["grado"], name=student_f["seccion"], isDeleted=False).first()
            if not section:
                notFound.append(self._importRowInfo(
                    row, student_f, u'Grado y sección no encontrados'))
                continue

            student = section.students.filter(
                firstName=student_f["nombre"], lastName=student_f["apellido"], gender=student_f["genero"], isDeleted=False).first()
            if not student:
                notFound.append(self._importRowInfo(
                    row, student_f, u'Estudiante no encontrado en la sección'))
                continue

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
            except ValidationError as err:
                # The whole load is rejected: nothing has been written yet
                return {
                    "error": "true",
                    "message": u'Fila {}: {} {} tiene un resultado inválido. No se guardó ningún resultado.'.format(
                        row, student_f.get("nombre", ""), student_f.get("apellido", "")),
                    "fila": row,
                    "errors": err.normalized_messages(),
                }, 400

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
            affected_sections.add(section.id)
            changed_students.append((section, student))

        if not changed_students:
            return {
                "error": "true",
                "message": u'Ningún estudiante del archivo coincide con los registrados en la escuela. No se guardó ningún resultado.',
                "loaded": 0,
                "notFound": notFound,
            }, 400

        for section in peca.school.sections:
            if section.id in affected_sections:
                section.refreshDiagnosticsSummary()

        peca.school.refreshDiagnosticsSummary()

        # peca.save() / schoolYear.save() diff the whole document (every section
        # and student) to find the changes, which takes minutes on big schools:
        # write only the changed diagnostics and summaries instead
        now = datetime.utcnow()
        updates, conditions = self._changedDiagnosticPaths(
            peca, lapse, changed_students, affected_sections)
        if not current_app.config.get("TESTING"):
            updates['updatedAt'] = now
        conditions['_id'] = peca.id
        result = PecaProject._get_collection().update_one(conditions, {'$set': updates})
        if result.matched_count == 0:
            return {
                "error": "true",
                "message": u'La lista de estudiantes de la escuela cambió mientras se cargaban los resultados. No se guardó ningún resultado, intente nuevamente.',
            }, 409

        update_yearbook_data_in_approval(peca)

        schoolYear = SchoolYear.objects(id=peca.schoolYear.id).only('diagnostics').first()
        schoolYear.refreshDiagnosticsSummary()
        SchoolYear._get_collection().update_one(
            {'_id': schoolYear.id},
            {'$set': {'diagnostics': schoolYear.diagnostics.to_mongo(), 'updatedAt': now}})

        loaded = len(set(id(student) for _, student in changed_students))
        return {
            "error": "false",
            "message": u'Resultados guardados exitosamente: {} estudiantes.'.format(loaded),
            "loaded": loaded,
            "notFound": notFound,
        }, 201
