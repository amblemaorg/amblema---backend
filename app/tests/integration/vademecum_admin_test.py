# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_admin_test.py
"""Administración de fichas, tipos, áreas y textos del sitio (API-12)."""

import json
import os
import unittest
from datetime import datetime

from bson import ObjectId

from app.tests.integration.vademecum_upload_test import VademecumUploadBase


class VademecumAdminBase(VademecumUploadBase):

    def call(self, method, path, data=None, headers=None):
        return self.client.open("/vademecum/admin" + path, method=method,
                                headers=self.adminHeaders if headers is None else headers,
                                data=json.dumps(data) if data is not None else None,
                                content_type="application/json")

    def sheet(self, number, sheetType=None, **extra):
        from app.models.vademecum import SheetFile, VademecumSheet
        data = dict(sheetType=sheetType or self.hora, number=number,
                    title=u"Ficha {}".format(number), description=u"Descripción",
                    grades=["3"], file=SheetFile(pdfPath="sheets/{}.pdf".format(number)))
        data.update(extra)
        sheet = VademecumSheet(**data)
        sheet.save()
        return sheet


class VademecumAdminPermissionTest(VademecumAdminBase):

    def test_every_admin_route_requires_an_admin(self):
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        sheet = self.sheet(1)
        routes = [("GET", "/sheet-types"), ("POST", "/sheet-types"), ("GET", "/areas"),
                  ("POST", "/areas"), ("GET", "/sheets"), ("POST", "/sheets/publish"),
                  ("GET", "/sheets/{}".format(sheet.id)), ("PUT", "/sheets/{}".format(sheet.id)),
                  ("DELETE", "/sheets/{}".format(sheet.id)),
                  ("POST", "/sheets/{}/publish".format(sheet.id)),
                  ("POST", "/sheets/{}/unpublish".format(sheet.id)),
                  ("GET", "/sheets/{}/file".format(sheet.id)), ("GET", "/site-content"),
                  ("PUT", "/site-content/home")]
        for method, path in routes:
            self.assertEqual(self.call(method, path, {}, headers={}).status_code, 401, path)
            self.assertEqual(self.call(method, path, {}, headers=self.headers(coordinator))
                             .status_code, 403, path)
        sheet.reload()
        self.assertFalse(sheet.isDeleted)


class VademecumAdminSheetTypeTest(VademecumAdminBase):

    def payload(self, **extra):
        data = {"name": u"Lectura Viva", "headerName": u"Lectura Viva", "codePrefix": "lv",
                "color": "#AA00CC", "sort": 5, "sectionTitle": u"Lectura",
                "series": [{"name": u"1.º y 2.º", "code": "12", "grades": ["1", "2"]}]}
        data.update(extra)
        return data

    def test_list_includes_inactive_types_with_sheet_counts(self):
        self.ingenio.status = "2"
        self.ingenio.save()
        self.sheet(1)
        self.sheet(2)
        records = self.call("GET", "/sheet-types").get_json()["records"]
        byPrefix = {r["codePrefix"]: r for r in records}
        self.assertEqual(byPrefix["IM"]["status"], "2")
        self.assertEqual(byPrefix["HT"]["sheetCount"], 2)
        self.assertEqual(byPrefix["HT"]["headerName"], u"Hora TAL")

    def test_create_validates_and_normalizes(self):
        res = self.call("POST", "/sheet-types", self.payload())
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual((body["codePrefix"], body["status"], body["sheetCount"]), ("LV", "1", 0))
        self.assertEqual(body["series"][0]["code"], "12")
        self.assertEqual(self.call("POST", "/sheet-types", self.payload()).get_json(),
                         {"codePrefix": [{"status": "1", "msg": "Duplicated record found"}]})
        bad = self.call("POST", "/sheet-types", self.payload(codePrefix="X", color="rojo",
                                                              name=""))
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(set(bad.get_json()), {"color", "name"})

    def test_duplicated_series_codes_are_rejected(self):
        series = [{"name": "A", "code": "12", "grades": ["1"]},
                  {"name": "B", "code": "12", "grades": ["2"]}]
        res = self.call("POST", "/sheet-types", self.payload(series=series))
        self.assertEqual(res.status_code, 400)
        self.assertIn("series", res.get_json())

    def test_changing_codes_recomputes_sheet_codes(self):
        third = self.ingenio.series[0]
        sheet = self.sheet(7, self.ingenio, seriesId=third.id)
        self.assertEqual(sheet.code, "IM34-7")
        series = [{"id": str(s.id), "name": s.name, "code": "X" + s.code, "grades": s.grades,
                   "sort": s.sort} for s in self.ingenio.series]
        res = self.call("PUT", "/sheet-types/{}".format(self.ingenio.id), {
            "name": u"Ingenio Matemático", "headerName": u"Ingenio Matemático",
            "codePrefix": "IN", "color": "#2F80ED", "sort": 2, "series": series})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        sheet.reload()
        self.assertEqual(sheet.code, "INX34-7")

    def test_series_with_sheets_is_hidden_not_removed(self):
        used, unused = self.ingenio.series
        self.sheet(1, self.ingenio, seriesId=used.id)
        res = self.call("PUT", "/sheet-types/{}".format(self.ingenio.id), {
            "name": u"Ingenio Matemático", "headerName": u"Ingenio Matemático",
            "codePrefix": "IM", "color": "#2F80ED", "sort": 2, "series": []})
        self.assertEqual(res.get_json()["series"], [])
        self.ingenio.reload()
        self.assertEqual([(str(s.id), s.isDeleted) for s in self.ingenio.series],
                         [(str(used.id), True)])

    def test_unknown_series_id_is_rejected(self):
        res = self.call("PUT", "/sheet-types/{}".format(self.hora.id), self.payload(
            series=[{"id": str(ObjectId()), "name": "A", "code": "1", "grades": []}]))
        self.assertEqual(res.status_code, 400)

    def test_type_with_sheets_cannot_be_deleted(self):
        self.sheet(1)
        res = self.call("DELETE", "/sheet-types/{}".format(self.hora.id))
        self.assertEqual((res.status_code, res.get_json()["general"][0]["status"]), (409, "119"))
        self.assertEqual(self.call("DELETE", "/sheet-types/{}".format(self.ingenio.id))
                         .status_code, 204)
        self.assertEqual(self.call("PUT", "/sheet-types/{}".format(self.ingenio.id),
                                   self.payload()).status_code, 404)


