# app/services/state_service.py


from datetime import datetime
from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.models.state_model import (
    Municipality,
    MunicipalitySchema)
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices


class StateService(GenericServices):

    def deleteRecord(self, recordId):
        """
        Delete (change status False) a record
        """

        from app.models.user_model import User
        from app.models.school_contact_model import SchoolContact
        from app.models.sponsor_contact_model import SponsorContact
        from app.models.coordinator_contact_model import CoordinatorContact
        from app.models.request_find_school_model import RequestFindSchool
        from app.models.request_find_sponsor_model import RequestFindSponsor
        from app.models.request_find_coordinator_model import RequestFindCoordinator
        from app.models.school_user_model import SchoolUser

        record = self.getOr404(recordId)

        entity = ''
        user = User.objects(
            isDeleted=False, userType__in=['1', '2', '3', '4'], addressState=recordId).first()
        if user:
            entity = 'AdminUser' if user.userType == '1' else 'CoordinatorUser' if user.userType == '2' else 'SponsorUser' if user.userType == '3' else 'SchoolUser'
        if not entity:
            schoolContact = SchoolContact.objects(Q(isDeleted=False) & (
                Q(addressState=recordId) | Q(sponsorAddressState=recordId))).first()
            if schoolContact:
                entity = 'SchoolContact'
            else:
                sponsorContact = SponsorContact.objects(Q(isDeleted=False) & (
                    Q(addressState=recordId) | Q(schoolAddressState=recordId))).first()
                if sponsorContact:
                    entity = 'SponsorContact'
                else:
                    coordinatorContact = CoordinatorContact.objects(
                        Q(isDeleted=False) & Q(addressState=recordId)).first()
                    if coordinatorContact:
                        entity = 'CoordinatorContact'
        if not entity:
            findSchool = RequestFindCoordinator.objects(
                isDeleted=False, addressState=recordId).first()
            if findSchool:
                entity = 'RequestFindSchool'
            else:
                findSponsor = RequestFindSponsor.objects(
                    isDeleted=False, addressState=recordId).first()
                if findSponsor:
                    entity = 'RequestFindSponsor'
                else:
                    findCoordinator = RequestFindCoordinator.objects(
                        isDeleted=False, addressState=recordId).first()
                    if findCoordinator:
                        entity = 'RequestFindCoordinator'
        if not entity:
            schools = SchoolUser.objects(
                isDeleted=False, teachers__isDeleted=False, teachers__addressMunicipality=recordId).only('teachers')
            for school in schools:
                teacher = school.teachers(
                    isDeleted=False, addressMunicipality=recordId).first()
                if teacher:
                    entity = 'Teacher'
                    break
        if entity:
            return {
                'status': '0',
                'entity': entity,
                'msg': 'Record has an active related entity'
            }, 419
        try:
            record.isDeleted = True
            record.save()
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

        return {"message": "Record deleted successfully"}, 200
