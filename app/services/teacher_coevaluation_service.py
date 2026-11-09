# -*- coding: utf-8 -*-
# app/services/teacher_coevaluation_service.py
"""
Coevaluación Docente AmbLeMa HQS.

- El coordinador puntúa desde el PECA (una sola vez).
- El docente puntúa desde un enlace público con token (una sola vez).
- En BD solo se guarda el hash SHA-256 del token; cada envío genera uno nuevo
  e invalida el anterior, y al guardar el docente el token se elimina.
"""

import os
from datetime import datetime

from bson import ObjectId
from flask import current_app
from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError

from app.models.peca_project_model import PecaProject
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.models.teacher_coevaluation_model import (
    TeacherCoevaluation, CoevaluationTeacher, CoevaluationCoordinator)
from app.schemas.teacher_coevaluation_schema import (
    CoevaluationScoresSchema, scores_to_list, scores_to_items)
from app.helpers.coevaluation_helper import (
    get_instrument, get_level, get_level_label, school_index, sections_label,
    generate_token, hash_token, LEVELS, LEVEL_CODES, N_ITEMS,
    STATUS_LABELS, STATUS_NOT_STARTED, STATUS_COMPLETED)
from app.helpers.handler_authorization import is_admin
from app.helpers.handler_emails import send_email


PERMISSION = "teacher_coevaluation"
INVALID_LINK_MSG = u"El enlace no es válido o la coevaluación ya fue enviada."


def _error(message, status_code, **extra):
    body = {"message": message}
    body.update(extra)
    return body, status_code


def _iso(value):
    return value.isoformat() if value else None


class TeacherCoevaluationService():

    # ------------------------------------------------------------------ helpers

    def _get_peca(self, pecaId):
        if not ObjectId.is_valid(pecaId):
            return None
        return PecaProject.objects(id=pecaId, isDeleted=False).first()

    def _get_school(self, peca):
        if not peca.project or not peca.project.school or not peca.project.school.id:
            return None
        return SchoolUser.objects(id=peca.project.school.id).only(
            'id', 'name', 'code', 'teachers').first()

    def _get_teacher(self, school, teacherId):
        if not school or not ObjectId.is_valid(teacherId):
            return None
        return school.teachers.filter(id=ObjectId(teacherId)).first()

    def _is_active(self, teacher):
        return bool(teacher and not teacher.isDeleted and teacher.status == "1")

    def check_access(self, caller, peca):
        """
        Admin (por rol) o coordinador del proyecto, y el rol debe tener el
        permiso teacher_coevaluation. Devuelve None si tiene acceso.
        En TESTING sin token (caller None) no se valida, igual que jwt_required.
        """
        if caller is None and current_app.config.get("TESTING"):
            return None
        if caller is None or not caller.role:
            return _error("No authorized", 403)
        if PERMISSION not in caller.get_permissions():
            return _error("No authorized", 403)
        if is_admin(caller):
            return None
        coordinator = peca.project.coordinator if peca.project else None
        if caller.userType == "2" and coordinator and str(coordinator.id) == str(caller.id):
            return None
        return _error("No authorized", 403)

    def _refresh_snapshot(self, coevaluation, peca, school, teacher):
        """Actualiza los datos copiados mientras la coevaluación no esté completa."""
        if coevaluation.status == STATUS_COMPLETED:
            return
        coevaluation.schoolYearId = str(peca.schoolYear.id) if peca.schoolYear else None
        coevaluation.schoolYearName = peca.schoolYearName
        coevaluation.schoolId = str(school.id)
        coevaluation.schoolName = school.name
        coevaluation.schoolCode = school.code
        coevaluation.teacher = CoevaluationTeacher(
            firstName=teacher.firstName, lastName=teacher.lastName,
            cardType=teacher.cardType, cardId=teacher.cardId,
            email=teacher.email, phone=teacher.phone)
        coevaluation.sections = sections_label(peca.school.sections, teacher.id)
        coordinator = peca.project.coordinator if peca.project else None
        coevaluation.coordinator = CoevaluationCoordinator(
            id=coordinator.id if coordinator else None,
            name=coordinator.name if coordinator else None)

    def _get_or_create(self, peca, school, teacher):
        coevaluation = TeacherCoevaluation.objects(
            pecaId=str(peca.id), teacherId=str(teacher.id)).first()
        if coevaluation:
            return coevaluation
        coevaluation = TeacherCoevaluation(pecaId=str(peca.id), teacherId=str(teacher.id))
        self._refresh_snapshot(coevaluation, peca, school, teacher)
        try:
            coevaluation.save()
        except NotUniqueError:
            # Otra petición la creó en paralelo.
            coevaluation = TeacherCoevaluation.objects(
                pecaId=str(peca.id), teacherId=str(teacher.id)).first()
        return coevaluation

    def _load(self, pecaId, teacherId):
        """(peca, school, teacher) o una respuesta de error."""
        peca = self._get_peca(pecaId)
        if not peca:
            return None, _error("Peca project not found", 404, pecaId=pecaId)
        school = self._get_school(peca)
        teacher = self._get_teacher(school, teacherId)
        if not teacher:
            return None, _error("Teacher not found", 404, teacherId=teacherId)
        return (peca, school, teacher), None

    def _validate_scores(self, jsonData):
        try:
            data = CoevaluationScoresSchema().load(jsonData or {})
        except ValidationError as err:
            return None, (err.normalized_messages(), 400)
        return scores_to_list(data), None

    def _web_url(self, origin=None):
        url = os.getenv('WEB_URL') or origin or 'http://localhost:4200'
        return url.rstrip('/')

    # ------------------------------------------------------------- serializers

    def _items(self, coevaluation):
        teacherScores = coevaluation.teacherScores if coevaluation else []
        coordinatorScores = coevaluation.coordinatorScores if coevaluation else []
        averages = coevaluation.averages if coevaluation else []
        items = []
        for index in range(N_ITEMS):
            items.append({
                "number": index + 1,
                "teacher": teacherScores[index] if len(teacherScores) == N_ITEMS else None,
                "coordinator": coordinatorScores[index] if len(coordinatorScores) == N_ITEMS else None,
                "average": averages[index] if len(averages) == N_ITEMS else None,
            })
        return items

    def _results(self, coevaluation):
        status = coevaluation.status if coevaluation else STATUS_NOT_STARTED
        level = coevaluation.level if coevaluation else None
        return {
            "status": status,
            "statusLabel": STATUS_LABELS[status],
            "totalScore": coevaluation.totalScore if coevaluation else None,
            "percentage": coevaluation.percentage if coevaluation else None,
            "level": level,
            "levelLabel": get_level_label(level),
        }

    def _detail(self, peca, school, teacher, coevaluation):
        data = {
            "id": str(coevaluation.id) if coevaluation else None,
            "instrument": get_instrument(),
            "schoolYear": {
                "id": str(peca.schoolYear.id) if peca.schoolYear else None,
                "name": peca.schoolYearName,
            },
            "school": {"id": str(school.id), "name": school.name, "code": school.code},
            "teacher": {
                "id": str(teacher.id),
                "firstName": teacher.firstName,
                "lastName": teacher.lastName,
                "cardType": teacher.cardType,
                "cardId": teacher.cardId,
                "email": teacher.email,
                "phone": teacher.phone,
                "status": teacher.status,
                "isDeleted": teacher.isDeleted,
            },
            "sections": sections_label(peca.school.sections, teacher.id),
            "coordinator": {
                "id": peca.project.coordinator.id if peca.project and peca.project.coordinator else None,
                "name": peca.project.coordinator.name if peca.project and peca.project.coordinator else None,
            },
            "items": self._items(coevaluation),
            "coordinatorSubmittedAt": _iso(coevaluation.coordinatorSubmittedAt) if coevaluation else None,
            "teacherSubmittedAt": _iso(coevaluation.teacherSubmittedAt) if coevaluation else None,
            "emailSentAt": _iso(coevaluation.emailSentAt) if coevaluation else None,
            "emailSentTo": coevaluation.emailSentTo if coevaluation else None,
            "emailSentCount": coevaluation.emailSentCount if coevaluation else 0,
            "canEvaluate": self._is_active(teacher) and not (coevaluation and coevaluation.coordinatorSubmittedAt),
            "canSendLink": self._is_active(teacher) and bool(teacher.email)
            and not (coevaluation and coevaluation.teacherSubmittedAt),
        }
        if coevaluation and coevaluation.status == STATUS_COMPLETED:
            # Ya cerrada: se muestran los datos con que se evaluó.
            data["sections"] = coevaluation.sections
            data["coordinator"] = {"id": coevaluation.coordinator.id,
                                   "name": coevaluation.coordinator.name}
        data.update(self._results(coevaluation))
        return data

    # --------------------------------------------------------------- PECA (JWT)

    def get_statuses(self, pecaId, caller=None):
        peca = self._get_peca(pecaId)
        if not peca:
            return _error("Peca project not found", 404, pecaId=pecaId)
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        records = []
        for coevaluation in TeacherCoevaluation.objects(pecaId=str(peca.id)):
            record = {"teacherId": coevaluation.teacherId}
            record.update(self._results(coevaluation))
            records.append(record)
        return {"records": records}, 200

    def get_detail(self, pecaId, teacherId, caller=None):
        loaded, error = self._load(pecaId, teacherId)
        if error:
            return error
        peca, school, teacher = loaded
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        coevaluation = TeacherCoevaluation.objects(
            pecaId=str(peca.id), teacherId=str(teacher.id)).first()
        return self._detail(peca, school, teacher, coevaluation), 200

    def save_coordinator(self, pecaId, teacherId, jsonData, caller=None):
        loaded, error = self._load(pecaId, teacherId)
        if error:
            return error
        peca, school, teacher = loaded
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        if not self._is_active(teacher):
            return _error(u"El docente no está activo.", 400)
        scores, error = self._validate_scores(jsonData)
        if error:
            return error

        coevaluation = self._get_or_create(peca, school, teacher)
        if coevaluation.coordinatorSubmittedAt:
            return _error(u"La coevaluación del coordinador ya fue registrada.", 409)
        self._refresh_snapshot(coevaluation, peca, school, teacher)
        coevaluation.save()

        # Condición atómica: solo se guarda si nadie lo hizo antes.
        updated = TeacherCoevaluation.objects(
            id=coevaluation.id, coordinatorSubmittedAt=None).update_one(
            set__coordinatorScores=scores,
            set__coordinatorSubmittedAt=datetime.utcnow(),
            set__coordinatorSubmittedBy=str(caller.id) if caller else None)
        if not updated:
            return _error(u"La coevaluación del coordinador ya fue registrada.", 409)

        coevaluation.reload()
        coevaluation.save()  # clean() recalcula promedios y nivel
        return self._detail(peca, school, teacher, coevaluation), 200

    def send_link(self, pecaId, teacherId, caller=None, origin=None):
        loaded, error = self._load(pecaId, teacherId)
        if error:
            return error
        peca, school, teacher = loaded
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        if not self._is_active(teacher):
            return _error(u"El docente no está activo.", 400)
        email = (teacher.email or "").strip()
        if not email:
            return _error(u"El docente no tiene correo electrónico registrado.", 400)

        coevaluation = self._get_or_create(peca, school, teacher)
        if coevaluation.teacherSubmittedAt:
            return _error(u"El docente ya envió su coevaluación.", 409)

        previousHash = coevaluation.tokenHash
        token = generate_token()
        self._refresh_snapshot(coevaluation, peca, school, teacher)
        coevaluation.tokenHash = hash_token(token)
        coevaluation.save()

        link = u"{}/coevaluacion/{}".format(self._web_url(origin), token)
        result = self._send_email(coevaluation, email, link)
        if result is not True:
            # El enlace anterior (si lo había) sigue siendo el válido.
            coevaluation.tokenHash = previousHash
            coevaluation.save()
            current_app.logger.error(
                "Coevaluation email failed for teacher {}: {}".format(teacherId, result))
            return _error(u"No se pudo enviar el correo. Intente nuevamente.", 502)

        coevaluation.emailSentAt = datetime.utcnow()
        coevaluation.emailSentTo = email
        coevaluation.emailSentCount = (coevaluation.emailSentCount or 0) + 1
        coevaluation.save()
        return self._detail(peca, school, teacher, coevaluation), 200

    def _send_email(self, coevaluation, email, link):
        teacherName = u"{} {}".format(
            coevaluation.teacher.firstName or "", coevaluation.teacher.lastName or "").strip()
        coordinatorName = coevaluation.coordinator.name if coevaluation.coordinator else ""
        subject = u"Coevaluación Docente AmbLeMa HQS - {}".format(coevaluation.schoolName or "")
        body = u"""
        <div style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
            <h2 style="color: #81B03E;">Coevaluación Docente AmbLeMa HQS</h2>
            <p>Estimado/a <strong>{teacher}</strong>,</p>
            <p>Lo/la invitamos a completar su parte de la coevaluación docente del año escolar
            <strong>{schoolYear}</strong> en la escuela <strong>{school}</strong>, junto a su
            coordinador/a AmbLeMa <strong>{coordinator}</strong>.</p>
            <p style="margin: 25px 0;">
                <a href="{link}" style="background-color: #81B03E; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                    Realizar coevaluación
                </a>
            </p>
            <p>O copie y pegue la siguiente dirección en su navegador:</p>
            <p><a href="{link}">{link}</a></p>
            <p style="color: #666; font-size: 0.9em;"><em>Este enlace es personal y de un solo uso.
            Una vez enviada la coevaluación no se podrá modificar. Si recibe un nuevo correo,
            use solo el enlace más reciente.</em></p>
            <br>
            <p>Atentamente,</p>
            <p><strong>Fundación AmbLeMa</strong></p>
        </div>
        """.format(teacher=teacherName, schoolYear=coevaluation.schoolYearName or "",
                   school=coevaluation.schoolName or "", coordinator=coordinatorName or "",
                   link=link)
        plainTextBody = (
            u"Hola {}, complete su parte de la coevaluación docente AmbLeMa HQS ({}, {}). "
            u"Enlace personal y de un solo uso: {}").format(
                teacherName, coevaluation.schoolName or "", coevaluation.schoolYearName or "", link)
        try:
            return send_email(body, plainTextBody, subject, email)
        except Exception as e:
            return str(e)

    # ------------------------------------------------------- Enlace del docente

    def _by_token(self, token):
        if not token or len(token) > 128:
            return None
        return TeacherCoevaluation.objects(tokenHash=hash_token(token)).first()

    def get_public(self, token):
        coevaluation = self._by_token(token)
        if not coevaluation or coevaluation.teacherSubmittedAt:
            return _error(INVALID_LINK_MSG, 404)
        # Nunca se exponen los puntajes del coordinador.
        return {
            "instrument": get_instrument(),
            "schoolYear": {"name": coevaluation.schoolYearName},
            "school": {"name": coevaluation.schoolName, "code": coevaluation.schoolCode},
            "teacher": {
                "firstName": coevaluation.teacher.firstName,
                "lastName": coevaluation.teacher.lastName,
            },
            "sections": coevaluation.sections,
            "coordinator": {"name": coevaluation.coordinator.name if coevaluation.coordinator else None},
        }, 200

    def submit_public(self, token, jsonData):
        coevaluation = self._by_token(token)
        if not coevaluation or coevaluation.teacherSubmittedAt:
            return _error(INVALID_LINK_MSG, 404)
        scores, error = self._validate_scores(jsonData)
        if error:
            return error

        # Condición atómica: mismo token vigente y sin respuesta previa.
        updated = TeacherCoevaluation.objects(
            id=coevaluation.id, tokenHash=coevaluation.tokenHash,
            teacherSubmittedAt=None).update_one(
            set__teacherScores=scores,
            set__teacherSubmittedAt=datetime.utcnow(),
            unset__tokenHash=True)
        if not updated:
            return _error(INVALID_LINK_MSG, 404)

        coevaluation.reload()
        coevaluation.save()  # clean() recalcula promedios y nivel
        return {"message": u"Coevaluación enviada correctamente.",
                "teacherScores": scores_to_items(coevaluation.teacherScores)}, 200

    # --------------------------------------------------------- Reporte (admin)

    def _row(self, coevaluation=None, teacher=None, sections="", coordinatorName=None):
        """Fila de docente para el reporte, desde la coevaluación o desde SchoolUser."""
        if coevaluation:
            snapshot = coevaluation.teacher or CoevaluationTeacher()
            row = {
                "teacherId": coevaluation.teacherId,
                "firstName": snapshot.firstName,
                "lastName": snapshot.lastName,
                "cardType": snapshot.cardType,
                "cardId": snapshot.cardId,
                "email": snapshot.email,
                "phone": snapshot.phone,
                "sections": coevaluation.sections,
                "coordinator": coevaluation.coordinator.name if coevaluation.coordinator else coordinatorName,
                "coordinatorSubmittedAt": _iso(coevaluation.coordinatorSubmittedAt),
                "teacherSubmittedAt": _iso(coevaluation.teacherSubmittedAt),
                "items": self._items(coevaluation),
            }
        else:
            row = {
                "teacherId": str(teacher.id),
                "firstName": teacher.firstName,
                "lastName": teacher.lastName,
                "cardType": teacher.cardType,
                "cardId": teacher.cardId,
                "email": teacher.email,
                "phone": teacher.phone,
                "sections": sections,
                "coordinator": coordinatorName,
                "coordinatorSubmittedAt": None,
                "teacherSubmittedAt": None,
                "items": self._items(None),
            }
        row.update(self._results(coevaluation))
        return row

    def report(self, schoolYearId, schoolId=None, level=None):
        if not ObjectId.is_valid(schoolYearId):
            return _error("School year not found", 404, schoolYearId=schoolYearId)
        schoolYear = SchoolYear.objects(id=schoolYearId, isDeleted=False).first()
        if not schoolYear:
            return _error("School year not found", 404, schoolYearId=schoolYearId)
        if level and level not in LEVEL_CODES:
            return _error("Invalid level", 400, level=level)

        pecaFilter = {"schoolYear": schoolYear.id, "isDeleted": False}
        if schoolId:
            pecaFilter["project__school__id"] = schoolId
        # Sin los estudiantes embebidos en las secciones (pesados y no se usan aquí).
        pecas = PecaProject.objects(**pecaFilter).only(
            'id', 'project', 'schoolYearName',
            'school.sections.grade', 'school.sections.name',
            'school.sections.teacher', 'school.sections.isDeleted')

        coevaluationsByPeca = {}
        for coevaluation in TeacherCoevaluation.objects(
                pecaId__in=[str(peca.id) for peca in pecas]):
            coevaluationsByPeca.setdefault(coevaluation.pecaId, {})[coevaluation.teacherId] = coevaluation

        # Los docentes viven en SchoolUser sin histórico por año: los "Sin iniciar"
        # solo se listan en el año escolar activo.
        includeNotStarted = schoolYear.status == "1"
        schoolIds = [peca.project.school.id for peca in pecas
                     if peca.project and peca.project.school]
        schoolsById = {}
        for school in SchoolUser.objects(id__in=schoolIds).only('id', 'name', 'code', 'teachers'):
            schoolsById[str(school.id)] = school

        schools = []
        byLevel = dict((code, []) for code in LEVEL_CODES)
        for peca in pecas:
            if not peca.project or not peca.project.school:
                continue
            school = schoolsById.get(peca.project.school.id)
            coordinatorName = peca.project.coordinator.name if peca.project.coordinator else None
            coevaluations = coevaluationsByPeca.get(str(peca.id), {})

            rows = [self._row(coevaluation=c, coordinatorName=coordinatorName)
                    for c in coevaluations.values()]
            if includeNotStarted and school:
                for teacher in school.teachers:
                    if self._is_active(teacher) and str(teacher.id) not in coevaluations:
                        rows.append(self._row(
                            teacher=teacher, coordinatorName=coordinatorName,
                            sections=sections_label(peca.school.sections, teacher.id)))
            if not rows:
                continue

            completed = [r for r in rows if r["status"] == STATUS_COMPLETED]
            index = school_index([r["percentage"] for r in completed])
            indexLevel = None
            if index is not None:
                for lvl in LEVELS:
                    if index >= lvl["minPercentage"]:
                        indexLevel = lvl["code"]
                        break
            schoolInfo = {
                "schoolId": peca.project.school.id,
                "name": school.name if school else peca.project.school.name,
                "code": school.code if school else peca.project.school.code,
                "pecaId": str(peca.id),
                "coordinator": coordinatorName,
            }
            levelCounts = dict((code, 0) for code in LEVEL_CODES)
            statusCounts = dict((code, 0) for code in STATUS_LABELS)
            for row in rows:
                statusCounts[row["status"]] += 1
                if row["level"]:
                    levelCounts[row["level"]] += 1

            for row in completed:
                if not level or row["level"] == level:
                    entry = dict(row)
                    entry["school"] = schoolInfo
                    byLevel[row["level"]].append(entry)

            visibleRows = [r for r in rows if not level or r["level"] == level]
            if level and not visibleRows:
                continue
            visibleRows.sort(key=lambda r: (
                -(r["percentage"] if r["percentage"] is not None else -1),
                (r["lastName"] or "").lower(), (r["firstName"] or "").lower()))

            summary = dict(schoolInfo)
            summary.update({
                "nTeachers": len(rows),
                "nCompleted": len(completed),
                "index": index,
                "indexLevel": indexLevel,
                "indexLevelLabel": get_level_label(indexLevel),
                "levelCounts": levelCounts,
                "statusCounts": statusCounts,
                "teachers": visibleRows,
            })
            schools.append(summary)

        schools.sort(key=lambda s: (s["name"] or "").lower())
        levels = []
        for lvl in LEVELS:
            if level and lvl["code"] != level:
                continue
            teachers = byLevel[lvl["code"]]
            teachers.sort(key=lambda r: (-r["percentage"], (r["lastName"] or "").lower()))
            levels.append({"code": lvl["code"], "label": lvl["label"],
                           "count": len(teachers), "teachers": teachers})

        return {
            "schoolYear": {"id": str(schoolYear.id), "name": schoolYear.name,
                           "status": schoolYear.status},
            "instrument": get_instrument(),
            "statusLabels": STATUS_LABELS,
            "bySchool": schools,
            "byLevel": levels,
        }, 200
