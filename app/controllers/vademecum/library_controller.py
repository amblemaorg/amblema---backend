# -*- coding: utf-8 -*-
# app/controllers/vademecum/library_controller.py
"""Biblioteca del docente: /vademecum/me/downloads y /vademecum/me/favorites (API-15)."""

from flask import g, request
from flask_restful import Resource

from app.helpers.vademecum_auth import vademecum_teacher_required
from app.services.vademecum.library_service import LibraryService


class MyDownloadsController(Resource):
    @vademecum_teacher_required
    def get(self):
        return LibraryService().list_downloads(g.vademecum_account, request.args)


class MyFavoritesController(Resource):
    @vademecum_teacher_required
    def get(self):
        return LibraryService().list_favorites(g.vademecum_account, request.args)


class MyFavoriteController(Resource):
    @vademecum_teacher_required
    def put(self, sheetId):
        return LibraryService().add_favorite(g.vademecum_account, sheetId)

    @vademecum_teacher_required
    def delete(self, sheetId):
        return LibraryService().remove_favorite(g.vademecum_account, sheetId)
