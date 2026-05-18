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
    def getAllContactsRequest(self, filters=None, only=None):
        query_filters = {'isDeleted': False}
        if filters:
            for f in filters:
                if f['field'] == 'status':
                    query_filters['status'] = f['value']

        coordinatorReq = CoordinatorContact.objects(
            **query_filters).order_by('-createdAt')
        sponsorReq = SponsorContact.objects(
            **query_filters).order_by('-createdAt')
        schoolReq = SchoolContact.objects(
            **query_filters).order_by('-createdAt')

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

        if only:
            coord_only = [f for f in only if f in CoordinatorContactSchema().fields.keys()]
            sponsor_only = [f for f in only if f in SponsorContactSchema().fields.keys()]
            school_only = [f for f in only if f in SchoolContactSchema().fields.keys()]
        else:
            coord_only = None
            sponsor_only = None
            school_only = None

        jsonRequests = []
        for request in requests:
            if request['type'] == 'coordinator':
                data = CoordinatorContactSchema(only=coord_only).dump(request['record']) if coord_only else CoordinatorContactSchema().dump(request['record'])
                data['type'] = 'coordinator'
                data['name'] = request['record']['firstName'] + \
                    ' ' + request['record']['lastName']
            if request['type'] == 'sponsor':
                data = SponsorContactSchema(only=sponsor_only).dump(request['record']) if sponsor_only else SponsorContactSchema().dump(request['record'])
                data['type'] = 'sponsor'
            if request['type'] == 'school':
                data = SchoolContactSchema(only=school_only).dump(request['record']) if school_only else SchoolContactSchema().dump(request['record'])
                data['type'] = 'school'
            jsonRequests.append(data)

        return {"records": jsonRequests}, 200

    def getAllFindRequest(self, filters=None, only=None):
        query_filters = {'isDeleted': False}
        if filters:
            for f in filters:
                if f['field'] == 'status':
                    query_filters['status'] = f['value']

        coordinatorReq = RequestFindCoordinator.objects(
            **query_filters).order_by('-createdAt')
        sponsorReq = RequestFindSponsor.objects(
            **query_filters).order_by('-createdAt')
        schoolReq = RequestFindSchool.objects(
            **query_filters).order_by('-createdAt')

        if only:
            coord_only = [f for f in only if f in ReqFindCoordSchema().fields.keys()]
            sponsor_only = [f for f in only if f in ReqFindSponsorSchema().fields.keys()]
            school_only = [f for f in only if f in ReqFindSchoolSchema().fields.keys()]
        else:
            coord_only = None
            sponsor_only = None
            school_only = None

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
                    'record': ReqFindCoordSchema(only=coord_only).dump(coord) if coord_only else ReqFindCoordSchema().dump(coord),
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
                    'record': ReqFindSponsorSchema(only=sponsor_only).dump(sponsor) if sponsor_only else ReqFindSponsorSchema().dump(sponsor),
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
                    'record': ReqFindSchoolSchema(only=school_only).dump(school) if school_only else ReqFindSchoolSchema().dump(school),
                    'status': school.status
                }
            )

        requests = coords + sponsors + schools
        requests = sorted(requests, reverse=True, key=lambda x: x['createdAt'])

        # for request in requests:
        #    request['createdAt'] = request['createdAt'].strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        return {"records": requests}, 200
