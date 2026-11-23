# -*- coding: utf-8 -*-
# app/services/vademecum/rating_service.py
"""Valoraciones de fichas y moderación de comentarios (API-16, GES-03 5.4).

Reglas:
- Una valoración por cuenta y ficha, editable. Solo valora quien descargó la ficha alguna vez
  (403, código 111).
- Las estrellas cuentan siempre, sin moderación (también si el comentario está oculto).
  `VademecumSheet.ratingCount` y `ratingSum` se mantienen con incrementos atómicos.
- Un comentario nuevo o editado queda `pending`; solo se publica tras aprobarlo. El
  administrador puede ocultarlo estando pendiente o ya publicado.
- Para no aprobar un texto que el moderador no vio, la moderación acepta `updatedAt` de la
  versión vista: si el docente editó después, 409 (código 120).
"""

import math
from datetime import datetime

from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError

from app.models.vademecum import (
    VademecumDownload, VademecumRating, VademecumSheet, VademecumTeacherAccount)
from app.models.vademecum.constants import COMMENT_STATUSES
from app.schemas.vademecum.rating_schema import ModerationSchema, RatingSchema
from app.services.vademecum.account_service import error
from app.services.vademecum.catalog_service import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, CatalogService, invalid, isoformat, not_found, object_id)

REQUIRES_DOWNLOAD = ("general", "111", "Download the sheet before rating it", 403)
CHANGED_SINCE_SEEN = ("general", "120", "Rating changed since it was reviewed", 409)
NO_COMMENT = ("comment", "1", "Rating has no comment to moderate")
MAX_SAVE_ATTEMPTS = 3


