# app/services/project_handler_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.helpers.handler_messages import HandlerMessages


class ProjectHandlerService(GenericServices):

    handlerMessages = HandlerMessages()

    def getRecord(self, recordId, only=None, exclude=()):
        """
        Return a record filterd by its id
        """
        schema = self.Schema(exclude=exclude, only=only)
        record = self.getOr404(recordId)
        record.stepsProgress.steps = sorted(
            record.stepsProgress.steps, key=lambda x: (x['tag'], x['sort']))
        return schema.dump(record), 200

    def deleteRecord(self, recordId):
        """
        Delete (change status False) a record
        """

        from app.models.request_content_approval_model import RequestContentApproval
        from app.models.request_find_coordinator_model import RequestFindCoordinator
        from app.models.request_find_sponsor_model import RequestFindSponsor
        from app.models.request_find_school_model import RequestFindSchool

        record = self.getOr404(recordId)

        entity = ''
        contentRequest = RequestContentApproval.objects(
            isDeleted=False, project__id=recordId, status="1").first()
        if contentRequest:
            entity = 'RequestContentApproval'
        else:
            findSchool = RequestFindSchool.objects(
                isDeleted=False, project=recordId, status="1").first()
            if findSchool:
                entity = 'RequestFindSchool'
            else:
                findSponsor = RequestFindSponsor.objects(
                    isDeleted=False, project=recordId, status="1").first()
                if findSponsor:
                    entity = 'RequestFindSponsor'
                else:
                    findCoordinator = RequestFindCoordinator.objects(
                        isDeleted=False, project=recordId, status="1").first()
                    if findCoordinator:
                        entity = 'RequestFindCoordinator'
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
