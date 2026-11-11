# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_catalog_test.py
"""Catálogo público y búsqueda (API-13)."""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database


class VademecumCatalogTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes, seed_vademecum
        ensure_vademecum_indexes()
        seed_vademecum()
        self.client = self.app.test_client()
        from app.models.vademecum import VademecumArea, VademecumSheetType
        self.hora = VademecumSheetType.objects(codePrefix="HT").first()
        self.ingenio = VademecumSheetType.objects(codePrefix="IM").first()
        self.lectora = VademecumArea.objects(name=u"Comprensión lectora").first()
        self.geometria = VademecumArea.objects(name=u"Geometría").first()
        self.storage = tempfile.mkdtemp()
        self.app.config["VADEMECUM_STORAGE_PATH"] = self.storage
        self.base = datetime(2026, 11, 1)

    def tearDown(self):
        shutil.rmtree(self.storage, ignore_errors=True)
        drop_testing_database(self.db)
        self.context.pop()

    def sheet(self, sheetType, number, status="published", days=0, **extra):
        from app.models.vademecum import SheetFile, VademecumSheet
        data = dict(sheetType=sheetType, number=number, title=u"Ficha {}".format(number),
                    description=u"Descripción", grades=["3"], status=status,
                    publishedAt=self.base + timedelta(days=days),
                    file=SheetFile(pdfPath="sheets/{}.pdf".format(number), sizeBytes=1000,
                                   pageCount=2, thumbnailPath="thumbs/{}.webp".format(number),
                                   previewPath="previews/{}.webp".format(number)),
                    searchText=u"texto oculto de la ficha")
        data.update(extra)
        sheet = VademecumSheet(**data)
        sheet.save()
        return sheet

    def get(self, path, **params):
        return self.client.get(path, query_string=params)

    def codes(self, res):
        return [r["code"] for r in res.get_json()["records"]]

    # --- Opciones ---

    def test_catalog_options_lists_active_types_series_areas_and_grades(self):
        self.hora.status = "2"
        self.hora.save()
        body = self.get("/vademecum/catalog-options").get_json()
        prefixes = [t["codePrefix"] for t in body["sheetTypes"]]
        self.assertEqual(prefixes, ["IM", "MX", "AM"])
        self.assertEqual([s["code"] for s in body["sheetTypes"][0]["series"]], ["34", "56"])
        self.assertEqual(body["sheetTypes"][0]["series"][0]["grades"], ["3", "4"])
        self.assertEqual(len(body["areas"]), 4)
        self.assertEqual(body["grades"][0], {"value": "0", "label": "Preescolar"})
        self.assertEqual(body["grades"][-1], {"value": "all", "label": "Todos"})

    # --- Listado ---

    def test_only_published_sheets_are_listed(self):
        self.sheet(self.hora, 1)
        self.sheet(self.hora, 2, status="draft")
        self.sheet(self.hora, 3, status="unpublished")
        self.sheet(self.hora, 4, isDeleted=True)
        res = self.get("/vademecum/sheets")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.codes(res), ["HT-1"])
        self.assertEqual(res.get_json()["pagination"],
                         {"page": 1, "pageSize": 20, "total": 1, "pages": 1})

    def test_summary_is_light_and_never_exposes_the_pdf(self):
        self.sheet(self.ingenio, 7, seriesId=self.ingenio.series[0].id,
                   areas=[self.lectora], ratingCount=2, ratingSum=9)
        record = self.get("/vademecum/sheets").get_json()["records"][0]
        self.assertEqual(record["code"], "IM34-7")
        self.assertEqual(record["series"]["code"], "34")
        self.assertEqual(record["sheetType"]["codePrefix"], "IM")
        self.assertEqual(record["areas"], [{"id": str(self.lectora.id),
                                            "name": u"Comprensión lectora"}])
        self.assertEqual((record["ratingAverage"], record["ratingCount"]), (4.5, 2))
        self.assertTrue(record["thumbnailUrl"].startswith(
            "/vademecum/sheets/{}/thumbnail.webp?v=".format(record["id"])))
        raw = str(record)
        for hidden in (".pdf", "pdfPath", "searchText", "texto oculto", "description"):
            self.assertNotIn(hidden, raw)

    def test_filter_by_type_and_series(self):
        self.sheet(self.hora, 1)
        self.sheet(self.ingenio, 1, seriesId=self.ingenio.series[0].id)
        self.sheet(self.ingenio, 2, seriesId=self.ingenio.series[1].id)
        self.assertEqual(sorted(self.codes(self.get("/vademecum/sheets",
                                                    sheetTypeId=str(self.ingenio.id)))),
                         ["IM34-1", "IM56-2"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets",
                                             seriesId=str(self.ingenio.series[1].id))),
                         ["IM56-2"])

    def test_filter_by_grades_always_includes_all(self):
        self.sheet(self.hora, 1, grades=["3"])
        self.sheet(self.hora, 2, grades=["5"])
        self.sheet(self.hora, 3, grades=["all"])
        self.sheet(self.hora, 4, grades=["4", "5"])
        res = self.client.get("/vademecum/sheets?grade=3&grade=4&sort=number")
        self.assertEqual(self.codes(res), ["HT-1", "HT-3", "HT-4"])

    def test_filter_by_area(self):
        self.sheet(self.hora, 1, areas=[self.lectora])
        self.sheet(self.hora, 2, areas=[self.geometria])
        self.sheet(self.hora, 3)
        res = self.get("/vademecum/sheets", areaId=str(self.geometria.id))
        self.assertEqual(self.codes(res), ["HT-2"])

    def test_sorts(self):
        self.sheet(self.hora, 1, days=1, downloadCount=5)
        self.sheet(self.hora, 2, days=3, downloadCount=1)
        self.sheet(self.hora, 3, days=2, downloadCount=9)
        self.assertEqual(self.codes(self.get("/vademecum/sheets")), ["HT-2", "HT-3", "HT-1"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", sort="number")),
                         ["HT-1", "HT-2", "HT-3"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", sort="popular")),
                         ["HT-3", "HT-1", "HT-2"])

    def test_spanish_search_with_relevance(self):
        self.sheet(self.hora, 1, title=u"Lectura de cuentos", description=u"Problemas geométricos sencillos")
        self.sheet(self.hora, 2, title=u"Problemas geométricos", description=u"Figuras")
        self.sheet(self.hora, 3, title=u"Sumas", description=u"Operaciones")
        res = self.get("/vademecum/sheets", q="geometricos", sort="relevance")
        self.assertEqual(self.codes(res), ["HT-2", "HT-1"])
        self.assertEqual(sorted(self.codes(self.get("/vademecum/sheets", q="oculto"))),
                         ["HT-1", "HT-2", "HT-3"])

    def test_pagination(self):
        for n in range(1, 6):
            self.sheet(self.hora, n, days=n)
        res = self.get("/vademecum/sheets", page=2, pageSize=2)
        self.assertEqual(self.codes(res), ["HT-3", "HT-2"])
        self.assertEqual(res.get_json()["pagination"],
                         {"page": 2, "pageSize": 2, "total": 5, "pages": 3})

    def test_invalid_parameters_answer_400(self):
        cases = ({"sheetTypeId": "x"}, {"grade": "9"}, {"areaId": "x"}, {"sort": "relevance"},
                 {"sort": "rare"}, {"pageSize": 101}, {"page": 0}, {"page": "a"},
                 {"q": "a" * 101})
        for params in cases:
            res = self.get("/vademecum/sheets", **params)
            self.assertEqual(res.status_code, 400, params)

    # --- Detalle ---

    def test_detail_of_published_sheet(self):
        sheet = self.sheet(self.hora, 41)
        from app.models.vademecum import VademecumRating, VademecumTeacherAccount
        for i, status in enumerate(("approved", "pending", "approved")):
            account = VademecumTeacherAccount(email="d{}@test.com".format(i), firstName="A",
                                              lastName="B", status="1")
            account.save()
            VademecumRating(account=account, sheet=sheet, stars=5, comment="Bien",
                            commentStatus=status).save()
        body = self.get("/vademecum/sheets/{}".format(sheet.id)).get_json()
        self.assertEqual(body["code"], "HT-41")
        self.assertEqual((body["description"], body["pageCount"], body["sizeBytes"]),
                         (u"Descripción", 2, 1000))
        self.assertEqual(body["commentCount"], 2)
        self.assertNotIn("pdf", str(body).lower())

    def test_detail_of_hidden_or_unknown_sheet_is_404(self):
        draft = self.sheet(self.hora, 1, status="draft")
        for sheetId in (str(draft.id), str(ObjectId()), "x"):
            res = self.get("/vademecum/sheets/{}".format(sheetId))
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.get_json()["general"][0]["status"], "5")

    # --- Imágenes ---

    def write(self, relative, content=b"RIFFwebp"):
        path = os.path.join(self.storage, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)

    def test_thumbnail_and_preview_are_served_with_long_cache(self):
        sheet = self.sheet(self.hora, 1)
        self.write("thumbs/1.webp", b"thumb")
        self.write("previews/1.webp", b"preview")
        res = self.get("/vademecum/sheets/{}/thumbnail.webp".format(sheet.id))
        self.assertEqual((res.status_code, res.data, res.mimetype), (200, b"thumb", "image/webp"))
        self.assertIn("max-age=31536000", res.headers["Cache-Control"])
        res.close()
        res = self.get("/vademecum/sheets/{}/preview.webp".format(sheet.id))
        self.assertEqual(res.data, b"preview")
        res.close()

    def test_images_of_unpublished_sheets_or_outside_storage_are_404(self):
        draft = self.sheet(self.hora, 1, status="draft")
        self.write("thumbs/1.webp")
        self.assertEqual(self.get("/vademecum/sheets/{}/thumbnail.webp".format(draft.id))
                         .status_code, 404)
        from app.models.vademecum import SheetFile
        outside = self.sheet(self.hora, 2, file=SheetFile(pdfPath="x.pdf",
                                                          thumbnailPath="../../etc/passwd"))
        self.assertEqual(self.get("/vademecum/sheets/{}/thumbnail.webp".format(outside.id))
                         .status_code, 404)
        missing = self.sheet(self.hora, 3)
        self.assertEqual(self.get("/vademecum/sheets/{}/preview.webp".format(missing.id))
                         .status_code, 404)

    def test_pdf_has_no_public_route(self):
        sheet = self.sheet(self.hora, 1)
        self.write("sheets/1.pdf", b"%PDF")
        for path in ("/vademecum/sheets/{}/file", "/vademecum/sheets/{}/download",
                     "/vademecum/sheets/{}/sheet.pdf"):
            res = self.get(path.format(sheet.id))
            self.assertIn(res.status_code, (404, 405))
            self.assertNotIn(b"%PDF", res.data)


if __name__ == "__main__":
    unittest.main()
