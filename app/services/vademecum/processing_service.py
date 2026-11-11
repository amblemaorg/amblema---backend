# -*- coding: utf-8 -*-
# app/services/vademecum/processing_service.py
"""Procesamiento de compendios en segundo plano, sin colas (API-08, GES-03 5.5).

- La petición solo deja la carga en `uploaded` y lanza un hilo; responde de inmediato.
- El hilo reclama la carga con una actualización atómica en Mongo (`uploaded` →
  `processing` con un `processingId` propio): con varios workers o procesos, solo uno la
  procesa.
- Mientras procesa, cada avance renueva `heartbeatAt`. Si el proceso muere (reinicio del
  contenedor, worker reciclado), el latido envejece y la carga se marca `error`
  ("interrumpido") al consultarla; el administrador la reintenta con /reprocess.
- Un hilo que perdió la carga (marcada interrumpida y reintentada por otro) deja de escribir:
  todas sus escrituras exigen su `processingId`.

El trabajo sobre el PDF (páginas, encabezados, cortes) lo hace `compendium_processor`.
"""

import logging
import threading
import uuid
from datetime import datetime, timedelta

from flask import current_app

from app.models.vademecum import VademecumUpload

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=5)
BUSY_STATUSES = ("uploaded", "processing", "generating")
REPROCESSABLE_STATUSES = ("review", "error")
INTERRUPTED_MESSAGE = u"El procesamiento se interrumpió. Vuelve a intentarlo."
FAILED_MESSAGE = u"No se pudo procesar el PDF."
MAX_ERROR_LENGTH = 300


class LostClaim(Exception):
    """La carga ya no pertenece a este proceso (se marcó interrumpida o se reintentó)."""


def processing_mode():
    """thread (por defecto), inline (pruebas) u off (pruebas que no procesan)."""
    return current_app.config.get("VADEMECUM_PROCESSING_MODE") or "thread"


def start(upload, target=None):
    """Lanza el procesamiento de una carga según el modo configurado.

    `target(app, uploadId)` es el trabajo; por defecto leer el compendio (`run`). La
    generación de fichas (API-11) usa el mismo arranque con su propio trabajo.
    """
    target = target or run
    mode = processing_mode()
    if mode == "off":
        return
    app = current_app._get_current_object()
    if mode == "inline":
        target(app, upload.id)
        return
    worker = threading.Thread(target=target, args=(app, upload.id),
                              name="vademecum-upload-{}".format(upload.id))
    worker.daemon = True  # no impide apagar la API; lo cortado se detecta por el latido
    worker.start()


def mark_stale(now=None):
    """Marca `error` las cargas ocupadas cuyo latido es viejo; devuelve cuántas."""
    now = now or datetime.utcnow()
    return VademecumUpload.objects(
        status__in=BUSY_STATUSES, heartbeatAt__lt=now - STALE_AFTER, isDeleted=False
    ).update(set__status="error", set__errorMessage=INTERRUPTED_MESSAGE,
             set__processingId=None, set__updatedAt=now)


def queue_again(upload):
    """Deja una carga en `uploaded` para reintentarla; False si su estado no lo permite."""
    now = datetime.utcnow()
    updated = VademecumUpload.objects(
        id=upload.id, status__in=REPROCESSABLE_STATUSES, isDeleted=False
    ).update_one(set__status="uploaded", set__progress=0, set__errorMessage=None,
                 set__processingId=None, set__heartbeatAt=now, set__updatedAt=now)
    return bool(updated)


def claim(uploadId):
    """`uploaded` → `processing` de forma atómica; devuelve (carga, processingId) o (None, None)."""
    processingId = uuid.uuid4().hex
    now = datetime.utcnow()
    upload = VademecumUpload.objects(id=uploadId, status="uploaded", isDeleted=False).modify(
        new=True, set__status="processing", set__progress=0, set__errorMessage=None,
        set__processingId=processingId, set__heartbeatAt=now, set__updatedAt=now)
    return (upload, processingId) if upload else (None, None)


def _owned(upload, processingId, status="processing"):
    return VademecumUpload.objects(id=upload.id, status=status,
                                   processingId=processingId, isDeleted=False)


def report_progress(upload, processingId, progress, status="processing"):
    """Guarda el avance (0–99) y renueva el latido; LostClaim si la carga ya no es suya."""
    now = datetime.utcnow()
    progress = max(0, min(99, int(progress)))
    if not _owned(upload, processingId, status).update_one(
            set__progress=progress, set__heartbeatAt=now, set__updatedAt=now):
        raise LostClaim()


def finish(upload, processingId, result):
    """Pasa a `review` con lo detectado; descarta cortes confirmados que no se generaron."""
    now = datetime.utcnow()
    return bool(_owned(upload, processingId).update_one(
        set__status="review", set__progress=100, set__pageCount=result["pageCount"],
        set__pages=result["pages"], set__proposedCuts=result["proposedCuts"],
        set__confirmedCuts=[], set__processedAt=now, set__processingId=None,
        set__heartbeatAt=now, set__updatedAt=now))


def fail(upload, processingId, message, status="processing"):
    now = datetime.utcnow()
    return bool(_owned(upload, processingId, status).update_one(
        set__status="error", set__errorMessage=message[:MAX_ERROR_LENGTH],
        set__processingId=None, set__heartbeatAt=now, set__updatedAt=now))


def run(app, uploadId):
    """Cuerpo del hilo: reclama, procesa y deja `review` o `error`. Nunca lanza."""
    with app.app_context():
        upload, processingId = claim(uploadId)
        if not upload:
            return  # otro worker la tomó o ya no está en `uploaded`
        from app.services.vademecum import compendium_processor
        try:
            result = compendium_processor.process(
                upload, lambda value: report_progress(upload, processingId, value))
        except LostClaim:
            logger.warning("Vademecum: upload %s was taken over; stopping", uploadId)
            return
        except compendium_processor.ProcessingError as exc:
            # Mensaje pensado para el administrador (PDF dañado, sin páginas...)
            fail(upload, processingId, exc.message)
            return
        except Exception:  # el detalle va al log, no al backoffice
            logger.exception("Vademecum: processing upload %s failed", uploadId)
            fail(upload, processingId, FAILED_MESSAGE)
            return
        if not finish(upload, processingId, result):
            logger.warning("Vademecum: upload %s was taken over before finishing", uploadId)
