import json
from flask import request
from flask_restful import Resource

from app.services.peca_project_service import PecaProjectService
from app.helpers.handler_authorization import jwt_required

class PecaProjectHandlerPrintOptionsController(Resource):

  service = PecaProjectService()

  @jwt_required
  def patch(self, id):
    jsonData = request.get_json()
    return self.service.savePrintOptions(id=id, jsonData=jsonData)


