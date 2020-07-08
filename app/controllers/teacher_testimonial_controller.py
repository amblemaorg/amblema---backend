# /app/controllers/teacher_testimonial_controller.py


from flask import request
from flask_restful import Resource

from app.services.teacher_testimonial_service import TeacherTestimonialService
from app.helpers.handler_request import getQueryParams


class TeacherTestimonialController(Resource):

    service = TeacherTestimonialService()

    def post(self, schoolId):
        userId = request.args.get('userId')
        jsonData = request.get_json()
        return self.service.save(schoolId, userId, jsonData)

    def get(self, schoolId):
        return self.service.get_all(schoolId)
