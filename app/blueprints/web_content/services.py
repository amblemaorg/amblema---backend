# app/blueprints/web_content/services.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.blueprints.web_content.models.web_content import WebContent, WebContentSchema


class WebContentService(GenericServices):

    def getAllRecords(self, only=None, exclude=()):
        """
        get all available states records
        """
        if only and exclude: schema = self.Schema(only=only, exclude=exclude)
        elif only: schema = self.Schema(only=only)
        elif exclude: schema = self.Schema(exclude=exclude)
        else: schema = self.Schema()

        record = self.Model.objects(status = True).first()
        return schema.dump(record), 200


    def saveRecord(self, jsonData, only=None):
        """
        Method that saves a new record.
        params: jsonData
        """
        schema = self.Schema(only=only)
        try:
            data = schema.load(jsonData, partial=True)
            
            record = WebContent.objects().first()
            if not record : record = self.Model()

            for field in data.keys():
                record[field] = data[field]
            
            try:
                record.save()
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.messages, 400
        except BaseException as e:
            return {"message": "Contact to support and mention it: File generic_service.py. "+str(e)}, 500