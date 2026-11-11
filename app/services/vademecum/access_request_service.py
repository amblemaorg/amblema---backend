# -*- coding: utf-8 -*-
# app/services/vademecum/access_request_service.py
"""Solicitudes de acceso y autorizaciones por año escolar (API-05, GES-03 5.2).

Quien no está en la matrícula pide acceso sin cuenta. Al aprobar se crea (o reutiliza) la
cuenta y la autorización del año vigente: el docente queda como "Externo" y la autorización
vence sola cuando cambia el año vigente (se busca siempre por el año, no se borra).
"""

import math
import re
from datetime import datetime

from flask import current_app
from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError

from app.helpers.handler_emails import send_email
from app.models.school_year_model import SchoolYear
from app.models.vademecum import (
    VademecumAccessRequest, VademecumAuthorization, VademecumTeacherAccount)
from app.models.vademecum.constants import REQUEST_STATUSES
from app.schemas.vademecum.access_schema import AccessRequestSchema, RejectSchema
from app.services.vademecum.account_service import error, isoformat, send_verification
from app.services.vademecum.catalog_service import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, invalid, not_found, object_id)
from app.services.vademecum.enrollment_service import EnrollmentService, normalize_email
from app.services.vademecum.recaptcha_service import recaptcha_is_valid

ALREADY_REQUESTED = ("email", "107", "Pending request or authorization already exists", 409)
ALREADY_REVIEWED = ("general", "118", "Request already reviewed", 409)
MAX_QUERY_LENGTH = 100


def _ref(document, **fields):
    return dict({"id": str(document.id)}, **fields) if document else None


def _user_ref(user):
    return _ref(user, name=getattr(user, "name", None)) if user else None


def _year_ref(year):
    return _ref(year, name=year.name) if year else None


def request_dict(accessRequest):
    return {
        "id": str(accessRequest.id),
        "firstName": accessRequest.firstName, "lastName": accessRequest.lastName,
        "email": accessRequest.email, "cardId": accessRequest.cardId,
        "phone": accessRequest.phone, "institution": accessRequest.institution,
        "schoolYear": _year_ref(accessRequest.schoolYear),
        "status": accessRequest.status, "rejectionReason": accessRequest.rejectionReason,
        "reviewedBy": _user_ref(accessRequest.reviewedBy),
        "reviewedAt": isoformat(accessRequest.reviewedAt),
        "createdAt": isoformat(accessRequest.createdAt),
    }


def authorization_dict(authorization):
    account = authorization.account
    return {
        "id": str(authorization.id),
        "account": _ref(account, email=account.email, firstName=account.firstName,
                        lastName=account.lastName) if account else None,
        "schoolYear": _year_ref(authorization.schoolYear),
        "accessRequestId": (str(authorization.accessRequest.id)
                            if authorization.accessRequest else None),
        "approvedBy": _user_ref(authorization.approvedBy),
        "approvedAt": isoformat(authorization.approvedAt),
        "revokedAt": isoformat(authorization.revokedAt),
    }


def _page_args(args):
    try:
        page = int(args.get("page") or 1)
        pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
    except ValueError:
        return None, None, invalid("page")
    if page < 1 or not 1 <= pageSize <= MAX_PAGE_SIZE:
        return None, None, invalid("pageSize" if page >= 1 else "page")
    return page, pageSize, None


def _page(queryset, page, pageSize, serializer):
    total = queryset.count()
    records = queryset.skip((page - 1) * pageSize).limit(pageSize)
    return {"records": [serializer(r) for r in records],
            "pagination": {"page": page, "pageSize": pageSize, "total": total,
                           "pages": int(math.ceil(float(total) / pageSize))}}, 200


def notify(email, firstName, subject, paragraphs):
    """Correo sin enlace de token; un fallo se registra y no rompe la revisión."""
    html = u"<p>Hola {},</p>{}<p>Vademécum AmbLeMa</p>".format(
        firstName or u"", u"".join(u"<p>{}</p>".format(p) for p in paragraphs))
    text = u"Hola {},\n\n{}\n\nVademécum AmbLeMa".format(firstName or u"",
                                                         u"\n\n".join(paragraphs))
    try:
        result = send_email(html, text, subject, email)
    except Exception:
        current_app.logger.exception("Vademecum: access request email failed")
        return False
    if result is not True:
        current_app.logger.error("Vademecum: access request email failed: %s", result)
        return False
    return True