class VademecumAdminAreaTest(VademecumAdminBase):

    def test_area_crud_and_delete_removes_it_from_sheets(self):
        res = self.call("POST", "/areas", {"name": u"Ortografía", "sort": 9})
        self.assertEqual(res.status_code, 201)
        areaId = res.get_json()["id"]
        self.assertEqual(self.call("POST", "/areas", {"name": u"Ortografía", "sort": 1})
                         .get_json(), {"name": [{"status": "1",
                                                 "msg": "Duplicated record found"}]})
        from app.models.vademecum import VademecumArea
        area = VademecumArea.objects.get(id=areaId)
        sheet = self.sheet(1, areas=[area])
        res = self.call("PUT", "/areas/{}".format(areaId),
                        {"name": u"Ortografía y acentos", "sort": 9, "status": "2"})
        self.assertEqual((res.get_json()["status"], res.get_json()["sheetCount"]), ("2", 1))
        self.assertEqual(self.call("DELETE", "/areas/{}".format(areaId)).status_code, 204)
        sheet.reload()
        self.assertEqual(sheet.areas, [])
        names = [a["name"] for a in self.call("GET", "/areas").get_json()["records"]]
        self.assertNotIn(u"Ortografía y acentos", names)


class VademecumAdminSheetTest(VademecumAdminBase):

    def test_list_shows_every_status_with_filters(self):
        self.sheet(1)
        self.sheet(2, status="published", publishedAt=datetime(2026, 11, 1))
        self.sheet(3, status="unpublished")
        self.sheet(4, isDeleted=True)
        self.sheet(5, title=u"Lectura de poesía")
        body = self.call("GET", "/sheets").get_json()
        self.assertEqual([r["code"] for r in body["records"]],
                         ["HT-1", "HT-2", "HT-3", "HT-5"])
        self.assertEqual(body["records"][1]["status"], "published")
        drafts = self.call("GET", "/sheets?status=draft").get_json()["records"]
        self.assertEqual([r["code"] for r in drafts], ["HT-1", "HT-5"])
        found = self.call("GET", "/sheets?q=POES").get_json()["records"]
        self.assertEqual([r["code"] for r in found], ["HT-5"])
        self.assertEqual(self.call("GET", "/sheets?q=.*").get_json()["records"], [])

    def test_edit_sheet(self):
        sheet = self.sheet(1)
        lectora = self.call("GET", "/areas").get_json()["records"][0]["id"]
        res = self.call("PUT", "/sheets/{}".format(sheet.id), {
            "number": 41, "title": u"Identifica la palabra", "grades": ["3", "4"],
            "areaIds": [lectora]})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        body = res.get_json()
        self.assertEqual((body["code"], body["title"], body["grades"]),
                         ("HT-41", u"Identifica la palabra", ["3", "4"]))
        self.assertEqual(body["areas"][0]["id"], lectora)
        self.assertEqual(self.call("PUT", "/sheets/{}".format(sheet.id),
                                   {"areaIds": [str(ObjectId())]}).status_code, 400)

    def test_duplicated_number_answers_112(self):
        self.sheet(1)
        sheet = self.sheet(2)
        res = self.call("PUT", "/sheets/{}".format(sheet.id), {"number": 1})
        self.assertEqual((res.status_code, res.get_json()["number"][0]["status"]), (409, "112"))

    def test_moving_to_a_type_with_series_requires_one(self):
        sheet = self.sheet(1)
        res = self.call("PUT", "/sheets/{}".format(sheet.id),
                        {"sheetTypeId": str(self.ingenio.id)})
        self.assertEqual(res.status_code, 400)
        self.assertIn("seriesId", res.get_json())
        res = self.call("PUT", "/sheets/{}".format(sheet.id),
                        {"sheetTypeId": str(self.ingenio.id),
                         "seriesId": str(self.ingenio.series[1].id)})
        self.assertEqual(res.get_json()["code"], "IM56-1")

    def test_publish_and_unpublish(self):
        sheet = self.sheet(1, description=None)
        res = self.call("POST", "/sheets/{}/publish".format(sheet.id))
        self.assertEqual((res.status_code, res.get_json()["description"][0]["status"]),
                         (400, "113"))
        self.call("PUT", "/sheets/{}".format(sheet.id), {"description": u"Texto"})
        res = self.call("POST", "/sheets/{}/publish".format(sheet.id))
        self.assertEqual(res.get_json()["status"], "published")
        publishedAt = res.get_json()["publishedAt"]
        self.assertIsNotNone(publishedAt)
        self.assertEqual(self.client.get("/vademecum/sheets/{}".format(sheet.id)).status_code,
                         200)
        # Publicada no puede quedar sin descripción
        self.assertEqual(self.call("PUT", "/sheets/{}".format(sheet.id),
                                   {"description": None}).status_code, 400)

        res = self.call("POST", "/sheets/{}/unpublish".format(sheet.id))
        self.assertEqual(res.get_json()["status"], "unpublished")
        self.assertEqual(self.client.get("/vademecum/sheets/{}".format(sheet.id)).status_code,
                         404)
        again = self.call("POST", "/sheets/{}/publish".format(sheet.id)).get_json()
        self.assertEqual(again["publishedAt"], publishedAt)

    def test_publish_many_reports_each_sheet(self):
        ready = self.sheet(1)
        missing = self.sheet(2, grades=[])
        res = self.call("POST", "/sheets/publish",
                        {"sheetIds": [str(ready.id), str(missing.id), str(ObjectId())]})
        body = res.get_json()
        self.assertEqual(body["published"], [str(ready.id)])
        self.assertEqual([f["sheetId"] for f in body["failed"]][0], str(missing.id))
        self.assertEqual(body["failed"][0]["errors"]["grades"][0]["status"], "113")
        self.assertEqual(body["failed"][1]["errors"]["general"][0]["status"], "5")
        self.assertEqual(self.call("POST", "/sheets/publish", {"sheetIds": []}).status_code,
                         400)

    def test_delete_is_logical_and_keeps_downloads(self):
        from app.models.vademecum import VademecumSheet
        sheet = self.sheet(1, status="published", publishedAt=datetime(2026, 11, 1))
        self.assertEqual(self.call("DELETE", "/sheets/{}".format(sheet.id)).status_code, 204)
        self.assertTrue(VademecumSheet.objects.get(id=sheet.id).isDeleted)
        self.assertEqual(self.call("GET", "/sheets/{}".format(sheet.id)).status_code, 404)
        self.assertEqual(self.client.get("/vademecum/sheets/{}".format(sheet.id)).status_code,
                         404)

    def test_admin_can_review_the_pdf_of_a_draft(self):
        from app.models.vademecum import VademecumDownload
        sheet = self.sheet(1)
        os.makedirs(os.path.join(self.storage, "sheets"))
        with open(os.path.join(self.storage, "sheets", "1.pdf"), "wb") as handle:
            handle.write(b"%PDF-1.4 borrador")
        res = self.call("GET", "/sheets/{}/file".format(sheet.id))
        self.assertEqual((res.status_code, res.get_data()), (200, b"%PDF-1.4 borrador"))
        res.close()
        self.assertEqual(VademecumDownload.objects.count(), 0)


class VademecumAdminSiteContentTest(VademecumAdminBase):

    def test_site_content_is_sanitized(self):
        keys = [r["key"] for r in self.call("GET", "/site-content").get_json()["records"]]
        self.assertEqual(keys, ["about", "access_request", "home"])
        body = (u'<p onclick="x()">Hola <strong>docente</strong><script>alert(1)</script></p>'
                u'<a href="javascript:alert(1)">mal</a><a href="https://amblema.org">bien</a>'
                u'<img src=x onerror=alert(1)><h2 style="color:red">Título</h2>')
        res = self.call("PUT", "/site-content/home", {"title": u"Bienvenida", "body": body})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["body"],
                         u'<p>Hola <strong>docente</strong></p><a>mal</a>'
                         u'<a href="https://amblema.org" target="_blank" '
                         u'rel="noopener noreferrer">bien</a><h2>Título</h2>')
        self.assertEqual(self.call("PUT", "/site-content/otra", {"title": "x"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
