# app/controllers/peca_school_controller.py


from flask import request
from flask_restful import Resource

from app.services.peca_school_service import SchoolService
from app.helpers.handler_request import getQueryParams


class SchoolController(Resource):

    service = SchoolService()

    def put(self, pecaId):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        return self.service.save(pecaId, userId, jsonData)

    def get(self, pecaId):
        return self.service.get(pecaId)
