# -*- coding: utf-8 -*-
# app/controllers/vademecum/rating_controller.py
"""Valoraciones del docente, comentarios públicos y moderación (API-16)."""

from flask import g, request
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_admin_required, vademecum_teacher_required
from app.services.vademecum.rating_service import RatingService, with_rating


class MyRatingController(Resource):
    @vademecum_teacher_required
    def get(self, sheetId):
        return RatingService().get_mine(g.vademecum_account, sheetId)

    @vademecum_teacher_required
    def put(self, sheetId):
        return RatingService().save_mine(g.vademecum_account, sheetId,
                                         request.get_json(silent=True))


class SheetCommentsController(Resource):
    def get(self, sheetId):
        return RatingService().public_comments(sheetId, request.args)


class AdminRatingListController(Resource):
    @vademecum_admin_required
    def get(self):
        return RatingService().admin_list(request.args)


class AdminRatingApproveController(Resource):
    @vademecum_admin_required
    def post(self, ratingId):
        service = RatingService()
        data = request.get_json(silent=True)
        return with_rating(service.get(ratingId),
                           lambda r: service.moderate(r, "approved", g.vademecum_admin, data))


class AdminRatingHideController(Resource):
    @vademecum_admin_required
    def post(self, ratingId):
        service = RatingService()
        data = request.get_json(silent=True)
        return with_rating(service.get(ratingId),
                           lambda r: service.moderate(r, "hidden", g.vademecum_admin, data))
