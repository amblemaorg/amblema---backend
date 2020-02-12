# app/services/user_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices


class UserService(GenericServices):

    def saveRecord(self, jsonData):
        """
        Method that saves a new record.   
        params: jsonData
        """
        schema = self.Schema()
        try:
            data = schema.load(jsonData)
            password = data['password']
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            record = self.Model()
            for field in data.keys():
                record[field] = data[field]
                if field in uniquesFields:
                    fieldsForCheckDuplicates.append(
                        {"field": field, "value": data[field]})
            isDuplicated = self.checkForDuplicates(fieldsForCheckDuplicates)
            if isDuplicated:
                return {
                    "message": "Duplicated record found.",
                    "data": isDuplicated}, 400
            try:
                record.save()
                record.sendRegistrationEmail(password)
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.messages, 400
