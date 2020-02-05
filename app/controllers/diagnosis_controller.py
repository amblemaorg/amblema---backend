# /app/controllers/role_controller.py

import json

from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.school_year_model import (
    SchoolYear, SchoolYearSchema)
from app.helpers.handler_request import getQueryParams
from app.helpers.error_helpers import RegisterNotFound


class DiagnosticController(Resource):
    
    service = GenericServices(
        Model=SchoolYear,
        Schema=SchoolYearSchema)

    def get(self):
        year = SchoolYear.objects(status=True, state='1').first()
        if not year:
            raise RegisterNotFound(message="There is not an active school year",
                               status_code=400)
        yearSchema = SchoolYearSchema(only=["diagnosticSettings"])
        
        return yearSchema.dump(year),200

    def post(self):
        year = SchoolYear.objects(status=True, state='1').first()
        if not year:
            raise RegisterNotFound(message="There is not an active school year",
                               status_code=400)
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=str(year.id),
            jsonData=jsonData,
            only=["diagnosticSettings"],
            partial=True)



