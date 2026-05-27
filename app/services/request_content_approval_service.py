# app/services/request_content_approval_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.models.school_year_model import SchoolYear


class RequestContentApprovalService(GenericServices):
    def getAllRecords(self, filters=None, only=None, exclude=(), limit=50, skip=0, page=None):
        """
        get all available roles records
        """
        schema = self.Schema(only=only, exclude=exclude)

        recordsJson = []
        import math
        
        query = self.Model.objects(isDeleted=False)
        
        active_school_year = SchoolYear.objects(isDeleted=False, status="1").first()
        if active_school_year:
            query = query.filter(
                createdAt__gte=active_school_year.startDate,
                createdAt__lte=active_school_year.endDate
            )
            
        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            query = query.filter(reduce(operator.and_, filterList))
            
        if only:
            only_fields = list(only)
            if 'user' not in only_fields:
                only_fields.append('user')
            query = query.only(*only_fields)
            
        total_records = query.count()
        records = query.order_by("status", "-updatedAt").skip(skip).limit(limit)

        
        for record in records:
            if not only or 'detail' in only:
                # Check if the sections key exists in detail
                if hasattr(record, 'detail') and record.detail and "sections" in record.detail:
                    for section in record.detail["sections"]:
                        # Check if the key students exists in section to remove it from the response
                        if "students" in section:
                            del section["students"]
                    
            data = schema.dump(record)
            if hasattr(record, 'user') and record.user:
                data['typeUser'] = record.user.userType
        
            recordsJson.append(data)
        
<<<<<<< HEAD
        
        response = {"records": recordsJson}
        
        if page is not None:
            total_pages = int(math.ceil(total_records / float(limit))) if limit else 0
            response["pagination"] = {
                "total_records": total_records,
                "total_pages": total_pages,
                "page": page
            }
            
        return response, 200
=======
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
>>>>>>> f055f1d044fa236b5edbae5a56d0211f069db42f
