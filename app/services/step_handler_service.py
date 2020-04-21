# app/services/step_handler_service.py


from functools import reduce
import operator
from bson import ObjectId

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import (
    getUniqueFields, getFileFields)
from app.helpers.handler_files import validate_files, upload_files
from app.services.generic_service import GenericServices


class StepHandlerService(GenericServices):

    def saveRecord(self, jsonData, files=None):
        """
        Method that saves a new record.
        params: jsonData
        """
        schema = self.Schema()
        try:
            documentFiles = getFileFields(self.Model)
            if files and documentFiles:
                validFiles = validate_files(files, documentFiles)
                folder = self.Model.__name__.lower()
                uploadedfiles = upload_files(validFiles, folder)
                jsonData.update(uploadedfiles)
            data = schema.load(jsonData)

            record = self.Model()
            for field in data.keys():
                record[field] = data[field]

            isDuplicated = self.checkForDuplicates(
                record['name'], record['tag'])
            if isDuplicated:
                raise ValidationError(
                    {"name": [{"status": "5",
                               "msg": "Duplicated record found: {}".format(record["name"])}]}
                )

            record.save()
            return schema.dump(record), 201

        except ValidationError as err:
            return err.normalized_messages(), 400

    def updateRecord(self, recordId, jsonData, partial=False, exclude=(), only=None, files=None):
        """
        Update a record
        """
        schema = self.Schema(exclude=exclude, only=only)
        try:
            documentFiles = getFileFields(self.Model)
            if files and documentFiles:
                validFiles = validate_files(files, documentFiles)
                folder = self.Model.__name__.lower()
                uploadedfiles = upload_files(validFiles, folder)
                jsonData.update(uploadedfiles)
            data = schema.load(jsonData, partial=partial)
            record = self.getOr404(recordId)
            has_changed = False
            has_changed_name = False
            for field in data.keys():
                if data[field] != record[field]:
                    if field == "name" and record[field].lower() != data[field].lower():
                        has_changed_name = True
                    record[field] = data[field]
                    has_changed = True

            if has_changed:
                isDuplicated = False
                if has_changed_name:
                    isDuplicated = self.checkForDuplicates(
                        record['name'],
                        record['tag'])
                if isDuplicated:
                    raise ValidationError(
                        {'name': [{"status": "5",
                                   "msg": "Duplicated record found: {}".format(record['name'])}]}
                    )

                record.save()

            return schema.dump(record), 200
        except ValidationError as err:
            return err.messages, 400

    def checkForDuplicates(self, name, tag):
        """
        Return True if find an duplicate field
        Return False otherwise

        """

        records = self.Model.objects.filter(
            name__iexact=name,
            tag=tag,
            isDeleted=False
        ).all()
        if records:
            return True
        return False
