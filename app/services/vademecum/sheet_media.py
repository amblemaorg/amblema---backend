# -*- coding: utf-8 -*-
# app/services/vademecum/sheet_media.py
"""Archivos derivados de cada ficha (API-10): PDF comprimido, imágenes WebP y texto.

- PDF: Ghostscript con el ajuste /ebook (150 ppp en imágenes, calidad de impresión
  aceptable). Ghostscript 9.x deja pasar los JPEG sin tocarlos; se desactiva para que las
  fotos también se reduzcan. Si Ghostscript no está, falla o el resultado no es más liviano, se conserva el
  PDF sin comprimir: la ficha se genera igual.
- Miniatura nítida (catálogo) y vista previa difuminada (detalle, no sirve para imprimir),
  ambas de la primera página. Miniaturas de páginas del compendio para revisar los cortes.
- Texto de todas las páginas para la búsqueda (`searchText`, índice de texto).

Requiere PyMuPDF (Python 3) y Pillow con WebP; los imports de PyMuPDF son perezosos.
"""

import logging
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime

from flask import current_app
from PIL import Image, ImageFilter

from app.models.vademecum import SheetFile

logger = logging.getLogger(__name__)

THUMBNAIL_WIDTH = 480        # tarjeta del catálogo a 240 px con pantallas 2x
THUMBNAIL_QUALITY = 82
PREVIEW_WIDTH = 900
PREVIEW_BLUR_RADIUS = 6      # se lee la composición, no el contenido
PREVIEW_QUALITY = 60
PAGE_THUMBNAIL_WIDTH = 240   # revisión de cortes en el backoffice
PAGE_THUMBNAIL_QUALITY = 70
MAX_SEARCH_TEXT = 20000
DEFAULT_GHOSTSCRIPT_TIMEOUT = 300
DEFAULT_GHOSTSCRIPT_PRESET = "/ebook"
GHOSTSCRIPT_PRESETS = ("/screen", "/ebook", "/printer", "/prepress")


# --- PDF ---

def ghostscript_binary():
    configured = current_app.config.get("VADEMECUM_GHOSTSCRIPT")
    return configured or shutil.which("gs")


def ghostscript_preset():
    preset = current_app.config.get("VADEMECUM_GHOSTSCRIPT_PRESET") or DEFAULT_GHOSTSCRIPT_PRESET
    return preset if preset in GHOSTSCRIPT_PRESETS else DEFAULT_GHOSTSCRIPT_PRESET


def ghostscript_timeout():
    try:
        return int(current_app.config.get("VADEMECUM_GHOSTSCRIPT_TIMEOUT")
                   or DEFAULT_GHOSTSCRIPT_TIMEOUT)
    except (TypeError, ValueError):
        return DEFAULT_GHOSTSCRIPT_TIMEOUT


def compress_pdf(source, target):
    """Escribe en `target` el PDF comprimido (o una copia); True si se comprimió."""
    binary = ghostscript_binary()
    if binary:
        temporary = target + ".gs-tmp"
        command = [binary, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
                   "-dPDFSETTINGS={}".format(ghostscript_preset()),
                   "-dPassThroughJPEGImages=false", "-dNOPAUSE", "-dBATCH",
                   "-dQUIET", "-dSAFER", "-sOutputFile={}".format(temporary), source]
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           timeout=ghostscript_timeout(), check=True)
            if 0 < os.path.getsize(temporary) < os.path.getsize(source):
                os.replace(temporary, target)
                return True
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("Vademecum: Ghostscript failed for %s: %s", source, exc)
        finally:
            _remove(temporary)
    else:
        logger.warning("Vademecum: Ghostscript is not available; PDF kept uncompressed")
    shutil.copyfile(source, target)
    return False


# --- Imágenes ---

def page_image(page, width):
    """Página de PyMuPDF como imagen RGB de Pillow con el ancho pedido."""
    import fitz  # PyMuPDF
    zoom = float(width) / page.rect.width
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def save_webp(image, target, quality):
    temporary = target + ".tmp"
    image.save(temporary, "WEBP", quality=quality, method=6)
    os.replace(temporary, target)


def render_page_thumbnail(page, target):
    save_webp(page_image(page, PAGE_THUMBNAIL_WIDTH), target, PAGE_THUMBNAIL_QUALITY)


def render_thumbnail(page, target):
    save_webp(page_image(page, THUMBNAIL_WIDTH), target, THUMBNAIL_QUALITY)


def render_preview(page, target):
    image = page_image(page, PREVIEW_WIDTH).filter(ImageFilter.GaussianBlur(PREVIEW_BLUR_RADIUS))
    save_webp(image, target, PREVIEW_QUALITY)


# --- Texto ---

def extract_text(document):
    """Texto de todas las páginas en una sola línea, recortado para el índice."""
    parts = [document.load_page(index).get_text("text") for index in range(document.page_count)]
    text = re.sub(r"\s+", u" ", u" ".join(parts)).strip()
    return text[:MAX_SEARCH_TEXT] or None


# --- Ficha completa ---

def storage_root():
    storage = current_app.config.get("VADEMECUM_STORAGE_PATH")
    return os.path.realpath(storage) if storage else None


def sheet_dir(sheetId):
    return "sheets/{}".format(sheetId)


def build_sheet_files(source, sheetId, pages=None):
    """Genera PDF, miniatura, vista previa y texto de una ficha en `sheets/<sheetId>/`.

    `source` es la ruta de un PDF; `pages` (índices consecutivos) toma solo esas páginas,
    o todas si es None. Los archivos nuevos reemplazan a los anteriores al final, de forma
    atómica por archivo. Devuelve (SheetFile, searchText).
    """
    import fitz  # PyMuPDF
    root = storage_root()
    if not root:
        raise RuntimeError("VADEMECUM_STORAGE_PATH is not configured")
    relative = sheet_dir(sheetId)
    target = os.path.join(root, relative)
    work = os.path.join(target, "tmp-{}".format(uuid.uuid4().hex))
    os.makedirs(work)
    try:
        raw = os.path.join(work, "raw.pdf")
        original = fitz.open(source)
        try:
            if pages is None:
                original.save(raw, garbage=3, deflate=True)
            else:
                extracted = fitz.open()
                extracted.insert_pdf(original, from_page=pages[0], to_page=pages[-1])
                extracted.save(raw, garbage=3, deflate=True)
                extracted.close()
        finally:
            original.close()

        compress_pdf(raw, os.path.join(work, "sheet.pdf"))
        document = fitz.open(os.path.join(work, "sheet.pdf"))
        try:
            first = document.load_page(0)
            render_thumbnail(first, os.path.join(work, "thumbnail.webp"))
            render_preview(first, os.path.join(work, "preview.webp"))
            searchText = extract_text(document)
            pageCount = document.page_count
        finally:
            document.close()

        for name in ("sheet.pdf", "thumbnail.webp", "preview.webp"):
            os.replace(os.path.join(work, name), os.path.join(target, name))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    sheetFile = SheetFile(
        pdfPath=relative + "/sheet.pdf",
        sizeBytes=os.path.getsize(os.path.join(target, "sheet.pdf")),
        pageCount=pageCount,
        thumbnailPath=relative + "/thumbnail.webp",
        previewPath=relative + "/preview.webp",
        generatedAt=datetime.utcnow())
    return sheetFile, searchText


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass
