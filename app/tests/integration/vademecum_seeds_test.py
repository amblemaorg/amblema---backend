# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_seeds_test.py

import unittest

from mongoengine import NotUniqueError

from app import create_app
from app.tests.base import drop_testing_database


class VademecumSeedsTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.context = self.app.app_context()
        self.context.push()
        from app import db
        self.db = db
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes
        ensure_vademecum_indexes()

    def tearDown(self):
        drop_testing_database(self.db)
        self.context.pop()

    def _sheet_type(self, codePrefix="HT"):
        from app.models.vademecum import VademecumSheetType
        return VademecumSheetType.objects(codePrefix=codePrefix).first()

    def test_ensure_indexes_covers_all_models(self):
        from app.helpers.vademecum_seeds import ensure_vademecum_indexes
        from app.models.vademecum import VADEMECUM_MODELS
        self.assertEqual(len(VADEMECUM_MODELS), 10)
        self.assertEqual(ensure_vademecum_indexes(), 10)

    def test_seed_creates_catalog_once(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        from app.models.vademecum import VademecumSheetType
        self.assertEqual(seed_vademecum(), {"sheetTypes": 4, "areas": 4, "siteContent": 3})
        self.assertEqual(seed_vademecum(), {"sheetTypes": 0, "areas": 0, "siteContent": 0})
        self.assertEqual(VademecumSheetType.objects.count(), 4)
        # Ambiente se detecta por "Ecotema N: Título" en el backoffice
        self.assertEqual(self._sheet_type("AM").headerName, u"Ecotema")
        # Cada área provisional nace ligada a sus tipos de ficha
        from app.models.vademecum import VademecumArea
        geometria = VademecumArea.objects.get(name=u"Geometría")
        self.assertEqual(sorted(t.codePrefix for t in geometria.sheetTypes), ["IM", "MX"])

    def test_link_area_types_fills_only_areas_without_types(self):
        from app.helpers.vademecum_seeds import link_vademecum_area_types, seed_vademecum
        from app.models.vademecum import VademecumArea
        seed_vademecum()
        VademecumArea(name=u"Antigua", sort=9).save()
        result = link_vademecum_area_types()
        self.assertEqual((result["areas"], result["sheetTypes"]), ([u"Antigua"], 4))
        self.assertEqual(len(VademecumArea.objects.get(name=u"Antigua").sheetTypes), 4)
        self.assertEqual(len(VademecumArea.objects.get(name=u"Geografía").sheetTypes), 1)
        self.assertEqual(link_vademecum_area_types()["areas"], [])

    def test_seed_does_not_overwrite_admin_edits(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        seed_vademecum()
        hora = self._sheet_type("HT")
        hora.color = "#000000"
        hora.save()
        seed_vademecum()
        self.assertEqual(self._sheet_type("HT").color, "#000000")

    def test_seed_does_not_revive_deleted_type_or_renamed_area(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        from app.models.vademecum import VademecumSheetType, VademecumArea
        seed_vademecum()
        momento = self._sheet_type("MX")
        momento.isDeleted = True
        momento.save()
        area = VademecumArea.objects(name=u"Geometría").first()
        area.name = u"Geometría y medida"
        area.save()
        self.assertEqual(seed_vademecum(), {"sheetTypes": 0, "areas": 0, "siteContent": 0})
        self.assertEqual(VademecumSheetType.objects(codePrefix="MX", isDeleted=False).count(), 0)
        self.assertEqual(VademecumArea.objects(name=u"Geometría").count(), 0)

    def _save_sheet(self, sheetType, number, **kwargs):
        from app.models.vademecum import VademecumSheet
        sheet = VademecumSheet(sheetType=sheetType, number=number,
                               title=kwargs.pop("title", "Ficha"), **kwargs)
        sheet.save()
        return sheet

    def test_unique_sheet_by_type_and_number(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        seed_vademecum()
        hora = self._sheet_type("HT")
        first = self._save_sheet(hora, 41)
        with self.assertRaises(NotUniqueError):
            self._save_sheet(hora, 41)
        first.isDeleted = True
        first.save()
        second = self._save_sheet(hora, 41)
        self.assertEqual(second.code, "HT-41")

    def _old_series_database(self, ingenioSheets):
        """Deja la base como antes del retiro: series, seriesId e índice viejo."""
        from bson import ObjectId
        from app.helpers.vademecum_seeds import OLD_SHEET_INDEX_KEY, seed_vademecum
        from app.models.vademecum import VademecumDownload, VademecumSheet, VademecumSheetType
        seed_vademecum()
        ingenio = self._sheet_type("IM")
        seriesIds = {"34": ObjectId(), "56": ObjectId()}
        VademecumSheetType._get_collection().update_one({"_id": ingenio.id}, {"$set": {
            "series": [{"_id": seriesIds[code], "name": code, "code": code, "grades": [],
                        "sort": 1, "isDeleted": False} for code in sorted(seriesIds)]}})
        sheets = VademecumSheet._get_collection()
        sheets.drop_indexes()
        sheets.create_index(OLD_SHEET_INDEX_KEY, unique=True,
                            partialFilterExpression={"isDeleted": False})
        for number, code in ingenioSheets:
            sheets.insert_one({"sheetType": ingenio.id, "seriesId": seriesIds[code[2:4]],
                               "number": number,
                               "code": code, "title": "Ficha", "status": "draft",
                               "isDeleted": False})
        VademecumDownload._get_collection().insert_one(
            {"sheet": {"id": "x", "code": "IM34-1", "seriesId": str(seriesIds["34"])}})
        return ingenio

    def test_remove_series_cleans_old_database(self):
        from app.helpers.vademecum_seeds import remove_vademecum_series
        from app.models.vademecum import VademecumDownload, VademecumSheet
        ingenio = self._old_series_database([(1, "IM34-1"), (2, "IM34-2")])
        result = remove_vademecum_series()
        self.assertEqual((result["sheetTypes"], result["sheets"], result["downloads"]), (1, 2, 1))
        self.assertEqual((result["codes"], result["conflicts"]), (2, []))
        self.assertTrue(result["indexDropped"])
        # Se cargan con el modelo nuevo (sin FieldDoesNotExist) y con el código nuevo
        self.assertFalse(hasattr(self._sheet_type("IM"), "series"))
        self.assertEqual(sorted(s.code for s in VademecumSheet.objects(sheetType=ingenio.id)),
                         ["IM-1", "IM-2"])
        self.assertEqual(VademecumDownload.objects.first().sheet.code, "IM34-1")
        with self.assertRaises(NotUniqueError):
            self._save_sheet(ingenio, 1)
        again = remove_vademecum_series()
        self.assertEqual((again["sheets"], again["codes"], again["indexDropped"]), (0, 0, None))

    def test_remove_series_reports_repeated_numbers(self):
        from app.helpers.vademecum_seeds import remove_vademecum_series
        from app.models.vademecum import VademecumSheet
        self._old_series_database([(1, "IM34-1"), (1, "IM56-1")])
        result = remove_vademecum_series()
        self.assertEqual(result["conflicts"], [["IM34-1", "IM56-1"]])
        self.assertEqual(result["codes"], 0)
        self.assertEqual(VademecumSheet._get_collection().count_documents(
            {"seriesId": {"$exists": True}}), 0)

    def test_spanish_text_search_ignores_accents(self):
        from app.helpers.vademecum_seeds import seed_vademecum
        from app.models.vademecum import VademecumSheet
        seed_vademecum()
        self._save_sheet(self._sheet_type("HT"), 1, title=u"Problemas de conteo geométrico",
                         status="published")
        self.assertEqual(VademecumSheet.objects.search_text("geometrico").count(), 1)

    def test_email_unique_across_formats(self):
        from app.models.vademecum import VademecumTeacherAccount
        VademecumTeacherAccount(email="maria@x.co", firstName="M", lastName="P").save()
        with self.assertRaises(NotUniqueError):
            VademecumTeacherAccount(email=" MARIA@x.co ", firstName="M", lastName="P").save()


if __name__ == "__main__":
    unittest.main()
