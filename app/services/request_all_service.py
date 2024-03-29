# app/services/request_all_service.py

import datetime
import json

from flask import current_app

from app.models.request_find_coordinator_model import RequestFindCoordinator
from app.models.request_find_sponsor_model import RequestFindSponsor
from app.models.request_find_school_model import RequestFindSchool
from app.models.coordinator_contact_model import CoordinatorContact
from app.models.school_contact_model import SchoolContact
from app.models.sponsor_contact_model import SponsorContact
from app.schemas.coordinator_contact_schema import CoordinatorContactSchema
from app.schemas.sponsor_contact_schema import SponsorContactSchema
from app.schemas.school_contact_schema import SchoolContactSchema
from app.schemas.request_find_coordinator_schema import ReqFindCoordSchema
from app.schemas.request_find_sponsor_schema import ReqFindSponsorSchema
from app.schemas.request_find_school_schema import ReqFindSchoolSchema


class RequestsAll():
    def getAllContactsRequest(self, filters=None):
        coordinatorReq = CoordinatorContact.objects(
            isDeleted=False).order_by('-createdAt')
        sponsorReq = SponsorContact.objects(
            isDeleted=False).order_by('-createdAt')
        schoolReq = SchoolContact.objects(
            isDeleted=False).order_by('-createdAt')

        coords = []
        for coord in coordinatorReq:
            coords.append(
                {'id': coord.id, 'createdAt': coord.createdAt, 'type': 'coordinator', 'record': coord})
        sponsors = []
        for sponsor in sponsorReq:
            sponsors.append(
                {'id': sponsor.id, 'createdAt': sponsor.createdAt, 'type': 'sponsor', 'record': sponsor})
        schools = []
        for school in schoolReq:
            schools.append(
                {'id': school.id, 'createdAt': school.createdAt, 'type': 'school', 'record': school})

        requests = coords + sponsors + schools
        requests = sorted(requests, reverse=True, key=lambda x: x['createdAt'])

        jsonRequests = []
        for request in requests:
            if request['type'] == 'coordinator':
                data = CoordinatorContactSchema().dump(request['record'])
                data['type'] = 'coordinator'
                data['name'] = request['record']['firstName'] + \
                    ' ' + request['record']['lastName']
            if request['type'] == 'sponsor':
                data = SponsorContactSchema().dump(request['record'])
                data['type'] = 'sponsor'
            if request['type'] == 'school':
                data = SchoolContactSchema().dump(request['record'])
                data['type'] = 'school'
            jsonRequests.append(data)

        return {"records": jsonRequests}, 200

    def getAllFindRequest(self, filters=None):
        coordinatorReq = RequestFindCoordinator.objects(
            isDeleted=False).order_by('-createdAt')
        sponsorReq = RequestFindSponsor.objects(
            isDeleted=False).order_by('-createdAt')
        schoolReq = RequestFindSchool.objects(
            isDeleted=False).order_by('-createdAt')

        coords = []
        for coord in coordinatorReq:
            coords.append(
                {
                    'id': str(coord.id),
                    'requestCode': coord.requestCode.zfill(7),
                    'projectCode': coord.project.code.zfill(7),
                    'type': 'coordinator',
                    'user': coord.user.name,
                    'createdAt': coord.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'record': ReqFindCoordSchema().dump(coord),
                    'status': coord.status
                }
            )
        sponsors = []
        for sponsor in sponsorReq:
            sponsors.append(
                {
                    'id': str(sponsor.id),
                    'requestCode': sponsor.requestCode.zfill(7),
                    'projectCode': sponsor.project.code.zfill(7),
                    'type': 'sponsor',
                    'user': sponsor.user.name,
                    'createdAt': sponsor.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'record': ReqFindSponsorSchema().dump(sponsor),
                    'status': sponsor.status
                }
            )
        schools = []
        for school in schoolReq:
            schools.append(
                {
                    'id': str(school.id),
                    'requestCode': school.requestCode.zfill(7),
                    'projectCode': school.project.code.zfill(7),
                    'type': 'school',
                    'user': school.user.name,
                    'createdAt': school.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'record': ReqFindSchoolSchema().dump(school),
                    'status': school.status
                }
            )

        requests = coords + sponsors + schools
        requests = sorted(requests, reverse=True, key=lambda x: x['createdAt'])

        # for request in requests:
        #    request['createdAt'] = request['createdAt'].strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        return {"records": requests}, 200
