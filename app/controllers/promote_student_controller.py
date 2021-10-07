# app/controllers/promote_student_controller.py


from flask import request
from flask_restful import Resource

from app.services.promote_student_service import PromoteStudentService, SectionsPromoteStudentService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class PromoteStudentController(Resource):
    service = PromoteStudentService()
    def get(self,school_code, id_section):
        return self.service.getList(school_code=school_code, id_section=id_section)

class SectionsPromoteStudentController(Resource):
    service = SectionsPromoteStudentService()
    def get(self,school_code):
        return self.service.getSections(school_code=school_code)

class PromoteStudentsController(Resource):
    service = PromoteStudentService()
    def post(self, school_code):
        jsonData = request.get_json()
        return self.service.promoteStudents(school_code=school_code, data=jsonData)