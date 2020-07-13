# app/controllers/peca_school_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_school_service import SchoolService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class SchoolController(Resource):

    service = SchoolService()

    @jwt_required
    def put(self, pecaId):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        return self.service.save(pecaId, userId, jsonData)

    @jwt_required
    def get(self, pecaId):
        return self.service.get(pecaId)
