# /app/controllers/step_controller.py


from flask import request
from flask_restful import Resource
from flask import current_app

from app.services.step_handler_service import StepHandlerService
from app.models.step_model import Step
from app.schemas.step_schema import StepSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class StepController(Resource):

    service = StepHandlerService(
        Model=Step,
        Schema=StepSchema)

    @jwt_required
    def get(self):
        from app.models.school_year_model import SchoolYear
        filters = getQueryParams(request)
        active_sy = SchoolYear.objects(isDeleted=False, status="1").first()
        if active_sy:
            has_sy = any(f.get('field') == 'schoolYear' for f in filters)
            if not has_sy:
                filters.append({"field": "schoolYear", "value": str(active_sy.id)})
        return self.service.getAllRecords(filters=filters)

    @jwt_required
    def post(self):
        jsonData = request.form.to_dict()
        return self.service.saveRecord(jsonData, request.files)


class StepHandlerController(Resource):

    service = StepHandlerService(
        Model=Step,
        Schema=StepSchema)

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)
