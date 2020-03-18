# app/controllers/initial_workshop_controller.py


from flask import request
from flask_restful import Resource

from app.services.initial_workshop_service import InicialWorkshopService


class InitialWorkshopController(Resource):

    service = InicialWorkshopService()

    def post(self):

        jsonData = request.form.to_dict()
        return self.service.save(jsonData, request.files)

    def get(self):
        return self.service.get()