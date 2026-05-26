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

    def getPaginatedData(self, filters=None, page=1, page_size=10):
        """
        get paginated and optimized records for table
        """
        records_qs = self.Model.objects(isDeleted=False)

        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records_qs = records_qs.filter(reduce(operator.and_, filterList))

        # Order by status (1 = pending comes first), then by updatedAt desc
        records_qs = records_qs.order_by("status", "-updatedAt")

        import math
        total = records_qs.count()
        items = records_qs.skip((page - 1) * page_size).limit(page_size).only(
            'id', 'code', 'project', 'type', 'user', 'status', 'updatedAt', 'createdAt'
        ).all()
        pages = int(math.ceil(total / float(page_size))) if page_size else 0

        recordsJson = []
        for record in items:
            data = {
                "id": str(record.id),
                "code": record.code,
                "type": record.type,
                "status": record.status,
                "createdAt": record.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if record.createdAt else None,
                "updatedAt": record.updatedAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if record.updatedAt else None
            }
            if record.project:
                data["project"] = {
                    "id": str(record.project.id),
                    "code": record.project.code
                }
            if record.user:
                data["user"] = {
                    "id": str(record.user.id),
                    "name": record.user.name
                }
                data["typeUser"] = record.user.userType
            recordsJson.append(data)

        return {
            "records": recordsJson,
            "pagination": {
                "total_records": total,
                "total_pages": pages,
                "page": page,
            }
        }, 200
