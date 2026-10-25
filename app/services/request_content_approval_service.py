# app/services/request_content_approval_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q
import datetime

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.models.user_model import User
from app.helpers.reference_prefetch import _refId
from app.helpers.school_year_filter import get_school_year_date_filters


class RequestContentApprovalService(GenericServices):
    def getAllRecords(self, filters=None, only=None, exclude=(), limit=50, skip=0, page=None):
        """
        get all available roles records
        """
        schema = self.Schema(only=only, exclude=exclude)

        recordsJson = []
        import math
        
        # The active school year filter (createdAt__gte) comes from the controller
        query = self.Model.objects(isDeleted=False)

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
        
        return {"records": recordsJson}, 200

    # Table filters accepted by getPaginatedData: query param -> lookup
    PAGINATED_FILTERS = {
        'code': 'code__icontains',
        'project': 'project__code__icontains',
        'status': 'status',
        'type': 'type',
    }
    # Table sort columns accepted by getPaginatedData: query param -> db field
    PAGINATED_SORTS = {
        'code': 'code',
        'project': 'project.code',
        'type': 'type',
        'status': 'status',
        'updatedAt': 'updatedAt',
    }
    NUMERIC_STRING_SORTS = ('code', 'project.code')

    def getPaginatedData(self, args, page=1, page_size=10):
        """
        get paginated and optimized records for table.
        Only whitelisted filters/sorts from args are applied.
        """
        records_qs = self.Model.objects(isDeleted=False)

        for f in get_school_year_date_filters():
            records_qs = records_qs.filter(**{f['field']: f['value']})

        for param, lookup in self.PAGINATED_FILTERS.items():
            value = args.get(param)
            if value:
                records_qs = records_qs.filter(**{lookup: value})

        userConditions = {}
        if args.get('user'):
            userConditions['name__icontains'] = args.get('user')
        if args.get('typeUser'):
            userConditions['userType'] = args.get('typeUser')
        if userConditions:
            userIds = list(User.objects(**userConditions).scalar('id'))
            records_qs = records_qs.filter(user__in=userIds)

        sortField = self.PAGINATED_SORTS.get(args.get('_sort'))
        if sortField:
            direction = '-' if args.get('_order', '').upper() == 'DESC' else '+'
            records_qs = records_qs.order_by(direction + sortField, '-updatedAt')
            if sortField in self.NUMERIC_STRING_SORTS:
                # Codes are stored as strings: compare them as numbers ("9" < "10")
                records_qs = records_qs.collation({'locale': 'en', 'numericOrdering': True})
        else:
            # Order by status (1 = pending comes first), then by updatedAt desc
            records_qs = records_qs.order_by("status", "-updatedAt")

        import math
        total = records_qs.count()
        items = list(records_qs.skip((page - 1) * page_size).limit(page_size).only(
            'id', 'code', 'project.id', 'project.code', 'type', 'user', 'status',
            'updatedAt', 'createdAt'
        ).no_dereference())
        pages = int(math.ceil(total / float(page_size))) if page_size else 0

        # Load all the page users in one query instead of one per record
        userIds = set(filter(None, [_refId(r._data.get('user')) for r in items]))
        users = User.objects.only('name', 'userType').in_bulk(list(userIds)) if userIds else {}

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
            user = users.get(_refId(record._data.get('user')))
            if user:
                data["user"] = {
                    "id": str(user.id),
                    "name": user.name
                }
                data["typeUser"] = user.userType
            recordsJson.append(data)

        return {
            "records": recordsJson,
            "pagination": {
                "total_records": total,
                "total_pages": pages,
                "page": page,
            }
        }, 200