class AccessRequestService(object):

    def __init__(self, enrollmentService=None):
        self.enrollment = enrollmentService or EnrollmentService()

    # --- Pública ---

    def create(self, jsonData):
        try:
            data = AccessRequestSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not recaptcha_is_valid(data.get("recaptchaToken")):
            return error("general", "105", "Invalid reCAPTCHA")
        schoolYear = self.enrollment.current_school_year()
        if not schoolYear:
            return error("general", "117", "No current school year", 409)

        email = normalize_email(data["email"])
        if self.enrollment.resolve(email, schoolYear).is_enrolled:
            return error("email", "106", "Email is in the current enrollment", 409)
        account = VademecumTeacherAccount.objects(email=email, isDeleted=False).first()
        if account and VademecumAuthorization.objects(
                account=account.id, schoolYear=schoolYear.id, revokedAt=None).first():
            return error(*ALREADY_REQUESTED)

        accessRequest = VademecumAccessRequest(
            email=email, firstName=data["firstName"], lastName=data["lastName"],
            cardId=data["cardId"] or None, phone=data["phone"] or None,
            institution=data["institution"], schoolYear=schoolYear)
        try:
            accessRequest.save()
        except NotUniqueError:  # ya hay una pendiente de ese email en el año
            return error(*ALREADY_REQUESTED)
        return {"id": str(accessRequest.id), "status": accessRequest.status}, 201

    # --- Backoffice ---

    def get(self, requestId):
        requestId = object_id(requestId)
        return requestId and VademecumAccessRequest.objects(id=requestId).first()

    def list(self, args):
        query = {}
        status = args.get("status")
        if status:
            if status not in REQUEST_STATUSES:
                return invalid("status")
            query["status"] = status
        if args.get("schoolYearId"):
            query["schoolYear"] = object_id(args.get("schoolYearId"))
            if not query["schoolYear"]:
                return invalid("schoolYearId")
        q = (args.get("q") or "").strip()
        if len(q) > MAX_QUERY_LENGTH:
            return {"q": [{"status": "13", "msg": "Invalid length"}]}, 400
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        requests = VademecumAccessRequest.objects(**query)
        if q:
            pattern = {"$regex": re.escape(q), "$options": "i"}
            requests = requests.filter(__raw__={"$or": [
                {"firstName": pattern}, {"lastName": pattern}, {"email": pattern},
                {"cardId": pattern}]})
        # Las pendientes se atienden por orden de llegada
        requests = requests.order_by("createdAt" if status == "pending" else "-createdAt")
        return _page(requests, page, pageSize, request_dict)

    def _review(self, accessRequest, admin, status, **fields):
        """pending → status de forma atómica; None si ya estaba revisada."""
        now = datetime.utcnow()
        updates = {"set__" + k: v for k, v in fields.items()}
        return VademecumAccessRequest.objects(id=accessRequest.id, status="pending").modify(
            new=True, set__status=status, set__reviewedBy=admin, set__reviewedAt=now,
            set__updatedAt=now, **updates)

    def approve(self, accessRequest, admin):
        reviewed = self._review(accessRequest, admin, "approved")
        if not reviewed:
            return error(*ALREADY_REVIEWED)
        account = self._account_for(reviewed)
        self._authorize(account, reviewed, admin)
        reviewed.update(set__account=account)
        reviewed.reload()

        if account.status == "pending":
            # Crea su contraseña desde el enlace (mismo correo que el registro)
            send_verification(account)
        else:
            notify(account.email, account.firstName,
                   u"Tu acceso al Vademécum AmbLeMa fue aprobado",
                   [u"Tu solicitud de acceso fue aprobada para el año escolar {}.".format(
                       reviewed.schoolYear.name),
                    u"Ya puedes iniciar sesión con tu cuenta y descargar las fichas."])
        return request_dict(reviewed), 200

    def _account_for(self, accessRequest):
        account = VademecumTeacherAccount.objects(email=accessRequest.email).first()
        if not account:
            account = VademecumTeacherAccount(
                email=accessRequest.email, firstName=accessRequest.firstName,
                lastName=accessRequest.lastName, status="pending")
            try:
                account.save()
            except NotUniqueError:  # se registró a la vez: se usa esa cuenta
                account = VademecumTeacherAccount.objects(email=accessRequest.email).first()
        elif account.isDeleted:
            account.update(set__isDeleted=False, set__status="pending", set__password=None)
            account.reload()
        return account

    def _authorize(self, account, accessRequest, admin):
        now = datetime.utcnow()
        # Una autorización por cuenta y año (índice único): si estaba revocada, se renueva
        VademecumAuthorization.objects(account=account.id,
                                       schoolYear=accessRequest.schoolYear.id).update_one(
            upsert=True, set__accessRequest=accessRequest, set__approvedBy=admin,
            set__approvedAt=now, set__revokedAt=None, set__updatedAt=now,
            set_on_insert__createdAt=now)

    def reject(self, accessRequest, jsonData, admin):
        try:
            data = RejectSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        reviewed = self._review(accessRequest, admin, "rejected",
                                rejectionReason=data["reason"])
        if not reviewed:
            return error(*ALREADY_REVIEWED)
        notify(reviewed.email, reviewed.firstName,
               u"Tu solicitud de acceso al Vademécum AmbLeMa",
               [u"Revisamos tu solicitud de acceso y no pudimos aprobarla.",
                u"Motivo: {}".format(data["reason"])])
        return request_dict(reviewed), 200

    # --- Autorizaciones ---

    def list_authorizations(self, args):
        schoolYearId = args.get("schoolYearId")
        if schoolYearId:
            schoolYear = object_id(schoolYearId) and SchoolYear.objects(
                id=object_id(schoolYearId)).first()
            if not schoolYear:
                return invalid("schoolYearId")
        else:
            schoolYear = self.enrollment.current_school_year()
            if not schoolYear:
                return {"records": [], "pagination": {"page": 1, "pageSize": DEFAULT_PAGE_SIZE,
                                                      "total": 0, "pages": 0}}, 200
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        authorizations = VademecumAuthorization.objects(
            schoolYear=schoolYear.id).order_by("-approvedAt")
        return _page(authorizations, page, pageSize, authorization_dict)

    def get_authorization(self, authorizationId):
        authorizationId = object_id(authorizationId)
        return authorizationId and VademecumAuthorization.objects(id=authorizationId).first()

    def revoke(self, authorization):
        if not authorization.revokedAt:
            authorization.revokedAt = datetime.utcnow()
            authorization.save()
        return authorization_dict(authorization), 200


def with_record(record, action):
    return action(record) if record else not_found()
