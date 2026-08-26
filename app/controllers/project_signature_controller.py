# app/controllers/project_signature_controller.py

from flask import request
from flask_restful import Resource
from datetime import datetime
from app.models.project_model import Project, AgreementSignature
from app.schemas.project_schema import ProjectSchema
from app.helpers.handler_authorization import jwt_required
from app.services.project_handler_service import ProjectHandlerService


class ProjectSignatureController(Resource):

    @jwt_required
    def post(self, id):
        project = Project.objects(id=id, isDeleted=False).first()
        if not project:
            return {'status_code': 404, 'message': 'Project not found'}, 404

        data = request.get_json() or {}
        role = data.get('role')
        if not role or role not in ['school', 'sponsor', 'amblema']:
            return {'status_code': 400, 'message': 'Invalid role'}, 400

        # Remove existing signature for this role if present
        project.agreementSignatures = [
            sig for sig in project.agreementSignatures if sig.role != role
        ]

        new_sig = AgreementSignature(
            role=role,
            signerName=data.get('signerName', ''),
            signerTitle=data.get('signerTitle', ''),
            signatureData=data.get('signatureData', ''),
            signedAt=datetime.utcnow()
        )
        project.agreementSignatures.append(new_sig)
        project.save()

        handler = ProjectHandlerService(Model=Project, Schema=ProjectSchema)
        return handler.getRecord(id)
