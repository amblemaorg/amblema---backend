# -*- coding: utf-8 -*-
# app/services/vademecum/sheet_media.py
"""Archivos derivados de cada ficha (API-10): PDF comprimido, imágenes WebP y texto.

- PDF: Ghostscript con el ajuste /ebook (150 ppp en imágenes, calidad de impresión
  aceptable). Ghostscript 9.x deja pasar los JPEG sin tocarlos; se desactiva para que las
  fotos también se reduzcan. Si Ghostscript no está, falla o el resultado no es más liviano, se conserva el
  PDF sin comprimir: la ficha se genera igual.
- Vista previa difuminada (sin sesión), miniatura nítida (480 px, con sesión, catálogo e
  Inicio) y una WebP nítida (1200 px) por cada cara 1..N para el visor (2 + N imágenes).
  Todas se generan al subir o reemplazar la ficha, en la misma petición; el visor nunca
  renderiza el PDF bajo demanda. Las miniaturas para revisar el compendio las hace el
  backoffice en el navegador (API-11 rehecho): el compendio no llega al servidor.
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
PAGE_VIEW_WIDTH = 1200       # visor protegido del docente: legible incluso con zoom
PAGE_VIEW_QUALITY = 85
PREVIEW_WIDTH = 900
PREVIEW_BLUR_RADIUS = 6      # se lee la composición, no el contenido
PREVIEW_SHARP_UNTIL = 0.20   # el 20 % superior queda nítido (encabezado y título)
PREVIEW_FADE_UNTIL = 0.35    # entre el 20 % y el 35 % el difuminado entra en degradado
PREVIEW_QUALITY = 60
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
    image.save(temporary, "WEBP", quality=quality, method=2)
    os.replace(temporary, target)


def resize_to_width(image, width):
    """Redimensiona manteniendo la relación de aspecto con filtro LANCZOS."""
    if image.width == width:
        return image
    height = max(1, int(round(image.height * (float(width) / image.width))))
    return image.resize((width, height), Image.LANCZOS)


def _save_preview_from_image(sharp, target):
    blurred = sharp.filter(ImageFilter.GaussianBlur(PREVIEW_BLUR_RADIUS))
    save_webp(Image.composite(blurred, sharp, blur_mask(sharp.size)), target, PREVIEW_QUALITY)


def render_thumbnail(page, target):
    save_webp(page_image(page, THUMBNAIL_WIDTH), target, THUMBNAIL_QUALITY)


def blur_mask(size):
    """Máscara "L": 0 (nítido) arriba, 255 (difuminado) abajo, con un degradado entre ambos."""
    width, height = size
    start = int(height * PREVIEW_SHARP_UNTIL)
    end = max(start + 1, int(height * PREVIEW_FADE_UNTIL))
    column = [0 if row < start else min(255, (row - start) * 255 // (end - start))
              for row in range(height)]
    mask = Image.new("L", (1, height))
    mask.putdata(column)
    return mask.resize((width, height))


def render_preview(page, target):
    _save_preview_from_image(page_image(page, PREVIEW_WIDTH), target)


def render_pdf_page(pdf_file_path, page_number, target):
    """Renderiza una página específica (1-based) del PDF en WebP nítido para el visor."""
    if page_number < 1:
        return False
    import fitz  # PyMuPDF
    document = fitz.open(pdf_file_path)
    try:
        if page_number > document.page_count:
            return False
        page = document.load_page(page_number - 1)
        save_webp(page_image(page, PAGE_VIEW_WIDTH), target, PAGE_VIEW_QUALITY)
        return True
    finally:
        document.close()


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
    """Genera PDF, vista previa, miniatura, caras 1..N y texto en `sheets/<sheetId>/`.

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
        if pages is None:
            # El backoffice ya envía la ficha separada: evitar re-guardar con garbage=3
            # antes de Ghostscript ahorra E/S y CPU sin cambiar el PDF final.
            compress_source = source
        else:
            raw = os.path.join(work, "raw.pdf")
            original = fitz.open(source)
            try:
                extracted = fitz.open()
                extracted.insert_pdf(original, from_page=pages[0], to_page=pages[-1])
                extracted.save(raw, garbage=3, deflate=True)
                extracted.close()
            finally:
                original.close()
            compress_source = raw

        compress_pdf(compress_source, os.path.join(work, "sheet.pdf"))
        document = fitz.open(os.path.join(work, "sheet.pdf"))
        try:
            searchText = extract_text(document)
            pageCount = document.page_count
            # Caras nítidas 1..N (1200 px) que el visor pide con token; ninguna se renderiza
            # al abrir la ficha. La página 1 se rasteriza una sola vez a 1200 px y se
            # redimensiona en memoria para miniatura (480 px) y vista previa (900 px).
            firstImage = page_image(document.load_page(0), PAGE_VIEW_WIDTH)
            save_webp(firstImage, os.path.join(work, "page-1.webp"), PAGE_VIEW_QUALITY)
            save_webp(resize_to_width(firstImage, THUMBNAIL_WIDTH),
                      os.path.join(work, "thumbnail.webp"), THUMBNAIL_QUALITY)
            _save_preview_from_image(resize_to_width(firstImage, PREVIEW_WIDTH),
                                     os.path.join(work, "preview.webp"))
            pageNames = ["page-1.webp"]
            for number in range(2, pageCount + 1):
                name = "page-{}.webp".format(number)
                image = page_image(document.load_page(number - 1), PAGE_VIEW_WIDTH)
                save_webp(image, os.path.join(work, name), PAGE_VIEW_QUALITY)
                pageNames.append(name)
        finally:
            document.close()

        for name in ("sheet.pdf", "thumbnail.webp", "preview.webp") + tuple(pageNames):
            os.replace(os.path.join(work, name), os.path.join(target, name))
        # Si la ficha se reemplaza con menos páginas, sobran caras del PDF anterior.
        for name in os.listdir(target):
            match = re.match(r"^page-(\d+)\.webp$", name)
            if match and int(match.group(1)) > pageCount:
                _remove(os.path.join(target, name))
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


def regenerate_page_images(sheetFile):
    """Completa las caras 1..N (1200 px) de una ficha ya subida, sin escribir en la BD.

    Las fichas creadas antes de este cambio solo tienen miniatura y vista previa (o caras 2..N).
    Devuelve el número de imágenes creadas; llamarlo dos veces no hace nada.
    """
    root = storage_root()
    if not root or not sheetFile or not sheetFile.pdfPath:
        return 0
    pdf = os.path.realpath(os.path.join(root, sheetFile.pdfPath))
    if not pdf.startswith(root + os.sep) or not os.path.isfile(pdf):
        return 0
    folder = os.path.dirname(pdf)
    count = sheetFile.pageCount or 0
    generated = 0
    for number in range(1, count + 1):
        target = os.path.join(folder, "page-{}.webp".format(number))
        if not os.path.isfile(target) and render_pdf_page(pdf, number, target):
            generated += 1
    for name in os.listdir(folder):
        match = re.match(r"^page-(\d+)\.webp$", name)
        if match and int(match.group(1)) > count:
            _remove(os.path.join(folder, name))
    return generated


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass
