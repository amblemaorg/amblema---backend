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
from app.models.state_model import State
from app.models.teacher_coevaluation_model import (
    TeacherCoevaluation, CoevaluationTeacher, CoevaluationCoordinator)
from app.schemas.teacher_coevaluation_schema import (
    CoevaluationScoresSchema, scores_to_list, scores_to_items)
from app.helpers.coevaluation_helper import (
    get_instrument, get_level, get_level_label, school_index, sections_label,
    generate_token, hash_token, field_value, coevaluation_status, LEVELS, LEVEL_CODES,
    N_ITEMS, STATUS_LABELS, STATUS_NOT_STARTED, STATUS_COMPLETED)
from app.helpers.handler_authorization import is_admin
from app.helpers.handler_emails import send_email


PERMISSION = "teacher_coevaluation"
INVALID_LINK_MSG = u"El enlace no es válido o la coevaluación ya fue enviada."

# Campos del PECA que usa cada operación: el documento completo trae las secciones
# con sus estudiantes embebidos (cientos de KB) y aquí no se usan.
PECA_ACCESS_FIELDS = ('id', 'project')
PECA_EVALUATION_FIELDS = (
    'id', 'project', 'schoolYear', 'schoolYearName',
    'school.sections.grade', 'school.sections.name',
    'school.sections.teacher', 'school.sections.isDeleted')
# Campos de la coevaluación para el reporte (sin token ni datos de envío de correo).
REPORT_COEVALUATION_FIELDS = (
    'pecaId', 'teacherId', 'teacher', 'sections', 'coordinator',
    'coordinatorSubmittedAt', 'teacherSubmittedAt',
    'teacherScores', 'coordinatorScores', 'averages', 'totalScore', 'percentage', 'level')
REPORT_TEACHER_FIELDS = tuple('teachers.' + name for name in (
    'id', 'firstName', 'lastName', 'cardType', 'cardId', 'email', 'phone', 'status', 'isDeleted'))


def _error(message, status_code, **extra):
    body = {"message": message}
    body.update(extra)
    return body, status_code


def _iso(value):
    return value.isoformat() if value else None


