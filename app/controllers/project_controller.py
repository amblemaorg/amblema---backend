# /app/controllers/project_controller.py


from flask import request
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.services.project_service import ProjectService
from app.services.project_handler_service import ProjectHandlerService
from app.models.project_model import Project
from app.schemas.project_schema import ProjectSchema
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ProjectController(Resource):

    service = GenericServices(
        Model=Project,
        Schema=ProjectSchema)

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        
        # Handling pagination params
        page = request.args.get('page')
        per_page = request.args.get('per_page')

        if page and per_page:
            # Custom filter mapping for related fields
            from app.models.coordinator_user_model import CoordinatorUser
            from app.models.school_user_model import SchoolUser
            from app.models.sponsor_user_model import SponsorUser
            from mongoengine import Q

            # Transform filters
            new_filters = []
            for f in filters:
                if f['field'] == 'coordinator':
                    # Search coordinators by name
                    coordinators = CoordinatorUser.objects(
                        Q(firstName__icontains=f['value']) | Q(lastName__icontains=f['value'])
                    ).only('id')
                    new_filters.append({'field': 'coordinator__in', 'value': [c.id for c in coordinators]})
                elif f['field'] == 'school':
                    schools = SchoolUser.objects(name__icontains=f['value']).only('id')
                    new_filters.append({'field': 'school__in', 'value': [s.id for s in schools]})
                elif f['field'] == 'sponsor':
                    sponsors = SponsorUser.objects(name__icontains=f['value']).only('id')
                    new_filters.append({'field': 'sponsor__in', 'value': [s.id for s in sponsors]})
                elif f['field'] in ['phase', 'status']:
                     new_filters.append(f)
                elif f['field'] == 'page' or f['field'] == 'per_page':
                    continue
                else:
                    new_filters.append(f)

            return self.service.getPaginatedRecords(
                filters=new_filters,
                exclude=("stepsProgress",),
                page=int(page),
                page_size=int(per_page)
            )

        return self.service.getAllRecords(
            filters=filters,
            exclude=(
                "stepsProgress",
            ))

    @jwt_required
    def post(self):
        jsonData = request.get_json()
        return self.service.saveRecord(jsonData)


class ProjectHandlerController(Resource):

    service = ProjectHandlerService(
        Model=Project,
        Schema=ProjectSchema)

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.get_json()
        print(jsonData)
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)


class ProjectStepsController(Resource):
    service = ProjectService()

    @jwt_required
    def post(self, id):
        jsonData = request.form.to_dict()
        return self.service.updateStep(id, jsonData, request.files)


class ProjectPecaController(Resource):
    service = ProjectService()

    @jwt_required
    def get(self, id):
        """
        create a peca for a project  
        params : id -> projectId
        """

        return self.service.handlerCreatePeca(id)
