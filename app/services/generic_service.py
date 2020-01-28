# app/services/generic_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields



class GenericServices():
    def __init__(self, Model, Schema):
        self.Model = Model
        self.Schema = Schema

    def getAllRecords(self, filters=None, only=None, exclude=()):
        """
        get all available states records
        """
        if only and exclude: schema = self.Schema(only=only, exclude=exclude)
        elif only: schema = self.Schema(only=only)
        elif exclude: schema = self.Schema(exclude=exclude)
        else: schema = self.Schema()

        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records = self.Model.objects(status = True).filter(
                reduce(operator.and_, filterList)).all()
        else:
            records = self.Model.objects(status = True).all()
        
        return schema.dump(records, many=True), 200

    
    def saveRecord(self, jsonData):
        """
        Method that saves a new record.   
        params: jsonData
        """
        schema = self.Schema()
        try:
            data = schema.load(jsonData)
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            record = self.Model()
            for field in data.keys():
                record[field] = data[field]
                if field in uniquesFields:
                    fieldsForCheckDuplicates.append(
                        {"field":field, "value":data[field]})
            isDuplicated = self.checkForDuplicates(fieldsForCheckDuplicates)
            if isDuplicated:
                return {
                    "message": "Duplicated record found.",
                    "data":isDuplicated}, 400
            try:
                record.save()
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.messages, 400

    
    def getRecord(self, recordId):
        """
        Return a record filterd by its id
        """
        schema = self.Schema()
        record = self.getOr404(recordId)
        return schema.dump(record), 200

    
    def updateRecord(self, recordId, jsonData, partial=False, exclude=())):
        """
        Update a record
        """
        schema = self.Schema(exclude=exclude)
        try:
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
                            {"field":field, "value":data[field]})
            
            if has_changed:
                isDuplicated = self.checkForDuplicates(fieldsForCheckDuplicates)
                if isDuplicated:
                    return {
                        "message": "Duplicates record found.",
                        "data": isDuplicated}, 400
                try:
                    record.save()
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            
            return schema.dump(record), 200
        except ValidationError as err:
            return err.messages, 400


    def deleteRecord(self, recordId):
        """
        Delete (change status False) a record
        """
        record = self.getOr404(recordId)
        try:
            record.status = False
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
                    reduce(operator.and_, filterList)
                    ).all()
            else: 
                records = self.Model.objects.filter(
                    reduce(operator.and_, filterList)
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
        
        record = self.Model.objects(id=recordId, status=True).first()
        if not record:
            raise RegisterNotFound(message="Record not found",
                                status_code=404,
                                payload={"recordId": recordId})
        return record

def getRecordOr404(model, recordId):
    """Method that find a record by its id  
    Return record if found  
    params:  
      model: a document model
      recordId: id for search
    """
    record = model.objects(id=str(recordId), status=True).first()
    if not record:
        raise RegisterNotFound(message="Record not found",
                               status_code=404,
                               payload={"Model": model.__name__, "recordId": recordId})

    return record