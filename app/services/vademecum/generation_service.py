# -*- coding: utf-8 -*-
# app/services/vademecum/generation_service.py
"""Cortes confirmados y generación de fichas en `draft` (API-11, GES-03 5.5).

Cortes (`PUT /admin/uploads/{id}/cuts`, solo en `review`):
- Cubren todas las páginas de la carga, en orden, cada página en un solo corte, y cada corte
  con páginas consecutivas. Así unir, separar o quitar páginas es solo reagrupar: quitar =
  dejar la página en un corte `excluded`.
- Número y título vacíos se toman de la primera página del corte: al unir dos fichas se
  conservan los de la primera.
- Los cortes que no son `excluded` necesitan número y título, sin números repetidos.

Generación (`POST /admin/uploads/{id}/generate`): `review` → `generating` con reclamo
atómico y latido (como el procesamiento, API-08) → una ficha `draft` por corte → `done`.
Una ficha que ya existe (tipo, serie, número) no se genera y se informa en `errorMessage`.
"""

import logging
import uuid
from datetime import datetime

from marshmallow import ValidationError
from mongoengine.errors import NotUniqueError

from app.models.vademecum import UploadCut, VademecumSheet, VademecumUpload
from app.schemas.vademecum.admin_schema import CutsInputSchema
from app.services.vademecum import processing_service
from app.services.vademecum.processing_service import LostClaim

logger = logging.getLogger(__name__)

# `error` permite reintentar una generación interrumpida; las fichas ya creadas se informan
# como existentes y no se duplican
GENERATABLE_STATUSES = ("review", "error")
MAX_TITLE_LENGTH = 150
STATUS_ERROR = ({"general": [{"status": "114",
                              "msg": "Upload status does not allow this action"}]}, 409)


def cuts_error(msg):
    return {"cuts": [{"status": "116", "msg": msg}]}, 400


def validate_cuts(upload, cuts):
    """Completa número y título desde la primera página; devuelve (cortes, error)."""
    pageCount = upload.pageCount or 0
    if not cuts:
        return None, cuts_error("At least one cut is required")
    pagesByIndex = {p.index: p for p in upload.pages}
    expected = 0
    result = []
    for position, cut in enumerate(cuts, 1):
        pages = cut["pages"]
        if not pages:
            return None, cuts_error("Cut {} has no pages".format(position))
        if pages != list(range(pages[0], pages[0] + len(pages))):
            return None, cuts_error("Pages of cut {} must be consecutive".format(position))
        if pages[0] != expected:
            return None, cuts_error(
                "Cuts must cover every page once and in order (page {})".format(expected))
        expected = pages[-1] + 1
        if expected > pageCount:
            return None, cuts_error("Cut {} is out of range".format(position))

        number, title = cut.get("number"), (cut.get("title") or u"").strip() or None
        first = pagesByIndex.get(pages[0])
        if not cut["excluded"] and first is not None:
            number = number or first.number
            title = title or ((first.title or u"").strip()[:MAX_TITLE_LENGTH] or None)
        result.append(UploadCut(pages=pages, number=number, title=title,
                                excluded=cut["excluded"]))
    if expected != pageCount:
        return None, cuts_error(
            "Cuts must cover every page once and in order (page {})".format(expected))

    numbers = set()
    for position, cut in enumerate(result, 1):
        if cut.excluded:
            continue
        if not cut.number or not cut.title:
            return None, cuts_error("Cut {} needs a number and a title".format(position))
        if cut.number in numbers:
            return None, cuts_error("Number {} is repeated".format(cut.number))
        numbers.add(cut.number)
    return result, None


def save_cuts(upload, jsonData, detail):
    """Guarda los cortes confirmados; `detail(upload)` da la respuesta."""
    try:
        data = CutsInputSchema().load(jsonData or {})
    except ValidationError as err:
        return err.messages, 400
    processing_service.mark_stale()
    upload.reload()
    if upload.status != "review":
        return STATUS_ERROR
    cuts, failure = validate_cuts(upload, data["cuts"])
    if failure:
        return failure
    # Solo si sigue en `review`: no pisa una generación que empezó entre medio
    if not VademecumUpload.objects(id=upload.id, status="review", isDeleted=False).update_one(
            set__confirmedCuts=cuts, set__updatedAt=datetime.utcnow()):
        return STATUS_ERROR
    upload.reload()
    return detail(upload), 200


