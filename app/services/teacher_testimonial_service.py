# app/services/teacher_testimonial_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.models.teacher_testimonial_model import TeacherTestimonial
from app.models.school_user_model import SchoolUser
from app.models.peca_project_model import Teacher
from app.schemas.teacher_testimonial_schema import TeacherTestimonialSchema
from app.schemas.peca_project_schema import TeacherSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class TeacherTestimonialService():

    def get_all(self, filters=None):
        return
    
    def get(self, id):

        teacherTestimonial = TeacherTestimonial.objects(
            id=id, isDeleted=False, status=2).first()
        if teacherTestimonial:
            schema = TeacherTestimonialSchema()
            return schema.dump(teacherTestimonial), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})
    
    def save(self, schoolId, userId, jsonData):