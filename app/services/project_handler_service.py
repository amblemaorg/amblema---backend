# app/services/project_handler_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices


class ProjectHandlerService(GenericServices):
    def getRecord(self, recordId, only=None, exclude=()):
        """
        Return a record filterd by its id
        """
        schema = self.Schema(exclude=exclude, only=only)
        record = self.getOr404(recordId)
        record.stepsProgress.steps = sorted(
            record.stepsProgress.steps, key=lambda x: (x['tag'], x['sort']))
        return schema.dump(record), 200
