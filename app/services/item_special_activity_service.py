# app/services/item_special_activity_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.models.teacher_testimonial_model import TeacherTestimonial
from app.models.school_user_model import SchoolUser
from app.models.user_model import User
from app.models.request_content_approval_model import RequestContentApproval
from app.models.teacher_model import Teacher
from app.schemas.teacher_testimonial_schema import TeacherTestimonialSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class TeacherTestimonialService():