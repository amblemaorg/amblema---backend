# app/blueprints/web_content/services.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.blueprints.web_content.models.web_content import WebContent, WebContentSchema
from app.services.statistics_service import StatisticsService


class WebContentService(GenericServices):

    def getAllRecords(self, page, only=None, exclude=()):
        """
        get all available states records
        """
        schema = self.Schema(only=only, exclude=exclude)
        if page:
            schema = self.Schema(only=[page], exclude=exclude)
            record = self.Model.objects().only(page).first()
            data = schema.dump(record)
            if page == 'homePage':
                statisticsService = StatisticsService()
                data['homePage']['nStudents'] = statisticsService.get_count_students()
                data['homePage']['diagnostics'] = statisticsService.get_diagnostics_last_five_years()

            return data, 200

    def saveRecord(self, jsonData, only=None):
        """
        Method that saves a new record.
        params: jsonData
        """
        schema = self.Schema(only=only)
        try:
            data = schema.load(jsonData, partial=True)

            record = WebContent.objects().first()
            if not record:
                record = self.Model()

            for field in data.keys():
                record[field] = data[field]

            try:
                record.save()
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.messages, 400
