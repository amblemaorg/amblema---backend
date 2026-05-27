# app/services/notifications_service.py

from flask import current_app
from app.models.coordinator_contact_model import CoordinatorContact
from app.models.sponsor_contact_model import SponsorContact
from app.models.school_contact_model import SchoolContact
from app.models.request_find_coordinator_model import RequestFindCoordinator
from app.models.request_find_sponsor_model import RequestFindSponsor
from app.models.request_find_school_model import RequestFindSchool
from app.models.request_project_approval_model import RequestProjectApproval
from app.models.request_content_approval_model import RequestContentApproval
from app.models.school_year_model import SchoolYear
from app.models.project_model import Project

from app.schemas.coordinator_contact_schema import CoordinatorContactSchema
from app.schemas.sponsor_contact_schema import SponsorContactSchema
from app.schemas.school_contact_schema import SchoolContactSchema
from app.schemas.request_find_coordinator_schema import ReqFindCoordSchema
from app.schemas.request_find_sponsor_schema import ReqFindSponsorSchema
from app.schemas.request_find_school_schema import ReqFindSchoolSchema
from app.schemas.request_project_approval_schema import RequestProjectApprovalSchema
from app.schemas.request_content_approval_schema import RequestContentApprovalSchema

import datetime

class NotificationsService:
    def get_pending_notifications(self):
        active_school_year = SchoolYear.objects(isDeleted=False, status="1").first()
        
        start_date = None
        end_date = None
        if active_school_year and active_school_year.startDate and active_school_year.endDate:
            start_date = datetime.datetime.combine(active_school_year.startDate, datetime.time.min)
            end_date = datetime.datetime.combine(active_school_year.endDate, datetime.time.max)

        notifications = []

        query_kwargs = {"isDeleted": False, "status": "1"}
        if start_date and end_date:
            query_kwargs["createdAt__gte"] = start_date
            query_kwargs["createdAt__lte"] = end_date

        approval_kwargs = {"isDeleted": False, "status": "1"}
        if start_date and end_date:
            approval_kwargs["createdAt__gte"] = start_date
            approval_kwargs["createdAt__lte"] = end_date

        # 1. Contact Requests (notiType=1)
        coord_contacts = CoordinatorContact.objects(**query_kwargs).only('id', 'firstName', 'lastName', 'createdAt')
        for doc in coord_contacts:
            notifications.append({
                'id': str(doc.id),
                'notiType': 1,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'name': f"{doc.firstName} {doc.lastName}"
            })

        sponsor_contacts = SponsorContact.objects(**query_kwargs).only('id', 'createdAt')
        for doc in sponsor_contacts:
            notifications.append({
                'id': str(doc.id),
                'notiType': 1,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'type': 'sponsor'
            })

        school_contacts = SchoolContact.objects(**query_kwargs).only('id', 'createdAt')
        for doc in school_contacts:
            notifications.append({
                'id': str(doc.id),
                'notiType': 1,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'type': 'school'
            })

        # 2. Find Requests (notiType=2)
        coord_find = RequestFindCoordinator.objects(**query_kwargs).only('id', 'user', 'createdAt')
        for doc in coord_find:
            notifications.append({
                'id': str(doc.id),
                'notiType': 2,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'user': {'name': doc.user.name} if doc.user else None
            })

        sponsor_find = RequestFindSponsor.objects(**query_kwargs).only('id', 'user', 'createdAt')
        for doc in sponsor_find:
            notifications.append({
                'id': str(doc.id),
                'notiType': 2,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'user': {'name': doc.user.name} if doc.user else None
            })

        school_find = RequestFindSchool.objects(**query_kwargs).only('id', 'user', 'createdAt')
        for doc in school_find:
            notifications.append({
                'id': str(doc.id),
                'notiType': 2,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'user': {'name': doc.user.name} if doc.user else None
            })

        # 3. Project Approval (notiType=3)
        project_approvals = RequestProjectApproval.objects(**approval_kwargs).only('id', 'createdAt')
        for doc in project_approvals:
            notifications.append({
                'id': str(doc.id),
                'notiType': 3,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            })

        # 4. Content Approval (notiType=4)
        content_approvals = RequestContentApproval.objects(**approval_kwargs).only('id', 'user', 'createdAt')
        for doc in content_approvals:
            notifications.append({
                'id': str(doc.id),
                'notiType': 4,
                'createdAt': doc.createdAt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                'user': {'name': doc.user.name} if doc.user else None
            })

        # Sort by createdAt descending
        notifications = sorted(notifications, key=lambda x: x.get('createdAt', ''), reverse=True)

        return {"records": notifications}, 200
