# app/services/peca_setting_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import (
    getUniqueFields, getFileFields)
from app.helpers.handler_files import validate_files, upload_files
from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import PecaSetting
from app.schemas.peca_setting_schema import PecaSettingSchema


class PecaSettingServices():
    Schema = PecaSettingSchema
    Model = PecaSetting

    def getSetting(self):
        """
        get setting in currect school year
        """
        schema = self.Schema()

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        return schema.dump(schoolYear["pecaSetting"]), 200
