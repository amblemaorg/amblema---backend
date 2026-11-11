# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_media_test.py
"""Compresión, miniaturas WebP y texto de las fichas (API-10) y su reemplazo."""

import io
import os
import shutil
import unittest

from PIL import Image, ImageFilter, ImageStat


try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - imagen sin PyMuPDF
    fitz = None
from app.tests.integration.vademecum_base import VademecumAdminTestBase


def make_pdf(pages=3):
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        page.insert_text((72, 72), u"Hora TAL {}. Página de prueba".format(index + 1))
    data = document.tobytes()
    document.close()
    return data


def make_compendium(headers):
    """PDF con el tipo en una línea y "<N>[A]. <Título>" en la siguiente."""
    document = fitz.open()
    for header in headers:
        page = document.new_page()
        page.insert_text((72, 60), u"Hora TAL")
        page.insert_text((72, 80), header)
        page.insert_text((72, 400), u"Cuerpo de la ficha")
    data = document.tobytes()
    document.close()
    return data


def write(path, data):
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def make_image_pdf():
    """Una página con una foto a ~300 ppp: /ebook baja las que pasan de 225 ppp (150 × 1,5)."""
    noise = Image.frombytes("RGB", (2600, 2600), os.urandom(2600 * 2600 * 3))
    buffer = io.BytesIO()
    noise.save(buffer, "JPEG", quality=95)
    document = fitz.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=buffer.getvalue())
    page.insert_text((72, 72), u"Ficha con imagen")
    data = document.tobytes()
    document.close()
    return data


def strongest_edge(image):
    """Borde más fuerte sin contar el contorno de la imagen (FIND_EDGES lo marca)."""
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(edges.crop((5, 5, edges.width - 5, edges.height - 5))).extrema[0][1]


def make_block_pdf():
    """Un bloque negro: su borde es nítido en la miniatura y suave en la vista previa."""
    document = fitz.open()
    page = document.new_page()
    page.draw_rect(fitz.Rect(100, 100, 400, 400), color=(0, 0, 0), fill=(0, 0, 0))
    data = document.tobytes()
    document.close()
    return data


@unittest.skipUnless(fitz, "PyMuPDF no está instalado")
class VademecumSheetMediaTest(VademecumAdminTestBase):

    def setUp(self):
        super(VademecumSheetMediaTest, self).setUp()
        self.work = os.path.join(self.storage, "work")
        os.makedirs(self.work)

    # --- Compresión ---

    @unittest.skipUnless(shutil.which("gs"), "Ghostscript no está instalado")
    def test_ghostscript_makes_image_pdf_lighter(self):
        from app.services.vademecum.sheet_media import compress_pdf
        source = write(os.path.join(self.work, "in.pdf"), make_image_pdf())
        target = os.path.join(self.work, "out.pdf")
        self.assertTrue(compress_pdf(source, target))
        self.assertLess(os.path.getsize(target), os.path.getsize(source))
        document = fitz.open(target)
        self.assertEqual(document.page_count, 1)
        self.assertIn(u"Ficha con imagen", document.load_page(0).get_text())
        document.close()

    def test_without_ghostscript_the_pdf_is_kept(self):
        from app.services.vademecum.sheet_media import compress_pdf
        self.app.config["VADEMECUM_GHOSTSCRIPT"] = "/no/existe/gs"
        source = write(os.path.join(self.work, "in.pdf"), make_pdf(2))
        target = os.path.join(self.work, "out.pdf")
        self.assertFalse(compress_pdf(source, target))
        with open(source, "rb") as a, open(target, "rb") as b:
            self.assertEqual(a.read(), b.read())
        self.assertEqual(sorted(os.listdir(self.work)), ["in.pdf", "out.pdf"])

    # --- Ficha completa ---

    def test_build_sheet_files_takes_only_its_pages(self):
        from app.services.vademecum.sheet_media import build_sheet_files
        source = write(os.path.join(self.work, "compendio.pdf"), make_compendium(
            [u"1. Primera", u"2. Segunda", u"2A. Segunda", u"3. Tercera"]))
        sheetFile, searchText = build_sheet_files(source, "abc123", pages=[1, 2])

        self.assertEqual(sheetFile.pageCount, 2)
        self.assertEqual(sheetFile.pdfPath, "sheets/abc123/sheet.pdf")
        self.assertIn(u"2. Segunda", searchText)
        self.assertNotIn(u"Primera", searchText)
        self.assertNotIn(u"Tercera", searchText)
        self.assertNotIn(u"\n", searchText)
        pdf = os.path.join(self.storage, sheetFile.pdfPath)
        self.assertEqual(os.path.getsize(pdf), sheetFile.sizeBytes)
        # Sin temporales en la carpeta de la ficha
        self.assertEqual(sorted(os.listdir(os.path.dirname(pdf))),
                         ["preview.webp", "sheet.pdf", "thumbnail.webp"])

    def test_thumbnail_is_sharp_and_preview_is_blurred(self):
        from app.services.vademecum.sheet_media import (
            PREVIEW_WIDTH, THUMBNAIL_WIDTH, build_sheet_files, page_image)
        source = write(os.path.join(self.work, "bloque.pdf"), make_block_pdf())
        sheetFile, _ = build_sheet_files(source, "abc123")

        thumbnail = Image.open(os.path.join(self.storage, sheetFile.thumbnailPath))
        preview = Image.open(os.path.join(self.storage, sheetFile.previewPath))
        self.assertEqual((thumbnail.format, thumbnail.width), ("WEBP", THUMBNAIL_WIDTH))
        self.assertEqual((preview.format, preview.width), ("WEBP", PREVIEW_WIDTH))
        document = fitz.open(source)
        sharp = page_image(document.load_page(0), PREVIEW_WIDTH)
        document.close()
        self.assertGreater(strongest_edge(sharp), 200)
        self.assertGreater(strongest_edge(thumbnail), 200)
        self.assertLess(strongest_edge(preview), 100)

    def test_generating_again_replaces_the_files(self):
        from app.services.vademecum.sheet_media import build_sheet_files
        first = write(os.path.join(self.work, "a.pdf"), make_pdf(1))
        second = write(os.path.join(self.work, "b.pdf"), make_pdf(3))
        build_sheet_files(first, "abc123")
        sheetFile, _ = build_sheet_files(second, "abc123")
        document = fitz.open(os.path.join(self.storage, sheetFile.pdfPath))
        self.assertEqual(document.page_count, 3)
        document.close()


