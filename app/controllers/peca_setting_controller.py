# app/controllers/peca_setting_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_setting_service import PecaSettingServices
from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import PecaSetting
from app.helpers.handler_authorization import jwt_required


class PecaSettingController(Resource):

    service = PecaSettingServices()

    @jwt_required
    def get(self):
        return self.service.getSetting()
