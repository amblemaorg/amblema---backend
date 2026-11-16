# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_indicators_test.py
"""Indicadores de uso para el backoffice (API-17)."""

import unittest
from unittest import mock
from datetime import datetime, timedelta

from bson import ObjectId

from app.tests.fixtures import create_school_year
from app.tests.integration.vademecum_base import VademecumAdminTestBase

STATE_LARA = str(ObjectId())
STATE_ZULIA = str(ObjectId())


class VademecumIndicatorsTest(VademecumAdminTestBase):

    def setUp(self):
        super(VademecumIndicatorsTest, self).setUp()
        self.year = create_school_year(name="2026 - 2027", start=datetime(2026, 10, 14),
                                       end=datetime(2027, 8, 31))
        self.oldYear = create_school_year(name="2025 - 2026", start=datetime(2025, 9, 1),
                                          end=datetime(2026, 7, 31), status="2")
        self.maria = self.account("maria@test.com", u"María", u"Pérez")
        self.jose = self.account("jose@test.com", u"José", u"Rojas")
        self.ana = self.account("ana@test.com", u"Ana", u"Externa")
        self.schoolA = {"id": str(ObjectId()), "name": "Escuela A", "code": "OD1",
                        "stateId": STATE_LARA, "stateName": "Lara"}
        self.schoolB = {"id": str(ObjectId()), "name": "Escuela B", "code": "OD2",
                        "stateId": STATE_ZULIA, "stateName": "Zulia"}
        self.ht1 = {"id": str(ObjectId()), "code": "HT-1", "title": "Hora 1",
                    "sheetTypeId": str(self.hora.id), "sheetTypeName": self.hora.name}
        self.ht2 = {"id": str(ObjectId()), "code": "HT-2", "title": "Hora 2",
                    "sheetTypeId": str(self.hora.id), "sheetTypeName": self.hora.name}
        self.im1 = {"id": str(ObjectId()), "code": "IM-1", "title": "Ingenio 1",
                    "sheetTypeId": str(self.ingenio.id), "sheetTypeName": self.ingenio.name}

        # Año vigente: María (A) 3 fichas + 1 redescarga; José (B) 1; Ana externa 2
        self.download(self.maria, self.ht1, self.schoolA)
        self.download(self.maria, self.ht2, self.schoolA)
        self.download(self.maria, self.im1, self.schoolA)
        self.download(self.maria, self.ht1, self.schoolA, isRedownload=True)
        self.download(self.jose, self.ht1, self.schoolB)
        self.download(self.ana, self.ht1, None)
        self.download(self.ana, self.im1, None)
        # Año anterior: no cuenta en el vigente
        self.download(self.jose, self.ht2, self.schoolB, year=self.oldYear)

    def account(self, email, firstName, lastName):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=email, firstName=firstName, lastName=lastName,
                                          status="1")
        account.save()
        return account

    def download(self, account, sheet, school, isRedownload=False, year=None):
        from app.models.vademecum import VademecumDownload
        year = year or self.year
        self._clock = getattr(self, "_clock", datetime(2026, 11, 1)) + timedelta(minutes=1)
        return VademecumDownload(
            sheet=sheet,
            account={"id": str(account.id), "email": account.email,
                     "firstName": account.firstName, "lastName": account.lastName},
            teacherId=None, school=school,
            schoolYear={"id": str(year.id), "name": year.name},
            origin="enrollment" if school else "external",
            isRedownload=isRedownload, createdAt=self._clock).save()

    def get(self, path, headers=None):
        res = self.client.get("/vademecum/admin/indicators" + path,
                              headers=self.adminHeaders if headers is None else headers)
        return res

    def ok(self, path):
        res = self.get(path)
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        return res.get_json()

    # --- Resumen ---

    def test_summary_counts_without_redownloads(self):
        data = self.ok("")
        self.assertEqual(data["schoolYear"]["id"], str(self.year.id))
        self.assertEqual(data["totals"], {"downloads": 6, "activeTeachers": 3,
                                          "activeSchools": 2, "externalTeachers": 1})
        self.assertEqual(data["byOrigin"], {"enrollment": 4, "external": 2})
        byType = {row["sheetType"]["codePrefix"]: row["downloads"] for row in data["byType"]}
        self.assertEqual(byType, {"HT": 4, "IM": 2})
        self.assertEqual(data["byType"][0]["sheetType"]["color"], self.hora.color)
        self.assertEqual(data["topSheets"][0], {
            "sheet": {"id": self.ht1["id"], "code": "HT-1", "title": "Hora 1"},
            "downloads": 3})
        self.assertEqual(data["topTeachers"][0]["account"]["email"], "maria@test.com")
        self.assertEqual(data["topTeachers"][0]["downloads"], 3)

    def test_externals_are_one_row_in_school_ranking(self):
        schools = {row["school"]["name"]: row for row in self.ok("")["topSchools"]}
        self.assertEqual(set(schools), {"Escuela A", "Escuela B", "Externos"})
        self.assertIsNone(schools["Externos"]["school"]["id"])
        self.assertEqual((schools["Externos"]["downloads"],
                          schools["Externos"]["activeTeachers"]), (2, 1))
        self.assertEqual((schools["Escuela A"]["downloads"],
                          schools["Escuela A"]["school"]["stateName"]), (3, "Lara"))

    def test_filters_by_school_state_type_and_origin(self):
        data = self.ok("?schoolId=" + self.schoolB["id"])
        self.assertEqual(data["totals"]["downloads"], 1)
        data = self.ok("?stateId=" + STATE_LARA)
        self.assertEqual((data["totals"]["downloads"], data["totals"]["externalTeachers"]), (3, 0))
        data = self.ok("?sheetTypeId=" + str(self.ingenio.id))
        self.assertEqual(data["totals"]["downloads"], 2)
        data = self.ok("?origin=external")
        self.assertEqual(data["totals"], {"downloads": 2, "activeTeachers": 1,
                                          "activeSchools": 0, "externalTeachers": 1})

    def test_filter_by_previous_year_and_top(self):
        data = self.ok("?schoolYearId=" + str(self.oldYear.id))
        self.assertEqual(data["totals"]["downloads"], 1)
        self.assertEqual(data["schoolYear"]["name"], "2025 - 2026")
        self.assertEqual(len(self.ok("?top=1")["topSheets"]), 1)

    def test_invalid_filters(self):
        for query, field in (("?top=0", "top"), ("?top=51", "top"), ("?origin=otro", "origin"),
                             ("?schoolId=x", "schoolId"), ("?schoolYearId=x", "schoolYearId"),
                             ("?schoolYearId=" + str(ObjectId()), "schoolYearId")):
            self.assert_error(self.get(query), 400, field, "1")

    def test_without_current_year_returns_empty(self):
        from app.models.school_year_model import SchoolYear
        SchoolYear.objects(id=self.year.id).update(set__status="2")
        data = self.ok("")
        self.assertIsNone(data["schoolYear"])
        self.assertEqual(data["totals"]["downloads"], 0)

    def test_requires_vademecum_admin(self):
        self.assertIn(self.get("", headers={}).status_code, (401, 422))
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        self.assertEqual(self.get("", headers=self.headers(coordinator)).status_code, 403)

    # --- Docentes ---

    def test_teachers_list(self):
        data = self.ok("/teachers")
        self.assertEqual(data["pagination"]["total"], 3)
        first = data["records"][0]
        self.assertEqual((first["account"]["email"], first["downloads"], first["origin"]),
                         ("maria@test.com", 3, "enrollment"))
        self.assertEqual([s["name"] for s in first["schools"]], ["Escuela A"])
        self.assertTrue(first["lastDownloadAt"].endswith("Z"))
        ana = [r for r in data["records"] if r["account"]["email"] == "ana@test.com"][0]
        self.assertEqual((ana["origin"], ana["schools"]), ("external", []))

    def test_teachers_search_filter_and_pagination(self):
        data = self.ok("/teachers?q=ROJAS")
        self.assertEqual([r["account"]["email"] for r in data["records"]], ["jose@test.com"])
        self.assertEqual(self.ok("/teachers?origin=external")["pagination"]["total"], 1)
        data = self.ok("/teachers?pageSize=2&page=2")
        self.assertEqual((len(data["records"]), data["pagination"]["pages"]), (1, 2))
        self.assert_error(self.get("/teachers?pageSize=0"), 400, "pageSize", "1")
        self.assert_error(self.get("/teachers?q=" + "a" * 101), 400, "q", "1")

    def test_teacher_downloads_include_marked_redownloads(self):
        data = self.ok("/teachers/%s/downloads" % self.maria.id)
        self.assertEqual(data["pagination"]["total"], 4)
        first = data["records"][0]
        self.assertTrue(first["isRedownload"])
        self.assertEqual((first["sheet"]["code"], first["school"]["name"],
                          first["schoolYear"]["id"]), ("HT-1", "Escuela A", str(self.year.id)))
        ana = self.ok("/teachers/%s/downloads" % self.ana.id)
        self.assertIsNone(ana["records"][0]["school"])

    def test_teacher_downloads_not_found(self):
        self.assert_error(self.get("/teachers/%s/downloads" % ObjectId()), 404, "general", "5")
        self.assert_error(self.get("/teachers/x/downloads"), 404, "general", "5")

    # --- Exportación ---

    def test_teachers_filter_by_sheet_type(self):
        data = self.ok("/teachers?sheetTypeId=" + str(self.ingenio.id))
        self.assertEqual(sorted((r["account"]["email"], r["downloads"]) for r in data["records"]),
                         [("ana@test.com", 1), ("maria@test.com", 1)])

    def test_export_flat_columns_and_order(self):
        # José también descarga en la escuela A: dos escuelas, sin repetir y ordenadas
        self.download(self.jose, self.ht2, self.schoolA)
        data = self.ok("/teachers/export")
        self.assertEqual(data["schoolYear"], {"id": str(self.year.id), "name": "2026 - 2027"})
        self.assertTrue(data["generatedAt"].endswith("Z"))
        self.assertEqual(data["filters"], {"schoolId": None, "stateId": None,
                                           "sheetTypeId": None, "origin": None, "q": None})
        self.assertEqual(data["total"], 3)
        self.assertEqual([r["email"] for r in data["records"]],
                         ["maria@test.com", "ana@test.com", "jose@test.com"])  # empate: apellido
        maria, jose = data["records"][0], data["records"][2]
        self.assertEqual((maria["firstName"], maria["lastName"], maria["origin"],
                          maria["originLabel"]), (u"María", u"Pérez", "enrollment", u"Matrícula"))
        self.assertEqual((maria["schools"], maria["schoolCodes"], maria["states"],
                          maria["downloads"]), ("Escuela A", "OD1", "Lara", 3))
        self.assertTrue(maria["lastDownloadAt"].endswith("Z"))
        self.assertEqual((jose["schools"], jose["schoolCodes"], jose["states"], jose["downloads"]),
                         ("Escuela A, Escuela B", "OD1, OD2", "Lara, Zulia", 2))

    def test_export_external_has_label_and_empty_schools(self):
        data = self.ok("/teachers/export?origin=external")
        self.assertEqual(data["filters"]["origin"], "external")
        self.assertEqual(data["total"], 1)
        ana = data["records"][0]
        self.assertEqual((ana["originLabel"], ana["schools"], ana["schoolCodes"], ana["states"]),
                         ("Externo", "", "", ""))

    def test_export_filters_by_sheet_type_and_ignores_redownloads(self):
        data = self.ok("/teachers/export?sheetTypeId=" + str(self.ingenio.id))
        self.assertEqual(sorted(r["email"] for r in data["records"]),
                         ["ana@test.com", "maria@test.com"])
        self.assertEqual(data["filters"]["sheetTypeId"], str(self.ingenio.id))
        # María tiene 4 descargas con la redescarga: el export cuenta 3
        maria = [r for r in self.ok("/teachers/export")["records"]
                 if r["email"] == "maria@test.com"][0]
        self.assertEqual(maria["downloads"], 3)
        self.assertEqual(self.ok("/teachers/export?q=ROJAS")["total"], 1)

    def test_export_invalid_filters(self):
        for query, field in (("?origin=otro", "origin"), ("?schoolId=x", "schoolId"),
                             ("?sheetTypeId=x", "sheetTypeId"), ("?schoolYearId=x", "schoolYearId"),
                             ("?q=" + "a" * 101, "q")):
            self.assert_error(self.get("/teachers/export" + query), 400, field, "1")

    def test_export_too_many_rows(self):
        with mock.patch("app.services.vademecum.indicator_service.MAX_EXPORT_ROWS", 1):
            self.assert_error(self.get("/teachers/export"), 400, "general", "1")
            self.assertEqual(self.ok("/teachers/export?origin=external")["total"], 1)

    def test_export_without_current_year_returns_empty(self):
        from app.models.school_year_model import SchoolYear
        SchoolYear.objects(id=self.year.id).update(set__status="2")
        data = self.ok("/teachers/export")
        self.assertIsNone(data["schoolYear"])
        self.assertEqual((data["total"], data["records"]), (0, []))

    def test_export_requires_vademecum_admin(self):
        self.assertIn(self.get("/teachers/export", headers={}).status_code, (401, 422))
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        self.assertEqual(self.get("/teachers/export",
                                  headers=self.headers(coordinator)).status_code, 403)


if __name__ == "__main__":
    unittest.main()
