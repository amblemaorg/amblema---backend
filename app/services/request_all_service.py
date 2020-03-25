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


class RequestsAll():
    def getAllContactsRequest(self, filters=None):
        coordinatorReq = CoordinatorContact.objects.order_by('-createdAt')
        sponsorReq = SponsorContact.objects.order_by('-createdAt')
        schoolReq = SchoolContact.objects.order_by('-createdAt')

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
                jsonRequests.append(data)
            if request['type'] == 'sponsor':
                data = SponsorContactSchema().dump(request['record'])
                data['type'] = 'sponsor'
                jsonRequests.append(data)
            if request['type'] == 'school':
                data = SchoolContactSchema().dump(request['record'])
                data['type'] = 'school'
                jsonRequests.append(data)

        return {"records": jsonRequests}, 200
