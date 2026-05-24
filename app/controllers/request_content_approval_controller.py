# app/controllers/request_content_approval_controller.py


from flask import request, current_app
from flask_restful import Resource

from app.services.generic_service import GenericServices
from app.models.request_content_approval_model import RequestContentApproval
from app.schemas.request_content_approval_schema import RequestContentApprovalSchema
from app.services.request_content_approval_service import RequestContentApprovalService
from app.helpers.handler_request import getQueryParams
from app.helpers.handler_authorization import jwt_required


class ReqContentApprovalController(Resource):
    service = RequestContentApprovalService(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
    )

    @jwt_required
    def get(self):
        filters = getQueryParams(request)
        only = None
        
        # Handling pagination params
        page = request.args.get('page')
        per_page = request.args.get('per_page')
        
        if 'only' in request.args:
            only = request.args['only'].split(',')
            
        if page and per_page:
            from app.models.user_model import User
            from mongoengine import Q
            
            new_filters = []
            for f in filters:
                if f['field'] == 'project':
                    new_filters.append({'field': 'project__code__icontains', 'value': f['value']})
                elif f['field'] == 'typeUser':
                    # typeUser is 1 (Coordinator), 2 (School), 3 (Sponsor)
                    # The frontend sends text like 'COORDINADOR', so we must map it back or just assume it matches the string representation
                    # Wait, the frontend filter sends whatever the user types. 
                    # If they type "coord", value is "coord".
                    val = str(f['value']).upper()
                    if "COOR" in val:
                        users = User.objects(userType='1').only('id')
                    elif "ESC" in val:
                        users = User.objects(userType='2').only('id')
                    elif "PAD" in val:
                        users = User.objects(userType='3').only('id')
                    else:
                        users = []
                    new_filters.append({'field': 'user__in', 'value': [u.id for u in users]})
                elif f['field'] == 'user':
                    users = User.objects(
                        Q(name__icontains=f['value']) | 
                        Q(firstName__icontains=f['value']) | 
                        Q(lastName__icontains=f['value'])
                    ).only('id')
                    new_filters.append({'field': 'user__in', 'value': [u.id for u in users]})
                elif f['field'] == 'type':
                    val = str(f['value']).upper()
                    type_val = None
                    if "PAS" in val: type_val = "1"
                    elif "TESTIMONIO" in val: type_val = "2"
                    elif "ACTIVIDAD" in val: type_val = "3"
                    elif "SLIDER" in val: type_val = "4"
                    elif "TALLER" in val: type_val = "5"
                    elif "ESPECIAL" in val: type_val = "6"
                    elif "ANUARIO" in val: type_val = "7"
                    elif "PLANIFICACION" in val: type_val = "8"
                    elif "FOTO" in val: type_val = "9"
                    
                    if type_val:
                        new_filters.append({'field': 'type', 'value': type_val})
                elif f['field'] == 'status':
                    val = str(f['value']).upper()
                    status_val = None
                    if "PENDIENTE" in val: status_val = "1"
                    elif "APROBADO" in val: status_val = "2"
                    elif "RECHAZADO" in val: status_val = "3"
                    elif "CANCELADO" in val: status_val = "4"
                    
                    if status_val:
                        new_filters.append({'field': 'status', 'value': status_val})
                elif f['field'] in ['page', 'per_page']:
                    continue
                else:
                    new_filters.append(f)
                    
            return self.service.getAllRecords(
                filters=new_filters, only=only, limit=int(per_page), skip=(int(page) - 1) * int(per_page), page=int(page))
        else:
            limit = request.args.get('limit', 50, type=int)
            skip = request.args.get('skip', 0, type=int)
            return self.service.getAllRecords(
                filters=filters, only=only, limit=limit, skip=skip)


class ReqContentApprovalHandlerController(Resource):
    service = RequestContentApprovalService(
        Model=RequestContentApproval,
        Schema=RequestContentApprovalSchema
    )

    @jwt_required
    def get(self, id):
        return self.service.getRecord(id)

    @jwt_required
    def put(self, id):
        jsonData = request.get_json()
        return self.service.updateRecord(
            recordId=id,
            jsonData=jsonData,
            files=request.files,
            partial=True)

    @jwt_required
    def delete(self, id):
        return self.service.deleteRecord(id)
