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

    def test_catalog_options_lists_active_types_areas_and_grades(self):
        self.hora.status = "2"
        self.hora.save()
        body = self.get("/vademecum/catalog-options").get_json()
        prefixes = [t["codePrefix"] for t in body["sheetTypes"]]
        self.assertEqual(prefixes, ["IM", "MX", "AM"])
        self.assertNotIn("series", body["sheetTypes"][0])
        self.assertEqual(len(body["areas"]), 4)
        # Cada área dice a qué tipos aplica, para filtrar en la web docente
        self.assertEqual(body["areas"][0]["sheetTypeIds"], [str(self.hora.id)])
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
        self.sheet(self.ingenio, 7, areas=[self.lectora], ratingCount=2, ratingSum=9)
        record = self.get("/vademecum/sheets").get_json()["records"][0]
        self.assertEqual(record["code"], "IM-7")
        self.assertNotIn("series", record)
        self.assertEqual(record["sheetType"]["codePrefix"], "IM")
        self.assertEqual(record["areas"], [{"id": str(self.lectora.id),
                                            "name": u"Comprensión lectora"}])
        self.assertEqual((record["ratingAverage"], record["ratingCount"]), (4.5, 2))
        self.assertTrue(record["thumbnailUrl"].startswith(
            "/vademecum/sheets/{}/thumbnail.webp?v=".format(record["id"])))
        self.assertEqual(record["description"], u"Descripción")
        raw = str(record)
        for hidden in (".pdf", "pdfPath", "searchText", "texto oculto"):
            self.assertNotIn(hidden, raw)

    def test_filter_by_type(self):
        self.sheet(self.hora, 1)
        self.sheet(self.ingenio, 1)
        self.sheet(self.ingenio, 2)
        self.assertEqual(sorted(self.codes(self.get("/vademecum/sheets",
                                                    sheetTypeId=str(self.ingenio.id)))),
                         ["IM-1", "IM-2"])

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

    def test_home_without_published_sheets_has_empty_comments(self):
        body = self.get("/vademecum/home").get_json()
        self.assertEqual(body["comments"], [])
        self.assertIsNone(body["ratingSummary"]["average"])
        self.assertEqual(body["ratingSummary"]["count"], 0)

    def test_only_new_and_only_popular_work_without_aggregation(self):
        now = datetime.utcnow()
        self.sheet(self.hora, 1, publishedAt=now - timedelta(days=1), downloadCount=3)
        self.sheet(self.hora, 2, publishedAt=now - timedelta(days=60), downloadCount=3)
        self.sheet(self.hora, 3, publishedAt=now - timedelta(days=1), downloadCount=0)
        self.assertCountEqual(self.codes(self.get("/vademecum/sheets", onlyNew=1)),
                              ["HT-1", "HT-3"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", onlyPopular=1)),
                         ["HT-1", "HT-2"])

    def test_aggregated_filters_by_type_grade_area_and_popular(self):
        self.sheet(self.hora, 1, areas=[self.lectora], grades=["3"],
                   downloadCount=2, ratingSum=5, ratingCount=1)
        self.sheet(self.ingenio, 2, areas=[self.lectora], grades=["3"],
                   downloadCount=2, ratingSum=5, ratingCount=1)
        self.sheet(self.hora, 3, areas=[self.geometria], grades=["4"],
                   downloadCount=0, ratingSum=5, ratingCount=1)
        res = self.get("/vademecum/sheets", sheetTypeId=str(self.hora.id), grade="3",
                       areaId=str(self.lectora.id), onlyPopular=1, sort="rating")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(self.codes(res), ["HT-1"])
        self.assertEqual(res.get_json()["pagination"]["total"], 1)

    def test_aggregated_search_by_code_and_text(self):
        for number in (1, 2, 10):
            self.sheet(self.hora, number, ratingSum=5, ratingCount=1)
        self.assertCountEqual(self.codes(self.get(
            "/vademecum/sheets", q="HT-1", sort="rating")), ["HT-1", "HT-10"])
        self.assertEqual(sorted(self.codes(self.get(
            "/vademecum/sheets", q="oculto", sort="rating"))), ["HT-1", "HT-10", "HT-2"])

    def test_aggregated_sorts_keep_number_popular_and_newest(self):
        self.sheet(self.hora, 1, days=1, downloadCount=5, ratingSum=9, ratingCount=2)
        self.sheet(self.hora, 2, days=3, downloadCount=1, ratingSum=8, ratingCount=2)
        self.sheet(self.hora, 3, days=2, downloadCount=9, ratingSum=7, ratingCount=2)
        self.assertEqual(self.codes(self.get("/vademecum/sheets", minRating="rated")),
                         ["HT-2", "HT-3", "HT-1"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", minRating="rated",
                                             sort="number")), ["HT-1", "HT-2", "HT-3"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", minRating="rated",
                                             sort="popular")), ["HT-3", "HT-1", "HT-2"])
        res = self.get("/vademecum/sheets", q="oculto", minRating="rated", sort="relevance")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(sorted(self.codes(res)), ["HT-1", "HT-2", "HT-3"])

    def test_only_commented_and_rated_filters_in_aggregation(self):
        from app.models.vademecum import VademecumRating, VademecumTeacherAccount
        rated = self.sheet(self.hora, 1, ratingSum=5, ratingCount=1)
        self.sheet(self.hora, 2)
        account = VademecumTeacherAccount(email="comentario@test.com", firstName="A",
                                          lastName="B", status="1")
        account.save()
        VademecumRating(account=account, sheet=rated, stars=5, comment=u"Bien",
                        commentStatus="approved").save()
        self.assertEqual(self.codes(self.get("/vademecum/sheets", onlyCommented=1)), ["HT-1"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", minRating="rated")), ["HT-1"])

    def test_home_indicators_match_catalog(self):
        from app.models.vademecum import VademecumDownload, VademecumSheet, VademecumTeacherAccount
        from app.tests.fixtures import create_school_year, enroll_vademecum_teacher
        year = create_school_year()
        enroll_vademecum_teacher(year, "ana@escuela.test", grades=("3",))
        enroll_vademecum_teacher(year, "juan@escuela.test", grades=("4",))
        self.sheet(self.hora, 1)
        indicators = self.get("/vademecum/home").get_json()["indicators"]
        self.assertEqual(set(indicators), {"sheets", "teachers", "schools", "downloads"})
        self.assertEqual(indicators["sheets"],
                         VademecumSheet.objects(status="published", isDeleted=False).count())
        self.assertEqual(indicators["teachers"],
                         VademecumTeacherAccount.objects(status="1", isDeleted=False).count())
        self.assertEqual(indicators["downloads"],
                         VademecumDownload.objects(isRedownload=False).count())
        # Cada alta crea una escuela con PECA del año: dos escuelas activas, no dos docentes
        self.assertEqual(indicators["schools"], 2)

    def test_list_sheets_multiple_types_paginates_server_side(self):
        for number in range(1, 41):
            self.sheet(self.hora if number <= 20 else self.ingenio, number)
        res = self.get("/vademecum/sheets",
                       sheetTypeId=[str(self.hora.id), str(self.ingenio.id)],
                       page=2, pageSize=20)
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(len(res.get_json()["records"]), 20)
        self.assertEqual(res.get_json()["pagination"],
                         {"page": 2, "pageSize": 20, "total": 40, "pages": 2})

    def test_list_sheets_sort_rating_uses_average(self):
        self.sheet(self.hora, 1, ratingSum=9, ratingCount=2)  # 4,5
        self.sheet(self.hora, 2, ratingSum=5, ratingCount=1)  # 5,0
        res = self.get("/vademecum/sheets", sort="rating")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(self.codes(res), ["HT-2", "HT-1"])
        self.assertEqual(res.get_json()["records"][0]["ratingAverage"], 5.0)

    def test_list_sheets_filters_combine(self):
        from app.models.vademecum import VademecumRating, VademecumTeacherAccount
        now = datetime.utcnow()
        recent = self.sheet(self.hora, 1, publishedAt=now - timedelta(days=10),
                            ratingSum=9, ratingCount=2)
        self.sheet(self.hora, 2, publishedAt=now - timedelta(days=60),
                   ratingSum=9, ratingCount=2)
        for index, status in enumerate(("approved", "hidden")):
            account = VademecumTeacherAccount(email="c{}@test.com".format(index),
                                              firstName="A", lastName="B", status="1")
            account.save()
            VademecumRating(account=account, sheet=recent, stars=5, comment="Texto",
                            commentStatus=status).save()
        res = self.get("/vademecum/sheets", onlyNew=1, minRating=4, sort="commented")
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(self.codes(res), ["HT-1"])
        self.assertEqual(res.get_json()["records"][0]["commentCount"], 1)

    def test_spanish_search_with_relevance(self):
        self.sheet(self.hora, 1, title=u"Lectura de cuentos", description=u"Problemas geométricos sencillos")
        self.sheet(self.hora, 2, title=u"Problemas geométricos", description=u"Figuras")
        self.sheet(self.hora, 3, title=u"Sumas", description=u"Operaciones")
        res = self.get("/vademecum/sheets", q="geometricos", sort="relevance")
        self.assertEqual(self.codes(res), ["HT-2", "HT-1"])
        self.assertEqual(sorted(self.codes(self.get("/vademecum/sheets", q="oculto"))),
                         ["HT-1", "HT-2", "HT-3"])

    def test_search_by_code(self):
        for n in (1, 2, 10, 12):
            self.sheet(self.ingenio, n)
        self.sheet(self.hora, 41, title=u"Identifica la palabra")
        self.sheet(self.hora, 4, title=u"Rimas", status="draft")  # no publicada: no aparece
        # Código que empieza por: en orden de número (10 antes que 12) con relevancia
        self.assertEqual(self.codes(self.get("/vademecum/sheets", q="IM-1", sort="relevance")),
                         ["IM-1", "IM-10", "IM-12"])
        # Sin mayúsculas y con o sin guion
        self.assertEqual(sorted(self.codes(self.get("/vademecum/sheets", q="im1"))),
                         ["IM-1", "IM-10", "IM-12"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", q="IM-2")), ["IM-2"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", q="ht41")), ["HT-41"])
        self.assertEqual(self.codes(self.get("/vademecum/sheets", q="HT-4")), ["HT-41"])
        # Una palabra sigue siendo búsqueda de texto
        self.assertEqual(self.codes(self.get("/vademecum/sheets", q="palabra")), ["HT-41"])

    def test_pagination(self):
        for n in range(1, 6):
            self.sheet(self.hora, n, days=n)
        res = self.get("/vademecum/sheets", page=2, pageSize=2)
        self.assertEqual(self.codes(res), ["HT-3", "HT-2"])
        self.assertEqual(res.get_json()["pagination"],
                         {"page": 2, "pageSize": 2, "total": 5, "pages": 3})

    def test_invalid_parameters_answer_400(self):
        cases = ({"sheetTypeId": "x"}, {"grade": "9"}, {"areaId": "x"},
                 {"sort": "relevance"}, {"sort": "rare"}, {"minRating": "2"},
                  {"pageSize": 101}, {"page": 0},
                 {"page": "a"}, {"q": "a" * 101})
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

    def test_detail_still_exposes_file_metadata(self):
        """Red de seguridad: el detalle no debe perder metadatos al proyectar el listado."""
        sheet = self.sheet(self.hora, 42)
        body = self.get("/vademecum/sheets/{}".format(sheet.id)).get_json()
        self.assertEqual(body["description"], u"Descripción")
        self.assertEqual(body["pageCount"], 2)
        self.assertEqual(body["sizeBytes"], 1000)
        self.assertEqual(body["commentCount"], 0)

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

    def test_thumbnail_uses_file_paths(self):
        """Red de seguridad: la proyección de imágenes debe conservar `file.*`."""
        sheet = self.sheet(self.hora, 7)
        self.write("thumbs/7.webp", b"thumb-7")
        res = self.get("/vademecum/sheets/{}/thumbnail.webp".format(sheet.id))
        self.assertEqual((res.status_code, res.data, res.mimetype), (200, b"thumb-7", "image/webp"))
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
