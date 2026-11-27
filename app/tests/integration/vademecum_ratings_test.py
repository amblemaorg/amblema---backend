# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_ratings_test.py
"""Valoraciones, comentarios públicos y moderación (API-16)."""

import json
import unittest
from datetime import datetime

from bson import ObjectId

from app.tests.integration.vademecum_base import VademecumAdminTestBase


class VademecumRatingsTest(VademecumAdminTestBase):

    def setUp(self):
        super(VademecumRatingsTest, self).setUp()
        self.sheet = self.create_sheet(41)
        self.maria = self.create_account("maria@test.com", u"María", u"Pérez")
        self.jose = self.create_account("jose@test.com", u"José", u"Rojas")
        self.mark_download(self.maria, self.sheet)
        self.mark_download(self.jose, self.sheet)
        from app.services.vademecum.token_service import issue_access_token
        self.mariaHeaders = {"Authorization": "Bearer " + issue_access_token(self.maria)}
        self.joseHeaders = {"Authorization": "Bearer " + issue_access_token(self.jose)}

    # --- Datos ---

    def create_sheet(self, number, status="published"):
        from app.models.vademecum import VademecumSheet
        sheet = VademecumSheet(sheetType=self.hora, number=number, title=u"Ficha {}".format(number),
                               description=u"Descripción", grades=["3"], status=status,
                               publishedAt=datetime(2026, 11, 1))
        sheet.save()
        return sheet

    def create_account(self, email, firstName, lastName):
        from app.models.vademecum import VademecumTeacherAccount
        account = VademecumTeacherAccount(email=email, firstName=firstName, lastName=lastName,
                                          status="1", emailVerifiedAt=datetime.utcnow())
        account.set_password("clave-segura")
        account.passwordChangedAt = datetime(2026, 1, 1)
        account.save()
        return account

    def mark_download(self, account, sheet):
        from app.models.vademecum import VademecumDownload
        VademecumDownload(
            sheet={"id": str(sheet.id), "code": sheet.code, "title": sheet.title},
            account={"id": str(account.id), "email": account.email},
            schoolYear={"id": str(ObjectId()), "name": "2025 - 2026"},
            origin="external", isRedownload=False).save()

    def rate(self, headers, data, sheet=None):
        return self.client.put("/vademecum/me/ratings/{}".format((sheet or self.sheet).id),
                               headers=headers, data=json.dumps(data),
                               content_type="application/json")

    def bo(self, method, path, data=None, headers=None):
        return self.client.open("/vademecum/admin" + path, method=method,
                                headers=self.adminHeaders if headers is None else headers,
                                data=json.dumps(data) if data is not None else None,
                                content_type="application/json")

    def sheet_totals(self):
        self.sheet.reload()
        return self.sheet.ratingCount, self.sheet.ratingSum

    def comments(self):
        res = self.client.get("/vademecum/sheets/{}/comments".format(self.sheet.id))
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        return res.get_json()

    def rating_id(self, account):
        from app.models.vademecum import VademecumRating
        return str(VademecumRating.objects(account=account.id).first().id)

    # --- Docente ---

    def test_stars_count_without_moderation(self):
        res = self.rate(self.mariaHeaders, {"stars": 4})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual((res.get_json()["stars"], res.get_json()["commentStatus"]), (4, None))
        self.assertEqual(self.sheet_totals(), (1, 4))
        self.rate(self.joseHeaders, {"stars": 2})
        self.assertEqual(self.sheet_totals(), (2, 6))
        detail = self.client.get("/vademecum/sheets/{}".format(self.sheet.id)).get_json()
        self.assertEqual((detail["ratingAverage"], detail["ratingCount"]), (3.0, 2))

    def test_editing_adjusts_the_sum_without_counting_twice(self):
        self.rate(self.mariaHeaders, {"stars": 4})
        self.rate(self.mariaHeaders, {"stars": 2})
        self.assertEqual(self.sheet_totals(), (1, 2))
        mine = self.client.get("/vademecum/me/ratings/{}".format(self.sheet.id),
                               headers=self.mariaHeaders).get_json()
        self.assertEqual(mine["stars"], 2)

    def test_comment_is_published_only_after_approval(self):
        res = self.rate(self.mariaHeaders, {"stars": 5, "comment": u"  Muy útil  "})
        self.assertEqual((res.get_json()["comment"], res.get_json()["commentStatus"]),
                         (u"Muy útil", "pending"))
        self.assertEqual(self.comments()["pagination"]["total"], 0)
        res = self.bo("POST", "/ratings/{}/approve".format(self.rating_id(self.maria)))
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertEqual(res.get_json()["moderatedBy"]["id"], str(self.admin.id))
        records = self.comments()["records"]
        self.assertEqual((records[0]["authorName"], records[0]["comment"], records[0]["stars"]),
                         (u"María P.", u"Muy útil", 5))
        detail = self.client.get("/vademecum/sheets/{}".format(self.sheet.id)).get_json()
        self.assertEqual(detail["commentCount"], 1)

    def test_edited_comment_goes_back_to_moderation_but_stars_alone_do_not(self):
        self.rate(self.mariaHeaders, {"stars": 5, "comment": u"Bien"})
        self.bo("POST", "/ratings/{}/approve".format(self.rating_id(self.maria)))
        res = self.rate(self.mariaHeaders, {"stars": 3, "comment": u"Bien"})
        self.assertEqual(res.get_json()["commentStatus"], "approved")
        res = self.rate(self.mariaHeaders, {"stars": 3, "comment": u"Cambié de opinión"})
        self.assertEqual(res.get_json()["commentStatus"], "pending")
        self.assertEqual(self.comments()["pagination"]["total"], 0)
        res = self.rate(self.mariaHeaders, {"stars": 3, "comment": ""})
        self.assertEqual((res.get_json()["comment"], res.get_json()["commentStatus"]),
                         (None, None))

    def test_rating_requires_a_download(self):
        other = self.create_sheet(42)
        self.assert_error(self.rate(self.mariaHeaders, {"stars": 4}, sheet=other),
                          403, "general", "111")
        self.assertEqual(other.ratingCount, 0)

    def test_rating_validation_and_sheet_state(self):
        for data in ({}, {"stars": 0}, {"stars": 6}, {"stars": "4"},
                     {"stars": 4, "comment": "x" * 1001}):
            self.assertEqual(self.rate(self.mariaHeaders, data).status_code, 400, data)
        draft = self.create_sheet(43, status="draft")
        self.assert_error(self.rate(self.mariaHeaders, {"stars": 4}, sheet=draft),
                          404, "general", "5")
        res = self.client.put("/vademecum/me/ratings/{}".format(self.sheet.id),
                              data=json.dumps({"stars": 4}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        self.assert_error(self.client.get("/vademecum/me/ratings/{}".format(self.sheet.id),
                                          headers=self.mariaHeaders), 404, "general", "5")

    # --- Moderación ---

    def test_admin_hides_a_published_comment_and_stars_still_count(self):
        self.rate(self.mariaHeaders, {"stars": 5, "comment": u"Excelente"})
        ratingId = self.rating_id(self.maria)
        self.bo("POST", "/ratings/{}/approve".format(ratingId))
        res = self.bo("POST", "/ratings/{}/hide".format(ratingId))
        self.assertEqual((res.status_code, res.get_json()["commentStatus"]), (200, "hidden"))
        self.assertEqual(self.comments()["pagination"]["total"], 0)
        self.assertEqual(self.sheet_totals(), (1, 5))

    def test_admin_list_filters_and_queue_order(self):
        self.rate(self.mariaHeaders, {"stars": 5, "comment": u"Primero"})
        self.rate(self.joseHeaders, {"stars": 4, "comment": u"Segundo"})
        records = self.bo("GET", "/ratings").get_json()["records"]
        self.assertEqual([r["comment"] for r in records], [u"Primero", u"Segundo"])
        self.assertEqual(records[0]["account"]["email"], "maria@test.com")
        self.assertEqual(records[0]["sheet"]["id"], str(self.sheet.id))
        self.assertEqual(set(records[0]),
                         {"id", "sheet", "account", "stars", "comment", "commentStatus",
                          "moderatedBy", "moderatedAt", "updatedAt"})
        self.bo("POST", "/ratings/{}/approve".format(self.rating_id(self.jose)))
        approved = self.bo("GET", "/ratings?commentStatus=approved").get_json()
        self.assertEqual([r["comment"] for r in approved["records"]], [u"Segundo"])
        self.assertEqual(approved["records"][0]["moderatedBy"]["id"], str(self.admin.id))
        other = self.bo("GET", "/ratings?sheetId={}".format(ObjectId())).get_json()
        self.assertEqual(other["pagination"]["total"], 0)
        self.assert_error(self.bo("GET", "/ratings?commentStatus=x"), 400, "commentStatus", "1")

    def test_moderation_rejects_a_version_the_admin_did_not_see(self):
        self.rate(self.mariaHeaders, {"stars": 5, "comment": u"Versión vista"})
        seen = self.bo("GET", "/ratings").get_json()["records"][0]
        # El docente edita después de que el moderador cargó la lista
        from app.models.vademecum import VademecumRating
        VademecumRating.objects(id=seen["id"]).update_one(
            set__comment=u"Otra cosa", set__updatedAt=datetime(2030, 1, 1))
        res = self.bo("POST", "/ratings/{}/approve".format(seen["id"]),
                      {"updatedAt": seen["updatedAt"]})
        self.assert_error(res, 409, "general", "120")
        self.assertEqual(VademecumRating.objects.get(id=seen["id"]).commentStatus, "pending")

    def test_moderation_accepts_the_version_the_admin_saw(self):
        self.rate(self.mariaHeaders, {"stars": 5, "comment": u"Versión vista"})
        seen = self.bo("GET", "/ratings").get_json()["records"][0]
        res = self.bo("POST", "/ratings/{}/approve".format(seen["id"]),
                      {"updatedAt": seen["updatedAt"]})
        self.assertEqual((res.status_code, res.get_json()["commentStatus"]), (200, "approved"),
                         res.get_data(as_text=True))

    def test_moderation_errors_and_permission(self):
        from unittest import mock
        from mongoengine import NotUniqueError
        from app.models.vademecum import VademecumRating
        from app.services.vademecum.rating_service import author_name
        self.assertIsNone(author_name(None))
        self.rate(self.mariaHeaders, {"stars": 5})
        ratingId = self.rating_id(self.maria)
        self.assert_error(self.bo("POST", "/ratings/{}/approve".format(ratingId)),
                          400, "comment", "1")
        self.assert_error(self.bo("POST", "/ratings/{}/approve".format(ratingId),
                                  {"updatedAt": "no-es-fecha"}), 400, "updatedAt", "1")
        self.assert_error(self.bo("POST", "/ratings/{}/hide".format(ObjectId())),
                          404, "general", "5")
        self.assertEqual(self.bo("GET", "/ratings?sheetId=x").status_code, 400)
        self.assertEqual(self.bo("GET", "/ratings?page=abc").status_code, 400)
        self.assertEqual(
            self.client.get("/vademecum/sheets/{}/comments?page=0".format(self.sheet.id))
            .status_code, 400)
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        res = self.bo("GET", "/ratings", headers=self.headers(coordinator))
        self.assertEqual(res.status_code, 403)

        # Concurrencia al guardar y al moderar
        with mock.patch("app.models.vademecum.rating_model.VademecumRating.objects") as mObj:
            mObj.return_value.first.return_value = VademecumRating.objects.get(id=ratingId)
            mObj.return_value.update_one.return_value = 0
            self.assert_error(self.rate(self.mariaHeaders, {"stars": 4}), 409, "general", "1")

        self.rate(self.mariaHeaders, {"stars": 5, "comment": u"Con comentario"})
        with mock.patch("app.models.vademecum.rating_model.VademecumRating.objects") as mObj:
            mObj.return_value.first.return_value = VademecumRating.objects.get(id=ratingId)
            mObj.return_value.update_one.return_value = 0
            self.assert_error(self.bo("POST", "/ratings/{}/approve".format(ratingId)),
                              409, "general", "120")

        with mock.patch.object(VademecumRating, "save", side_effect=NotUniqueError("dup")):
            self.assert_error(self.rate(self.joseHeaders, {"stars": 5}), 409, "general", "1")

    def test_public_comments_of_unpublished_sheet_are_not_found(self):
        draft = self.create_sheet(44, status="draft")
        res = self.client.get("/vademecum/sheets/{}/comments".format(draft.id))
        self.assert_error(res, 404, "general", "5")


if __name__ == "__main__":
    unittest.main()
