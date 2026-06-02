# app/services/request_all_service.py

import datetime
import json

from flask import current_app

from app.models.request_find_coordinator_model import RequestFindCoordinator
from app.models.request_find_sponsor_model import RequestFindSponsor
from app.models.request_find_school_model import RequestFindSchool
from app.models.request_project_approval_model import RequestProjectApproval
from app.models.request_content_approval_model import RequestContentApproval
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
    def getPendingNotifications(self):
        from app.models.school_year_model import SchoolYear
        notifications = []
        
        active_school_year = SchoolYear.objects(isDeleted=False, status="1").first()
        if not active_school_year:
            return {"records": []}, 200

        query_filters = {
            'isDeleted': False,
            'status': "1"
        }
        
        if active_school_year.startDate and active_school_year.endDate:
            start_date = datetime.datetime.combine(active_school_year.startDate, datetime.time.min)
            end_date = datetime.datetime.combine(active_school_year.endDate, datetime.time.max)
            query_filters['createdAt__gte'] = start_date
            query_filters['createdAt__lte'] = end_date
        
        # 1. Project Requests (ContactRequests) - notiType 1
        coordinatorReq = CoordinatorContact.objects(**query_filters)
        sponsorReq = SponsorContact.objects(**query_filters)
        schoolReq = SchoolContact.objects(**query_filters)
        
        for req in coordinatorReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 1,
                'user': {'name': req.firstName + ' ' + req.lastName},
                'createdAt': req.createdAt
            })
        for req in sponsorReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 1,
                'user': {'name': req.name},
                'createdAt': req.createdAt
            })
        for req in schoolReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 1,
                'user': {'name': req.name},
                'createdAt': req.createdAt
            })
            
        # 2. User Creation Requests (FindRequests) - notiType 2
        coordFindReq = RequestFindCoordinator.objects(**query_filters)
        sponsorFindReq = RequestFindSponsor.objects(**query_filters)
        schoolFindReq = RequestFindSchool.objects(**query_filters)
        
        for req in coordFindReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 2,
                'user': {'name': req.user.name},
                'createdAt': req.createdAt
            })
        for req in sponsorFindReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 2,
                'user': {'name': req.user.name},
                'createdAt': req.createdAt
            })
        for req in schoolFindReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 2,
                'user': {'name': req.user.name},
                'createdAt': req.createdAt
            })
            
        # 3. Project Validation Requests - notiType 3
        projectApprovalReq = RequestProjectApproval.objects(**query_filters)
        for req in projectApprovalReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 3,
                'user': None,
                'createdAt': req.createdAt
            })
            
        # 4. Request Content - notiType 4
        contentApprovalReq = RequestContentApproval.objects(**query_filters)
        for req in contentApprovalReq:
            notifications.append({
                'id': str(req.id),
                'notiType': 4,
                'user': {'name': req.user.name} if req.user else None,
                'createdAt': req.createdAt
            })
            
        # Sort all by createdAt desc
        notifications = sorted(notifications, reverse=True, key=lambda x: x['createdAt'])
        
        # Format dates to string
        for noti in notifications:
            noti['createdAt'] = noti['createdAt'].strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            
        return {"records": notifications}, 200

    def getAllContactsRequest(self, filters=None, only=None):
        query_filters = {'isDeleted': False}
        if filters:
            for f in filters:
                if f['field'] in ['status', 'createdAt__gte', 'createdAt__lte']:
                    query_filters[f['field']] = f['value']

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
                if f['field'] in ['status', 'createdAt__gte', 'createdAt__lte']:
                    query_filters[f['field']] = f['value']

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
