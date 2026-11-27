# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_admin_test.py
"""Administración de fichas, tipos, áreas y textos del sitio (API-12)."""

import json
import os
import unittest
from datetime import datetime

from bson import ObjectId

from app.tests.integration.vademecum_base import VademecumAdminTestBase


class VademecumAdminBase(VademecumAdminTestBase):

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
                "color": "#AA00CC", "sort": 5, "sectionTitle": u"Lectura"}
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
        self.assertNotIn("series", body)
        self.assertEqual(self.call("POST", "/sheet-types", self.payload()).get_json(),
                         {"codePrefix": [{"status": "1", "msg": "Duplicated record found"}]})
        bad = self.call("POST", "/sheet-types", self.payload(codePrefix="X", color="rojo",
                                                              name=""))
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(set(bad.get_json()), {"color", "name"})

    def test_changing_prefix_recomputes_sheet_codes(self):
        sheet = self.sheet(7, self.ingenio)
        self.assertEqual(sheet.code, "IM-7")
        res = self.call("PUT", "/sheet-types/{}".format(self.ingenio.id), {
            "name": u"Ingenio Matemático", "headerName": u"Ingenio Matemático",
            "codePrefix": "IN", "color": "#2F80ED", "sort": 2})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        sheet.reload()
        self.assertEqual(sheet.code, "IN-7")

    def test_changing_prefix_updates_twenty_sheet_codes(self):
        from app.models.vademecum import VademecumSheet
        for number in range(1, 21):
            self.sheet(number, self.ingenio)
        res = self.call("PUT", "/sheet-types/{}".format(self.ingenio.id), {
            "name": u"Ingenio Matemático", "headerName": u"Ingenio Matemático",
            "codePrefix": "IN", "color": "#2F80ED", "sort": 2})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        sheets = list(VademecumSheet.objects(sheetType=self.ingenio.id, isDeleted=False))
        self.assertEqual(len(sheets), 20)
        self.assertEqual(sorted(s.code for s in sheets),
                         sorted("IN-{}".format(number) for number in range(1, 21)))
        self.assertTrue(all(s.status == "draft" for s in sheets))

    def test_series_field_is_ignored_and_bad_payloads_are_rejected(self):
        from mongoengine import ValidationError as ModelValidationError
        from app.services.vademecum.taxonomy_admin_service import _model_errors
        res = self.call("POST", "/sheet-types", self.payload(
            series=[{"name": "A", "code": "1", "grades": []}]))
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        self.assertNotIn("series", res.get_json())
        self.assertEqual(self.call("PUT", "/sheet-types/{}".format(self.hora.id), {}).status_code,
                         400)
        self.assertEqual(self.call("DELETE", "/sheet-types/{}".format(ObjectId())).status_code, 404)
        self.assertEqual(_model_errors(ModelValidationError("fallo general"))[1], 400)

    def test_type_with_sheets_cannot_be_deleted(self):
        self.sheet(1)
        res = self.call("DELETE", "/sheet-types/{}".format(self.hora.id))
        self.assertEqual((res.status_code, res.get_json()["general"][0]["status"]), (409, "119"))
        self.assertEqual(self.call("DELETE", "/sheet-types/{}".format(self.ingenio.id))
                         .status_code, 204)
        self.assertEqual(self.call("PUT", "/sheet-types/{}".format(self.ingenio.id),
                                   self.payload()).status_code, 404)