@unittest.skipUnless(fitz, "PyMuPDF no está instalado")
class VademecumReplaceSheetFileTest(VademecumAdminTestBase):

    def setUp(self):
        super(VademecumReplaceSheetFileTest, self).setUp()
        from app.models.vademecum import VademecumSheet
        self.sheet = VademecumSheet(sheetType=self.hora, number=41, title=u"Identifica")
        self.sheet.save()

    def replace(self, content, filename="nueva.pdf", headers=None):
        data = {} if content is None else {"file": (io.BytesIO(content), filename)}
        return self.client.put("/vademecum/admin/sheets/{}/file".format(self.sheet.id),
                               data=data, content_type="multipart/form-data",
                               headers=self.adminHeaders if headers is None else headers)

    def test_replace_generates_files_and_text(self):
        res = self.replace(make_pdf(2))
        self.assertEqual(res.status_code, 202)
        body = res.get_json()
        self.assertEqual((body["pageCount"], body["fileStatus"]), (2, "ready"))
        self.assertIsNotNone(body["fileReplacedAt"])
        self.sheet.reload()
        self.assertIn(u"Página de prueba", self.sheet.searchText)
        for path in (self.sheet.file.pdfPath, self.sheet.file.thumbnailPath,
                     self.sheet.file.previewPath):
            self.assertTrue(os.path.isfile(os.path.join(self.storage, path)), path)
        # Sin el PDF recibido suelto en el almacenamiento
        self.assertEqual(os.listdir(os.path.join(self.storage, "incoming")), [])

        pdf = self.client.get("/vademecum/admin/sheets/{}/file".format(self.sheet.id),
                              headers=self.adminHeaders)
        self.assertEqual(pdf.status_code, 200)
        pdf.close()

    def test_invalid_file_is_rejected(self):
        res = self.replace(b"no es un pdf")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["file"][0]["status"], "115")
        # %PDF- pero dañado
        res = self.replace(b"%PDF-1.7\nbasura")
        self.assertEqual(res.get_json()["file"][0]["status"], "115")
        self.sheet.reload()
        self.assertIsNone(self.sheet.file)
        self.assertEqual(os.listdir(os.path.join(self.storage, "incoming")), [])
        self.assertFalse(os.path.exists(os.path.join(self.storage, "sheets")))

    def test_missing_file(self):
        res = self.replace(None)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["file"][0]["status"], "2")

    def test_too_large_is_rejected_before_reading(self):
        self.app.config["VADEMECUM_MAX_UPLOAD_MB"] = 1
        res = self.replace(b"%PDF-" + b"0" * (2 * 1024 * 1024))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["file"][0]["status"], "115")

    def test_requires_admin_and_existing_sheet(self):
        self.assertIn(self.replace(make_pdf(1), headers={}).status_code, (401, 403))
        res = self.client.put("/vademecum/admin/sheets/5f0000000000000000000000/file",
                              data={"file": (io.BytesIO(make_pdf(1)), "a.pdf")},
                              content_type="multipart/form-data", headers=self.adminHeaders)
        self.assertEqual(res.status_code, 404)
