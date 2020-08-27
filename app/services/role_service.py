# app/services/entity_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.helpers.handler_messages import HandlerMessages


class RoleService(GenericServices):

    handlerMessages = HandlerMessages()

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
        # oculta los permisos que tienen que ver con el peca
        for record in records:
            record.permissions = [permission for permission in record.permissions if not permission.entityName.startswith('PECA')]

        return {"records": schema.dump(records, many=True)}, 200

    def deleteRecord(self, recordId):
        """
        Delete (change status False) a record
        """
        from app.models.user_model import User

        record = self.getOr404(recordId)

        if record.isStandard:
            return {'status': 0, 'message': 'Standard role can not be deleted'}, 400

        entity = ''
        user = User.objects(
            isDeleted=False, userType__in=['1', '2', '3', '4'], role=recordId).first()
        if user:
            entity = 'AdminUser' if user.userType == '1' else 'CoordinatorUser' if user.userType == '2' else 'SponsorUser' if user.userType == '3' else 'SchoolUser'

        if entity:
            return {
                'status': '0',
                'entity': entity,
                'msg': self.handlerMessages.getDeleteEntityMsg(entity)
            }, 419
        try:
            record.isDeleted = True
            record.save()
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

        return {"message": "Record deleted successfully"}, 200