def _page_args(args):
    try:
        page = int(args.get("page") or 1)
        pageSize = int(args.get("pageSize") or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        return None, None, invalid("page")
    if page < 1:
        return None, None, invalid("page")
    if not 1 <= pageSize <= MAX_PAGE_SIZE:
        return None, None, invalid("pageSize")
    return page, pageSize, None


def _pagination(page, pageSize, total):
    return {"page": page, "pageSize": pageSize, "total": total,
            "pages": int(math.ceil(float(total) / pageSize))}


def author_name(account):
    """Nombre e inicial del apellido: "María P."."""
    if not account:
        return None
    lastName = (account.lastName or u"").strip()
    return u"{} {}.".format(account.firstName, lastName[0]).strip() if lastName \
        else account.firstName


def my_rating_dict(rating):
    return {"stars": rating.stars, "comment": rating.comment,
            "commentStatus": rating.commentStatus, "updatedAt": isoformat(rating.updatedAt)}


class RatingService(object):

    # --- Docente: GET/PUT /vademecum/me/ratings/{sheetId} ---

    def get_mine(self, account, sheetId):
        sheetOid = object_id(sheetId)
        rating = sheetOid and VademecumRating.objects(account=account.id, sheet=sheetOid).first()
        return (my_rating_dict(rating), 200) if rating else not_found()

    def save_mine(self, account, sheetId, jsonData):
        sheet = CatalogService().published_sheet(sheetId)
        if not sheet:
            return not_found()
        try:
            data = RatingSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not VademecumDownload.objects(__raw__={"account.id": str(account.id),
                                                  "sheet.id": str(sheet.id)}).first():
            return error(*REQUIRES_DOWNLOAD)

        # Reintenta si otra petición de la misma cuenta crea o edita la valoración a la vez
        for _ in range(MAX_SAVE_ATTEMPTS):
            rating = VademecumRating.objects(account=account.id, sheet=sheet.id).first()
            saved = (self._create(account, sheet, data) if rating is None
                     else self._update(rating, data))
            if saved:
                return my_rating_dict(saved), 200
        return error("general", "1", "Rating is being updated, try again", 409)

    def _create(self, account, sheet, data):
        rating = VademecumRating(account=account.id, sheet=sheet.id, stars=data["stars"])
        rating.set_comment(data.get("comment"))
        try:
            rating.save()
        except NotUniqueError:
            return None  # otra petición la creó: se reintenta como edición
        VademecumSheet.objects(id=sheet.id).update_one(inc__ratingCount=1,
                                                        inc__ratingSum=rating.stars)
        return rating

    def _update(self, rating, data):
        previousStars, previousUpdatedAt = rating.stars, rating.updatedAt
        rating.stars = data["stars"]
        rating.set_comment(data.get("comment"))
        now = datetime.utcnow()
        # Escritura condicionada a la versión leída: así el ajuste de ratingSum es exacto
        updated = VademecumRating.objects(id=rating.id, updatedAt=previousUpdatedAt).update_one(
            set__stars=rating.stars, set__comment=rating.comment,
            set__commentStatus=rating.commentStatus, set__moderatedBy=rating.moderatedBy,
            set__moderatedAt=rating.moderatedAt, set__updatedAt=now)
        if not updated:
            return None
        delta = rating.stars - previousStars
        if delta:
            VademecumSheet.objects(id=rating.sheet.id).update_one(inc__ratingSum=delta)
        rating.updatedAt = now
        return rating

    # --- Público: GET /vademecum/sheets/{sheetId}/comments ---

    def public_comments(self, sheetId, args):
        sheet = CatalogService().published_sheet(sheetId)
        if not sheet:
            return not_found()
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        ratings = VademecumRating.objects(sheet=sheet.id, commentStatus="approved") \
            .order_by("-updatedAt")
        total = ratings.count()
        records = list(ratings.skip((page - 1) * pageSize).limit(pageSize))
        accounts = self._accounts(records)
        return {"records": [{"id": str(r.id),
                             "authorName": author_name(accounts.get(self._account_id(r))),
                             "stars": r.stars, "comment": r.comment,
                             "updatedAt": isoformat(r.updatedAt)} for r in records],
                "pagination": _pagination(page, pageSize, total)}, 200

    # --- Backoffice: GET /vademecum/admin/ratings y moderación ---

    def admin_list(self, args):
        status = args.get("commentStatus") or "pending"
        if status not in COMMENT_STATUSES:
            return invalid("commentStatus")
        query = {"commentStatus": status}
        sheetId = args.get("sheetId")
        if sheetId:
            if not object_id(sheetId):
                return invalid("sheetId")
            query["sheet"] = object_id(sheetId)
        page, pageSize, failure = _page_args(args)
        if failure:
            return failure
        # Pendientes por orden de llegada (cola de moderación); el resto, lo más reciente primero
        order = "updatedAt" if status == "pending" else "-updatedAt"
        ratings = VademecumRating.objects(**query).order_by(order)
        total = ratings.count()
        records = list(ratings.skip((page - 1) * pageSize).limit(pageSize))
        accounts = self._accounts(records)
        sheets = {s.id: s for s in VademecumSheet.objects(
            id__in=list({self._sheet_id(r) for r in records}))}
        return {"records": [self._admin_dict(r, accounts, sheets) for r in records],
                "pagination": _pagination(page, pageSize, total)}, 200

    def get(self, ratingId):
        ratingOid = object_id(ratingId)
        return ratingOid and VademecumRating.objects(id=ratingOid).first()

    def moderate(self, rating, status, admin, jsonData):
        try:
            data = ModerationSchema().load(jsonData or {})
        except ValidationError as err:
            return err.messages, 400
        if not rating.comment:
            return error(*NO_COMMENT)
        seen = data.get("updatedAt")
        if seen is not None:
            seen = seen.replace(tzinfo=None, microsecond=0)
            if rating.updatedAt.replace(microsecond=0) != seen:
                return error(*CHANGED_SINCE_SEEN)
        # Condicionada a la versión leída: si el docente edita a la vez, no se pisa su cambio
        now = datetime.utcnow()
        updated = VademecumRating.objects(id=rating.id, updatedAt=rating.updatedAt).update_one(
            set__commentStatus=status, set__moderatedBy=admin.id, set__moderatedAt=now)
        if not updated:
            return error(*CHANGED_SINCE_SEEN)
        rating.reload()
        accounts = self._accounts([rating])
        sheets = {s.id: s for s in VademecumSheet.objects(id=self._sheet_id(rating))}
        return self._admin_dict(rating, accounts, sheets), 200

    # --- Utilidades ---

    @staticmethod
    def _account_id(rating):
        return rating._data["account"].id if hasattr(rating._data["account"], "id") \
            else rating._data["account"]

    @staticmethod
    def _sheet_id(rating):
        return rating._data["sheet"].id if hasattr(rating._data["sheet"], "id") \
            else rating._data["sheet"]

    def _accounts(self, ratings):
        ids = list({self._account_id(r) for r in ratings})
        return {a.id: a for a in VademecumTeacherAccount.objects(id__in=ids)}

    def _admin_dict(self, rating, accounts, sheets):
        account = accounts.get(self._account_id(rating))
        sheet = sheets.get(self._sheet_id(rating))
        moderator = rating.moderatedBy if rating._data.get("moderatedBy") else None
        return {
            "id": str(rating.id),
            "sheet": ({"id": str(sheet.id), "code": sheet.code, "title": sheet.title}
                      if sheet else None),
            "account": ({"id": str(account.id), "email": account.email,
                         "firstName": account.firstName, "lastName": account.lastName}
                        if account else None),
            "stars": rating.stars,
            "comment": rating.comment,
            "commentStatus": rating.commentStatus,
            "moderatedBy": ({"id": str(moderator.id), "name": u" ".join(
                filter(None, [getattr(moderator, "firstName", None),
                              getattr(moderator, "lastName", None)])) or None}
                            if moderator else None),
            "moderatedAt": isoformat(rating.moderatedAt),
            "updatedAt": isoformat(rating.updatedAt),
        }


def with_rating(rating, action):
    return action(rating) if rating else not_found()
