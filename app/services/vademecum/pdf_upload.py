# -*- coding: utf-8 -*-
# app/services/vademecum/pdf_upload.py
"""Recepción de PDF de fichas desde el backoffice (API-07, rehecho en API-11).

El backoffice separa el compendio en el navegador y envía cada ficha por separado; aquí
solo se recibe el archivo por bloques, se valida (firma, tamaño, que abra y tenga páginas) y
se deja en un temporal dentro de VADEMECUM_STORAGE_PATH (nunca en resources/, que es
público). El compendio original no se guarda.
"""

import logging
import os
import uuid

from flask import current_app

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_MB = 100
# El encabezado %PDF- puede estar en cualquier parte del primer KB (especificación PDF)
PDF_SIGNATURE = b"%PDF-"
PDF_HEADER_WINDOW = 1024
CHUNK_SIZE = 1024 * 1024
# Margen para los campos y separadores del multipart sobre el tamaño del PDF
MULTIPART_OVERHEAD_BYTES = 64 * 1024


def error(field, code, msg, httpStatus=400):
    return {field: [{"status": code, "msg": msg}]}, httpStatus


def max_upload_bytes():
    try:
        megabytes = int(current_app.config.get("VADEMECUM_MAX_UPLOAD_MB")
                        or DEFAULT_MAX_UPLOAD_MB)
    except (TypeError, ValueError):
        megabytes = DEFAULT_MAX_UPLOAD_MB
    return megabytes * 1024 * 1024


def storage_root():
    storage = current_app.config.get("VADEMECUM_STORAGE_PATH")
    return os.path.realpath(storage) if storage else None


def too_large():
    return error("file", "115", "File must be a PDF up to {} MB".format(
        max_upload_bytes() // (1024 * 1024)))


def body_too_large(request):
    """Antes de leer request.files: Werkzeug volcaría a disco un cuerpo de cualquier tamaño."""
    return (request.content_length or 0) > max_upload_bytes() + MULTIPART_OVERHEAD_BYTES


class InvalidPdf(Exception):
    pass


def save_pdf_stream(stream, target, maxBytes):
    """Copia el archivo por bloques validando firma y tamaño; devuelve los bytes escritos."""
    written = 0
    head = b""
    with open(target, "wb") as handle:
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            if len(head) < PDF_HEADER_WINDOW:
                head += chunk[:PDF_HEADER_WINDOW - len(head)]
            written += len(chunk)
            if written > maxBytes:
                raise InvalidPdf("too large")
            handle.write(chunk)
    if not written or PDF_SIGNATURE not in head:
        raise InvalidPdf("not a pdf")
    return written


def check_pdf(path):
    """Que PyMuPDF lo abra, sin contraseña y con páginas; InvalidPdf si no."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("Vademecum: PyMuPDF is not installed")
        raise
    try:
        document = fitz.open(path)
    except Exception:
        raise InvalidPdf("damaged")
    try:
        if document.needs_pass or document.page_count == 0:
            raise InvalidPdf("protected or empty")
    finally:
        document.close()


class ReceivedPdf(object):
    """Contexto con la ruta del PDF recibido; el temporal se borra al salir."""

    def __init__(self, fileStorage):
        self.fileStorage = fileStorage
        self.path = None
        self.failure = None

    def __enter__(self):
        if self.fileStorage is None or not self.fileStorage.filename:
            self.failure = error("file", "2", "Missing data for required field.")
            return self
        root = storage_root()
        if not root:
            logger.error("Vademecum: VADEMECUM_STORAGE_PATH is not configured")
            self.failure = error("general", "0", "Storage is not configured", 500)
            return self
        incoming = os.path.join(root, "incoming")
        os.makedirs(incoming, exist_ok=True)
        self.path = os.path.join(incoming, "{}.pdf".format(uuid.uuid4().hex))
        try:
            save_pdf_stream(self.fileStorage.stream, self.path, max_upload_bytes())
            check_pdf(self.path)
        except InvalidPdf:
            self.failure = too_large()
        return self

    def __exit__(self, *exc):
        if self.path:
            try:
                os.remove(self.path)
            except OSError:
                pass
        return False
