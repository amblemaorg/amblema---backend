# app/services/state_service.py


from datetime import datetime
from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.models.specialty_teacher_model import (SpecialtyTeacher)
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.helpers.handler_messages import HandlerMessages


class SpecialtyTeacherService(GenericServices):

    handlerMessages = HandlerMessages()