class TeacherCoevaluationService():

    # ------------------------------------------------------------------ helpers

    def _get_peca(self, pecaId, fields):
        if not ObjectId.is_valid(pecaId):
            return None
        return PecaProject.objects(id=pecaId, isDeleted=False).only(*fields).first()

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
        """Docente activo; acepta el documento o el dict crudo (defaults del modelo Teacher)."""
        return bool(teacher and not field_value(teacher, "isDeleted", False)
                    and field_value(teacher, "status", "1") == "1")

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
        peca = self._get_peca(pecaId, PECA_EVALUATION_FIELDS)
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
        url = (os.getenv('WEB_URL') or origin
               or current_app.config.get('WEB_URL') or 'http://localhost:2005')
        return url.rstrip('/')

    # ------------------------------------------------------------- serializers

    def _items(self, coevaluation):
        """coevaluation: documento, dict crudo o None."""
        teacherScores = field_value(coevaluation, "teacherScores") or []
        coordinatorScores = field_value(coevaluation, "coordinatorScores") or []
        averages = field_value(coevaluation, "averages") or []
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
        """coevaluation: documento, dict crudo o None."""
        status = coevaluation_status(
            field_value(coevaluation, "teacherSubmittedAt"),
            field_value(coevaluation, "coordinatorSubmittedAt")) if coevaluation else STATUS_NOT_STARTED
        level = field_value(coevaluation, "level")
        return {
            "status": status,
            "statusLabel": STATUS_LABELS[status],
            "totalScore": field_value(coevaluation, "totalScore"),
            "percentage": field_value(coevaluation, "percentage"),
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
        peca = self._get_peca(pecaId, PECA_ACCESS_FIELDS)
        if not peca:
            return _error("Peca project not found", 404, pecaId=pecaId)
        denied = self.check_access(caller, peca)
        if denied:
            return denied
        records = []
        for coevaluation in TeacherCoevaluation.objects(pecaId=str(peca.id)).only(
                'teacherId', 'teacherSubmittedAt', 'coordinatorSubmittedAt',
                'totalScore', 'percentage', 'level'):
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
        coordinatorName = (
            coevaluation.coordinator.name
            if coevaluation.coordinator and coevaluation.coordinator.name else u"Por asignar")
        schoolLabel = u"{}{}".format(
            coevaluation.schoolName or "",
            u" ({})".format(coevaluation.schoolCode) if coevaluation.schoolCode else u"")
        sectionsLabel = coevaluation.sections or u"Sin sección asignada"
        schoolYearLabel = coevaluation.schoolYearName or u""
        subject = u"Coevaluación Docente AmbLeMa HQS - {}".format(coevaluation.schoolName or "")
        body = u"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coevaluación Docente AmbLeMa HQS</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: 'Montserrat', 'Segoe UI', Arial, Helvetica, sans-serif; color: #1c3135; -webkit-font-smoothing: antialiased;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f7f6; padding: 28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #ffffff; border: 1px solid #d7e2e4; border-radius: 12px; overflow: hidden;">
          <!-- Encabezado azul PECA con filete inferior verde AmbLeMa -->
          <tr>
            <td style="background-color: #00809a; border-bottom: 4px solid #81b03e; padding: 26px 32px;">
              <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #cce7ed;">
                Fundación AmbLeMa · Instrumento HQS
              </p>
              <h1 style="margin: 0; font-size: 22px; line-height: 1.3; font-weight: 700; color: #ffffff;">
                Coevaluación Docente AmbLeMa HQS
              </h1>
              <p style="margin: 8px 0 0 0; font-size: 13px; color: #e2f2f5;">
                Año escolar <strong>{schoolYear}</strong>
              </p>
            </td>
          </tr>

          <!-- Contenido principal -->
          <tr>
            <td style="padding: 30px 32px 24px 32px;">
              <p style="margin: 0 0 14px 0; font-size: 16px; line-height: 1.5; color: #00353a;">
                Estimado/a <strong>{teacher}</strong>,
              </p>
              <p style="margin: 0 0 22px 0; font-size: 14px; line-height: 1.65; color: #364f54;">
                Lo/la invitamos a completar su parte de la <strong>Coevaluación Docente AmbLeMa HQS</strong>.
                Este instrumento consta de <strong>15 prácticas pedagógicas</strong> valoradas en una escala de
                <strong>0 a 5</strong>; su coordinador/a AmbLeMa realizará la misma valoración para luego
                conversar juntos sobre los resultados.
              </p>

              <!-- Tarjeta de datos del docente y la escuela -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f7f6; border: 1px solid #d7e2e4; border-left: 4px solid #00809a; border-radius: 8px; margin: 0 0 26px 0;">
                <tr>
                  <td style="padding: 16px 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                      <tr>
                        <td style="padding: 4px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #5b7278; width: 38%; vertical-align: top;">
                          Escuela
                        </td>
                        <td style="padding: 4px 0; font-size: 14px; font-weight: 600; color: #00353a; vertical-align: top;">
                          {school}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding: 4px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #5b7278; vertical-align: top;">
                          Grado / Sección
                        </td>
                        <td style="padding: 4px 0; font-size: 14px; color: #1c3135; vertical-align: top;">
                          {sections}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding: 4px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #5b7278; vertical-align: top;">
                          Año escolar
                        </td>
                        <td style="padding: 4px 0; font-size: 14px; color: #1c3135; vertical-align: top;">
                          {schoolYear}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding: 4px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #5b7278; vertical-align: top;">
                          Coordinador/a
                        </td>
                        <td style="padding: 4px 0; font-size: 14px; color: #1c3135; vertical-align: top;">
                          {coordinator}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Botón principal -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin: 0 0 26px 0;">
                <tr>
                  <td align="center">
                    <a href="{link}" target="_blank" rel="noopener noreferrer" style="background-color: #81b03e; color: #ffffff; font-size: 15px; font-weight: 700; text-decoration: none; padding: 14px 32px; border-radius: 8px; display: inline-block; border: 1px solid #6f9a33;">
                      Realizar coevaluación
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Indicaciones importantes -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f9fbfa; border: 1px solid #d7e2e4; border-radius: 8px; margin: 0 0 22px 0;">
                <tr>
                  <td style="padding: 14px 18px; font-size: 13px; line-height: 1.55; color: #4a6268;">
                    <strong style="color: #00353a; display: block; margin-bottom: 4px;">Importante antes de comenzar:</strong>
                    • Este enlace es <strong>personal y de un solo uso</strong>.<br>
                    • Una vez enviada la coevaluación, las respuestas quedan registradas y no se podrán modificar.<br>
                    • Si recibe un nuevo correo, utilice únicamente el <strong>enlace más reciente</strong>.
                  </td>
                </tr>
              </table>

              <!-- Enlace directo alternativo -->
              <p style="margin: 0 0 6px 0; font-size: 12px; color: #5b7278;">
                Si el botón no abre directamente, copie y pegue este enlace en su navegador:
              </p>
              <p style="margin: 0; font-size: 12px; line-height: 1.5; word-break: break-all;">
                <a href="{link}" target="_blank" rel="noopener noreferrer" style="color: #00809a; text-decoration: underline;">{link}</a>
              </p>
            </td>
          </tr>

          <!-- Pie -->
          <tr>
            <td style="background-color: #f4f7f6; border-top: 1px solid #d7e2e4; padding: 18px 32px;">
              <p style="margin: 0 0 2px 0; font-size: 13px; font-weight: 700; color: #00353a;">
                Fundación AmbLeMa
              </p>
              <p style="margin: 0; font-size: 12px; color: #5b7278;">
                Mensaje enviado automáticamente desde la plataforma AmbLeMa.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>""".format(teacher=teacherName, schoolYear=schoolYearLabel,
                  school=schoolLabel, sections=sectionsLabel,
                  coordinator=coordinatorName, link=link)
        plainTextBody = (
            u"Hola {}, complete su parte de la coevaluación docente AmbLeMa HQS ({}, {}). "
            u"Grado / Sección: {}. Coordinador/a: {}. "
            u"Enlace personal y de un solo uso: {}").format(
                teacherName, schoolLabel, schoolYearLabel, sectionsLabel, coordinatorName, link)
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
        """
        Fila de docente para el reporte, desde la coevaluación o desde SchoolUser.
        Ambos llegan como dicts crudos (as_pymongo).
        """
        if coevaluation:
            snapshot = coevaluation.get("teacher") or {}
            coordinator = coevaluation.get("coordinator")
            row = {
                "teacherId": coevaluation.get("teacherId"),
                "firstName": snapshot.get("firstName"),
                "lastName": snapshot.get("lastName"),
                "cardType": snapshot.get("cardType"),
                "cardId": snapshot.get("cardId"),
                "email": snapshot.get("email"),
                "phone": snapshot.get("phone"),
                "sections": coevaluation.get("sections", ""),
                "coordinator": coordinator.get("name") if coordinator else coordinatorName,
                "coordinatorSubmittedAt": _iso(coevaluation.get("coordinatorSubmittedAt")),
                "teacherSubmittedAt": _iso(coevaluation.get("teacherSubmittedAt")),
                "items": self._items(coevaluation),
            }
        else:
            row = {
                "teacherId": str(teacher.get("id")),
                "firstName": teacher.get("firstName"),
                "lastName": teacher.get("lastName"),
                "cardType": teacher.get("cardType"),
                "cardId": teacher.get("cardId"),
                "email": teacher.get("email"),
                "phone": teacher.get("phone"),
                "sections": sections,
                "coordinator": coordinatorName,
                "coordinatorSubmittedAt": None,
                "teacherSubmittedAt": None,
                "items": self._items(None),
            }
        row.update(self._results(coevaluation))
        return row

    def report(self, schoolYearId, schoolId=None, level=None, stateId=None):
        if not ObjectId.is_valid(schoolYearId):
            return _error("School year not found", 404, schoolYearId=schoolYearId)
        schoolYear = SchoolYear.objects(id=schoolYearId, isDeleted=False).first()
        if not schoolYear:
            return _error("School year not found", 404, schoolYearId=schoolYearId)
        if level and level not in LEVEL_CODES:
            return _error("Invalid level", 400, level=level)
        if stateId and not ObjectId.is_valid(stateId):
            return _error("State not found", 404, stateId=stateId)

        pecaFilter = {"schoolYear": schoolYear.id, "isDeleted": False}
        if schoolId:
            pecaFilter["project__school__id"] = schoolId
        if stateId:
            pecaFilter["school__addressState"] = ObjectId(stateId)
        # Lectura cruda (as_pymongo) y solo los campos usados: construir documentos
        # MongoEngine y dereferenciar las referencias de cada docente era el grueso del tiempo.
        pecas = list(PecaProject.objects(**pecaFilter).only(
            'id', 'project.school', 'project.coordinator', 'school.addressState',
            'school.sections.grade', 'school.sections.name',
            'school.sections.teacher', 'school.sections.isDeleted').as_pymongo())

        coevaluationsByPeca = {}
        for coevaluation in TeacherCoevaluation.objects(
                pecaId__in=[str(peca["_id"]) for peca in pecas]).only(
                *REPORT_COEVALUATION_FIELDS).as_pymongo():
            coevaluationsByPeca.setdefault(coevaluation["pecaId"], {})[coevaluation["teacherId"]] = coevaluation

        # Los docentes viven en SchoolUser sin histórico por año: los "Sin iniciar"
        # solo se listan en el año escolar activo.
        includeNotStarted = schoolYear.status == "1"
        schoolIds = [peca["project"]["school"]["id"] for peca in pecas
                     if (peca.get("project") or {}).get("school")]
        statesById = dict((str(state.id), {"id": str(state.id), "name": state.name})
                          for state in State.objects(isDeleted=False).only('id', 'name'))

        schoolsById = {}
        for school in SchoolUser.objects(id__in=schoolIds).only(
                'id', 'name', 'code', *REPORT_TEACHER_FIELDS).as_pymongo():
            schoolsById[str(school["_id"])] = school

        schools = []
        byLevel = dict((code, []) for code in LEVEL_CODES)
        for peca in pecas:
            pecaId = str(peca["_id"])
            project = peca.get("project") or {}
            projectSchool = project.get("school")
            if not projectSchool:
                continue
            pecaSchool = peca.get("school") or {}
            school = schoolsById.get(projectSchool.get("id"))
            coordinator = project.get("coordinator")
            coordinatorName = coordinator.get("name") if coordinator else None
            coevaluations = coevaluationsByPeca.get(pecaId, {})

            rows = [self._row(coevaluation=c, coordinatorName=coordinatorName)
                    for c in coevaluations.values()]
            if includeNotStarted and school:
                for teacher in school.get("teachers") or []:
                    if self._is_active(teacher) and str(teacher.get("id")) not in coevaluations:
                        rows.append(self._row(
                            teacher=teacher, coordinatorName=coordinatorName,
                            sections=sections_label(pecaSchool.get("sections"), teacher.get("id"))))
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
            source = school if school else projectSchool
            addressState = pecaSchool.get("addressState")
            schoolInfo = {
                "schoolId": projectSchool.get("id"),
                "name": source.get("name"),
                "code": source.get("code"),
                "pecaId": pecaId,
                "coordinator": coordinatorName,
                "state": statesById.get(str(addressState)) if addressState else None,
            }
            levelCounts = dict((code, 0) for code in LEVEL_CODES)
            statusCounts = dict((code, 0) for code in STATUS_LABELS)
            for row in rows:
                statusCounts[row["status"]] += 1
                if row["level"]:
                    levelCounts[row["level"]] += 1

            for row in completed:
                if not level or row["level"] == level:
                    # Sin los 15 ítems: la vista por nivel no los usa y duplicaban
                    # buena parte de la respuesta (ya van en bySchool).
                    entry = dict((key, value) for key, value in row.items() if key != "items")
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
