# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_sheet_create_test.py
"""Ficha nueva con su PDF ya separado en el backoffice (API-11 rehecho)."""

import io
import json
import os
import unittest

from app.tests.integration.vademecum_base import VademecumAdminTestBase
from app.tests.integration.vademecum_media_test import fitz, make_pdf


@unittest.skipUnless(fitz, "PyMuPDF no está instalado")
class VademecumSheetCreateTest(VademecumAdminTestBase):

    def setUp(self):
        super(VademecumSheetCreateTest, self).setUp()
        from app.models.vademecum import VademecumArea
        self.area = VademecumArea.objects.first()
        self.series = self.ingenio.active_series()[0]

    def data(self, **values):
        base = {"number": 41, "title": u"Identifica la Palabra", "sheetTypeId": str(self.hora.id)}
        base.update(values)
        return base

    def create(self, data=None, content=None, publish=None, headers=None, raw=None):
        form = {"data": raw if raw is not None else json.dumps(data or self.data())}
        if content is not False:
            form["file"] = (io.BytesIO(content or make_pdf(2)), "HT-41.pdf")
        if publish is not None:
            form["publish"] = "true" if publish else "false"
        return self.client.post("/vademecum/admin/sheets", data=form,
                                content_type="multipart/form-data",
                                headers=self.adminHeaders if headers is None else headers)

    def sheet_doc(self, sheetId):
        from app.models.vademecum import VademecumSheet
        return VademecumSheet.objects.get(id=sheetId)

    # --- Creación ---

    def test_creates_a_draft_with_its_files(self):
        res = self.create(self.data(description=u"Lectura", grades=["1", "2"],
                                    areaIds=[str(self.area.id)]))
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual((body["code"], body["title"], body["status"], body["pageCount"]),
                         ("HT-41", u"Identifica la Palabra", "draft", 2))
        self.assertEqual(body["grades"], ["1", "2"])
        self.assertEqual([a["id"] for a in body["areas"]], [str(self.area.id)])
        self.assertIsNone(body["publishedAt"])
        sheet = self.sheet_doc(body["id"])
        self.assertIn(u"Página de prueba", sheet.searchText)
        for path in (sheet.file.pdfPath, sheet.file.thumbnailPath, sheet.file.previewPath):
            self.assertTrue(os.path.isfile(os.path.join(self.storage, path)), path)
        # El PDF recibido no queda suelto
        self.assertEqual(os.listdir(os.path.join(self.storage, "incoming")), [])

    def test_creates_and_publishes(self):
        res = self.create(self.data(description=u"Lectura", grades=["all"]), publish=True)
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual(body["status"], "published")
        self.assertIsNotNone(body["publishedAt"])
        catalog = self.client.get("/vademecum/sheets/{}".format(body["id"]))
        self.assertEqual(catalog.status_code, 200)

    def test_publish_without_required_data_creates_nothing(self):
        res = self.create(publish=True)
        self.assertEqual(res.status_code, 400)
        body = res.get_json()
        self.assertEqual(sorted(body), ["description", "grades"])
        self.assertEqual(body["grades"][0]["status"], "113")
        from app.models.vademecum import VademecumSheet
        self.assertEqual(VademecumSheet.objects.count(), 0)

    def test_series_gives_code_and_is_required(self):
        res = self.create(self.data(sheetTypeId=str(self.ingenio.id), number=3))
        self.assertEqual(res.status_code, 400)
        self.assertIn("seriesId", res.get_json())
        res = self.create(self.data(sheetTypeId=str(self.ingenio.id), number=3,
                                    seriesId=str(self.series.id)))
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["code"], "IM{}-3".format(self.series.code))

    # --- Rechazos ---

    def test_duplicate_is_rejected_before_receiving_the_file(self):
        self.assertEqual(self.create().status_code, 201)
        res = self.create()
        self.assert_error(res, 409, "number", "112")
        from app.models.vademecum import VademecumSheet
        self.assertEqual(VademecumSheet.objects.count(), 1)

    def test_invalid_files(self):
        self.assert_error(self.create(content=b"no es un pdf"), 400, "file", "115")
        self.assert_error(self.create(content=b"%PDF-1.7\nbasura"), 400, "file", "115")
        self.assert_error(self.create(content=False), 400, "file", "2")
        from app.models.vademecum import VademecumSheet
        self.assertEqual(VademecumSheet.objects.count(), 0)
        self.assertEqual(os.listdir(os.path.join(self.storage, "incoming")), [])

    def test_too_large_is_rejected_before_reading(self):
        self.app.config["VADEMECUM_MAX_UPLOAD_MB"] = 1
        res = self.create(content=b"%PDF-" + b"0" * (2 * 1024 * 1024))
        self.assert_error(res, 400, "file", "115")

    def test_invalid_data(self):
        self.assertEqual(self.create(raw="{no json").status_code, 400)
        res = self.create({"title": u"Sin número", "sheetTypeId": str(self.hora.id)})
        self.assertEqual(res.status_code, 400)
        self.assertIn("number", res.get_json())
        res = self.create(self.data(sheetTypeId="5f0000000000000000000000"))
        self.assertIn("sheetTypeId", res.get_json())
        res = self.create(self.data(areaIds=["5f0000000000000000000000"]))
        self.assertIn("areaIds", res.get_json())
        res = self.create(self.data(grades=["9"]))
        self.assertIn("grades", res.get_json())

    def test_failure_building_files_leaves_nothing(self):
        from unittest import mock
        from app.services.vademecum import sheet_media
        with mock.patch.object(sheet_media, "build_sheet_files", side_effect=RuntimeError("x")):
            with self.assertRaises(RuntimeError):
                self.create()
        from app.models.vademecum import VademecumSheet
        self.assertEqual(VademecumSheet.objects.count(), 0)
        self.assertEqual(os.listdir(os.path.join(self.storage, "incoming")), [])

    def test_requires_the_permission(self):
        self.assertIn(self.create(headers={}).status_code, (401, 403))
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        self.assertEqual(self.create(headers=self.headers(coordinator)).status_code, 403)

    def test_old_upload_routes_are_gone(self):
        res = self.client.get("/vademecum/admin/uploads", headers=self.adminHeaders)
        self.assertEqual(res.status_code, 404)