class VademecumAdminAreaTest(VademecumAdminBase):

    def area(self, name=u"Ortografía", sort=9, types=None):
        return {"name": name, "sort": sort,
                "sheetTypeIds": [str(t.id) for t in (types or [self.hora])]}

    def test_area_crud_and_delete_removes_it_from_sheets(self):
        res = self.call("POST", "/areas", self.area())
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["sheetTypes"], [{"id": str(self.hora.id), "name": u"Hora TAL"}])
        areaId = res.get_json()["id"]
        self.assertEqual(self.call("POST", "/areas", self.area(sort=1))
                         .get_json(), {"name": [{"status": "1",
                                                 "msg": "Duplicated record found"}]})
        from app.models.vademecum import VademecumArea
        area = VademecumArea.objects.get(id=areaId)
        sheet = self.sheet(1, areas=[area])
        res = self.call("PUT", "/areas/{}".format(areaId),
                        dict(self.area(u"Ortografía y acentos"), status="2"))
        self.assertEqual((res.get_json()["status"], res.get_json()["sheetCount"]), ("2", 1))
        self.assertEqual(self.call("DELETE", "/areas/{}".format(areaId)).status_code, 204)
        sheet.reload()
        self.assertEqual(sheet.areas, [])
        names = [a["name"] for a in self.call("GET", "/areas").get_json()["records"]]
        self.assertNotIn(u"Ortografía y acentos", names)
        self.assertEqual(self.call("POST", "/areas", {}).status_code, 400)
        self.assertEqual(self.call("PUT", "/areas/{}".format(areaId),
                                   self.area(u"X", 1)).status_code, 404)
        self.assertEqual(self.call("DELETE", "/areas/{}".format(areaId)).status_code, 404)

    def test_area_requires_valid_sheet_types(self):
        for types in ([], ["no-es-oid"], [str(ObjectId())]):
            res = self.call("POST", "/areas", {"name": u"Sin tipo", "sort": 1, "sheetTypeIds": types})
            self.assertEqual(res.status_code, 400, types)
            self.assertIn("sheetTypeIds", res.get_json())

    def test_removing_a_type_from_an_area_removes_it_from_those_sheets(self):
        from app.models.vademecum import VademecumArea
        areaId = self.call("POST", "/areas", self.area(types=[self.hora, self.ingenio])).get_json()["id"]
        area = VademecumArea.objects.get(id=areaId)
        lectura = self.sheet(1, areas=[area])
        calculo = self.sheet(2, self.ingenio, areas=[area])
        res = self.call("PUT", "/areas/{}".format(areaId), self.area(types=[self.hora]))
        self.assertEqual((res.status_code, res.get_json()["sheetCount"]), (200, 1))
        lectura.reload()
        calculo.reload()
        self.assertEqual(([a.id for a in lectura.areas], calculo.areas), ([area.id], []))

    def test_deleting_a_type_removes_it_from_areas(self):
        from app.models.vademecum import VademecumArea
        areaId = self.call("POST", "/areas", self.area(types=[self.hora, self.ingenio])).get_json()["id"]
        self.assertEqual(self.call("DELETE", "/sheet-types/{}".format(self.ingenio.id)).status_code, 204)
        self.assertEqual([t.id for t in VademecumArea.objects.get(id=areaId).sheetTypes], [self.hora.id])


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
        self.assertEqual(self.call("GET", "/sheets?sheetTypeId={}".format(self.hora.id))
                         .status_code, 200)
        for query in ("?status=bad", "?sheetTypeId=bad", "?q=" + "a" * 101,
                      "?page=bad", "?page=0", "?pageSize=101"):
            self.assertEqual(self.call("GET", "/sheets" + query).status_code, 400, query)

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
        # Un área de otro tipo se rechaza con 121 (Geometría es de Ingenio y Momento X)
        geometria = [a["id"] for a in self.call("GET", "/areas").get_json()["records"]
                     if a["name"] == u"Geometría"][0]
        res = self.call("PUT", "/sheets/{}".format(sheet.id), {"areaIds": [geometria]})
        self.assertEqual((res.status_code, res.get_json()["areaIds"][0]["status"]), (400, "121"))
        # También al cambiar de tipo si conserva áreas que no aplican
        res = self.call("PUT", "/sheets/{}".format(sheet.id), {"sheetTypeId": str(self.ingenio.id)})
        self.assertEqual((res.status_code, res.get_json()["areaIds"][0]["status"]), (400, "121"))
        res = self.call("PUT", "/sheets/{}".format(sheet.id),
                        {"sheetTypeId": str(self.ingenio.id), "areaIds": [geometria]})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        for bad in ({"title": ""}, {"number": 0}, {"areaIds": ["no-es-oid"]}):
            self.assertEqual(self.call("PUT", "/sheets/{}".format(sheet.id), bad).status_code, 400)

    def test_duplicated_number_answers_112(self):
        self.sheet(1)
        sheet = self.sheet(2)
        res = self.call("PUT", "/sheets/{}".format(sheet.id), {"number": 1})
        self.assertEqual((res.status_code, res.get_json()["number"][0]["status"]), (409, "112"))

    def test_moving_to_another_type_changes_the_code(self):
        sheet = self.sheet(1)
        res = self.call("PUT", "/sheets/{}".format(sheet.id),
                        {"sheetTypeId": str(self.ingenio.id)})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(res.get_json()["code"], "IM-1")

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

    def test_publish_many_keeps_the_final_state_of_twenty_sheets(self):
        from app.models.vademecum import VademecumSheet
        sheets = [self.sheet(number) for number in range(1, 21)]
        ids = [str(s.id) for s in sheets]
        res = self.call("POST", "/sheets/publish", {"sheetIds": ids})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(res.get_json(), {"published": ids, "failed": []})
        published = list(VademecumSheet.objects(id__in=[s.id for s in sheets]))
        self.assertEqual(len(published), 20)
        self.assertTrue(all(s.status == "published" and s.publishedAt for s in published))
        firstDates = {str(s.id): s.publishedAt for s in published}
        self.assertEqual(self.call("POST", "/sheets/publish", {"sheetIds": ids}).get_json(),
                         {"published": ids, "failed": []})
        for sheet in VademecumSheet.objects(id__in=[s.id for s in sheets]):
            self.assertEqual(sheet.publishedAt, firstDates[str(sheet.id)])

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
        self.assertEqual(self.call("GET", "/sheets/{}/file".format(ObjectId())).status_code, 404)


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
        self.assertEqual(self.call("PUT", "/site-content/home", {"title": "x" * 151}).status_code,
                         400)


if __name__ == "__main__":
    unittest.main()
