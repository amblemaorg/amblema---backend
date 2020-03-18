# app/services/entity_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices


class RoleService(GenericServices):
    def getAllRecords(self, filters=None, only=None, exclude=()):
        """
        get all available roles records
        """
        schema = self.Schema(only=only, exclude=exclude)

        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records = self.Model.objects(isDeleted=False, devName__ne='superadmin').filter(
                reduce(operator.and_, filterList)).order_by('name')
        else:
            records = self.Model.objects(
                isDeleted=False, devName__ne='superadmin').order_by('name')

        return {"records": schema.dump(records, many=True)}, 200
