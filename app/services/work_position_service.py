# app/services/work_position_service.py


from datetime import datetime
from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.models.work_position_model import (WorkPosition)
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.helpers.handler_messages import HandlerMessages


class WorkPositionService(GenericServices):

    handlerMessages = HandlerMessages()