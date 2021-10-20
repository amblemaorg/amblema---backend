# app/controllers/cron_student_controller.py


from flask import request
from flask_restful import Resource

from app.services.cron_student_service import CronStudentService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class CronStudentController(Resource):
    service = CronStudentService()
    def get(self, limit, skip):
        return self.service.run(limit=limit, skip=skip)