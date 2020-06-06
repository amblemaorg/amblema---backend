# app/services/steps_approval_service.py


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


class StepsApprovalService(GenericServices):
    def __init__(self, Model, Schema):
        self.Model = Model
        self.Schema = Schema

    def saveRecord(self, jsonData, files=None):
        """
        Method that saves a new record.
        params: jsonData
        """

        from app.models.request_content_approval_model import RequestContentApproval
        from app.schemas.request_content_approval_schema import RequestContentApprovalSchema

        schema = self.Schema()
        try:
            documentFiles = getFileFields(self.Model)
            if files and documentFiles:
                validFiles = validate_files(files, documentFiles)
                folder = "projects/{}/stepsapproval/{}".format(
                    jsonData['project'], jsonData['stepId']
                )
                uploadedfiles = upload_files(validFiles, folder)
                jsonData.update(uploadedfiles)
            data = schema.load(jsonData)
            record = self.Model()
            for field in data.keys():
                record[field] = data[field]
            request = RequestContentApproval(
                project=record.project.getReference(),
                user=record.user,
                type="1",
                detail=schema.dump(record)
            ).save()

            # record.save()
            return RequestContentApprovalSchema().dump(request), 201

        except ValidationError as err:
            return err.normalized_messages(), 400
