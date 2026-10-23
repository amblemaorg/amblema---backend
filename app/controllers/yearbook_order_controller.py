# app/controllers/yearbook_order_controller.py

from flask import request
from flask_restful import Resource

from app.services.yearbook_order_service import YearbookOrderService
from app.helpers.handler_authorization import jwt_required


class YearbookOrderController(Resource):
    service = YearbookOrderService()

    @jwt_required
    def get(self):
        return self.service.getSetting()


class YearbookOrderHandlerController(Resource):
    service = YearbookOrderService()

    @jwt_required
    def put(self, lapse):
        jsonData = request.get_json()
        return self.service.saveSetting(lapse=lapse, jsonData=jsonData)


class PecaYearbookOrderController(Resource):
    service = YearbookOrderService()

    @jwt_required
    def get(self, pecaId):
        return self.service.getPecaOrder(pecaId)