def claim_generation(upload):
    """`review` con cortes confirmados → `generating`; devuelve el processingId o None."""
    processingId = uuid.uuid4().hex
    now = datetime.utcnow()
    updated = VademecumUpload.objects(
        id=upload.id, status__in=GENERATABLE_STATUSES, isDeleted=False,
        confirmedCuts__elemMatch={"excluded": False}
    ).update_one(set__status="generating", set__progress=0, set__errorMessage=None,
                 set__processingId=processingId, set__heartbeatAt=now, set__updatedAt=now)
    return processingId if updated else None


def generate(upload, summary):
    """Lanza la generación; 202 con la carga en `generating`."""
    processing_service.mark_stale()
    processingId = claim_generation(upload)
    if not processingId:
        return STATUS_ERROR
    processing_service.start(upload, target=lambda app, uploadId: run(app, uploadId,
                                                                      processingId))
    upload.reload()
    return summary(upload), 202


def _sheet_label(upload, number):
    from app.models.vademecum.sheet_model import build_sheet_code
    series = upload.sheetType.get_series(upload.seriesId)
    return build_sheet_code(upload.sheetType.codePrefix, series.code if series else None,
                            number)


def build_sheet(upload, cut, source):
    """Crea la ficha en `draft` con sus archivos; None si ya existe (tipo, serie, número)."""
    from app.services.vademecum import sheet_media
    # Consulta cruda: seriesId null también encuentra el campo ausente (como el índice único)
    if VademecumSheet.objects(__raw__={"sheetType": upload.sheetType.id,
                                       "seriesId": upload.seriesId,
                                       "number": cut.number, "isDeleted": False}).first():
        return None
    series = upload.sheetType.get_series(upload.seriesId)
    sheet = VademecumSheet(sheetType=upload.sheetType, seriesId=upload.seriesId,
                           number=cut.number, title=cut.title, upload=upload,
                           sourcePages=list(cut.pages),
                           grades=list(series.grades) if series else [])
    try:
        sheet.save()
    except NotUniqueError:
        return None
    try:
        sheet.file, sheet.searchText = sheet_media.build_sheet_files(
            source, sheet.id, pages=list(cut.pages))
        sheet.save()
    except Exception:
        sheet.delete()  # recién creada y sin archivos: no queda nada a medias
        raise
    return sheet


def run(app, uploadId, processingId):
    """Cuerpo del hilo: una ficha por corte y `done` al final. Nunca lanza."""
    with app.app_context():
        from app.services.vademecum.compendium_processor import ProcessingError, original_path
        upload = VademecumUpload.objects(id=uploadId, processingId=processingId,
                                         status="generating", isDeleted=False).first()
        if not upload:
            return
        owned = VademecumUpload.objects(id=uploadId, processingId=processingId,
                                        status="generating", isDeleted=False)
        cuts = [c for c in upload.confirmedCuts if not c.excluded]
        duplicated = []
        try:
            source = original_path(upload)
            for position, cut in enumerate(cuts, 1):
                sheet = build_sheet(upload, cut, source)
                if sheet is None:
                    duplicated.append(_sheet_label(upload, cut.number))
                elif not owned.update_one(push__sheets=sheet, set__updatedAt=datetime.utcnow()):
                    raise LostClaim()
                processing_service.report_progress(
                    upload, processingId, 99 * position / len(cuts), status="generating")
        except LostClaim:
            logger.warning("Vademecum: generation of upload %s was taken over", uploadId)
            return
        except ProcessingError as exc:
            processing_service.fail(upload, processingId, exc.message, status="generating")
            return
        except Exception:
            logger.exception("Vademecum: generating sheets of upload %s failed", uploadId)
            processing_service.fail(upload, processingId,
                                    u"No se pudieron generar las fichas.", status="generating")
            return

        message = None
        if duplicated:
            message = u"Fichas que ya existían y no se generaron: {}.".format(
                u", ".join(duplicated))[:processing_service.MAX_ERROR_LENGTH]
        now = datetime.utcnow()
        if not owned.update_one(set__status="done", set__progress=100,
                                set__errorMessage=message, set__processingId=None,
                                set__heartbeatAt=now, set__updatedAt=now):
            logger.warning("Vademecum: upload %s was taken over before finishing", uploadId)
