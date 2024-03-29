# app/services/request_content_approval_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices


class RequestContentApprovalService(GenericServices):
    def getAllRecords(self, filters=None, only=None, exclude=()):
        """
        get all available roles records
        """
        schema = self.Schema(only=only, exclude=exclude)

        recordsJson = []
        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records = self.Model.objects(isDeleted=False).filter(
                reduce(operator.and_, filterList)).order_by("-updatedAt","status").limit(50)
        else:
            records = self.Model.objects(
                isDeleted=False).order_by("-updatedAt","status").limit(50)
        
        for record in records:
            # Check if the sections key exists in detail
            if "sections" in record["detail"]:
                for section in record["detail"]["sections"]:
                    # Check if the key students exists in section to remove it from the response
                    if "students" in section:
                        del section["students"]
                    
            data = schema.dump(record)
            data['typeUser'] = record.user.userType
        
            recordsJson.append(data)
        
        return {"records": recordsJson}, 200
