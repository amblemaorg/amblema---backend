# app/services/generic_service.py


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


class GenericServices():
    def __init__(self, Model, Schema):
        self.Model = Model
        self.Schema = Schema

    def getAllRecords(self, filters=None, only=None, exclude=()):
        """
        get all available states records
        """
        schema = self.Schema(only=only, exclude=exclude)

        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records = self.Model.objects(isDeleted=False).filter(
                reduce(operator.and_, filterList)).all()
        else:
            records = self.Model.objects(isDeleted=False).all()

        return {"records": schema.dump(records, many=True)}, 200

    def getPaginatedRecords(self, filters=None, only=None, exclude=(), order_by='+createdAt', page=0, page_size=4) :
        # THIS METHOD ASSUMES THAT MODEL IS A SUBCLASS OF DOCUMENT FROM FLASK_MONGOENGINE
        schema = self.Schema(only=only, exclude=exclude)
        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
        
        records = self.Model.objects(isDeleted=False).filter(
            reduce(operator.and_, filterList)
        ).order_by(order_by).paginate(page=page, per_page=page_size)

        return {
            "records": schema.dump(records.items, many=True) ,
            "pagination": {
                "total_records": records.total,
                "total_pages": records.pages,
                "page": records.page,
            }
        }, 200

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
                for field in isDuplicated:
                    raise ValidationError(
                        {field["field"]: [{"status": "5",
                                           "msg": "Duplicated record found: {}".format(field["value"])}]}
                    )

            record.save()
            return schema.dump(record), 201

        except ValidationError as err:
            return err.normalized_messages(), 400

    def getRecord(self, recordId, only=None, exclude=()):
        """
        Return a record filterd by its id
        """
        schema = self.Schema(exclude=exclude, only=only)
        record = self.getOr404(recordId)
        return schema.dump(record), 200

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
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            for field in data.keys():
                if data[field] != record[field]:
                    record[field] = data[field]
                    has_changed = True
                    if field in uniquesFields:
                        fieldsForCheckDuplicates.append(
                            {"field": field, "value": data[field]})

            if has_changed:
                isDuplicated = self.checkForDuplicates(
                    fieldsForCheckDuplicates)
                if isDuplicated:
                    for field in isDuplicated:
                        raise ValidationError(
                            {field["field"]: [{"status": "5",
                                               "msg": "Duplicated record found: {}".format(field["value"])}]}
                        )

                record.save()

            return schema.dump(record), 200
        except ValidationError as err:
            return err.messages, 400

    def deleteRecord(self, recordId):
        """
        Delete (change status False) a record
        """
        record = self.getOr404(recordId)
        try:
            record.isDeleted = True
            record.save()
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

        return {"message": "Record deleted successfully"}, 200

    def checkForDuplicates(self, attributes):
        """
        Return True if find an duplicate field
        Return False otherwise

        Params.
        attributes: array. example [{"field":"name", "value":"Iribarren"}]
        """
        filterList = []

        if len(attributes):
            for f in attributes:
                filterList.append(Q(**{f['field']: f['value']}))

            if self.Model.__base__._meta['allow_inheritance']:
                records = self.Model.__base__.objects.filter(
                    reduce(operator.or_, filterList),
                    isDeleted=False
                ).all()
            else:
                records = self.Model.objects.filter(
                    reduce(operator.or_, filterList),
                    isDeleted=False
                ).all()
            if records:
                duplicates = []
                for record in records:
                    for attr in attributes:
                        if attr['value'] == record[attr['field']]:
                            duplicates.append(attr)
                return duplicates
        return False

    def getOr404(self, recordId):
        """
        Return a record filterd by its id.
        Otherwise return a 404 not found error
        """

        record = self.Model.objects(id=recordId, isDeleted=False).first()
        if not record:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": recordId})
        return record


def getRecordById(model, recordId):
    """Method that find a record by its id
    Return record if found
    params:
      model: a document model
      recordId: id for search
    """
    if len(str(recordId)) != 24:
        return False

    record = model.objects(id=str(recordId), isDeleted=False).first()
    if not record:
        return False

    return record
