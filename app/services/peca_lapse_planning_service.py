# app/services/peca_lapse_planning_service.py

import copy
import os
import os.path

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_lapse_planning_model import LapsePlanningPeca
from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
from app.models.request_content_approval_model import RequestContentApproval
from app.models.user_model import User
from app.models.shared_embedded_documents import Approval
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from resources.files import files_path


class LapsePlanningService():

    filesFolder = 'lapse_planning'

    def get(self, pecaId, lapse):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = LapsePlanningPecaSchema()
            lapsePlanning = peca['lapse{}'.format(
                lapse)].lapsePlanning
            return schema.dump(lapsePlanning), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, lapse, jsonData, userId, files=None):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = LapsePlanningPecaSchema()

                if not peca['lapse{}'.format(lapse)].lapsePlanning:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"lapsePlanning lapse: ": lapse})

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                lapsePlanning = peca['lapse{}'.format(
                    lapse)].lapsePlanning
                oldLapsePlanning = copy.copy(lapsePlanning)

                if files and lapsePlanning.isInApproval:
                    return {
                        "status": "0",
                        "msg": "Record has a pending approval request"
                    }, 400

                documentFiles = getFileFields(LapsePlanningPeca)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    folder = "school_years/{}/pecas/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesFolder
                    )
                    DIR = files_path + '/' + folder
                    folder = folder + \
                        '/{}'.format(len([name for name in os.listdir(DIR)]) + 1
                                     if os.path.exists(DIR) else 1)
                    uploadedfiles = upload_files(validFiles, folder)
                    jsonData.update(uploadedfiles)

                data = schema.load(jsonData)

                approval = False
                if 'attachedFile' in data:
                    approval = True

                try:
                    if approval:
                        jsonData['pecaId'] = pecaId
                        jsonData['lapse'] = lapse
                        request = RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="8",
                            detail=jsonData
                        ).save()
                        lapsePlanning.isInApproval = True
                        if 'meetingDate' in data:
                            lapsePlanning.meetingDate = data['meetingDate']
                        lapsePlanning.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user.id,
                                detail=jsonData
                            )
                        )
                    else:
                        for field in schema.dump(data).keys():
                            lapsePlanning[field] = data[field]

                    if lapsePlanning.meetingDate != oldLapsePlanning.meetingDate:
                        peca.scheduleActivity(
                            devName="lapseplanning__meetingDate",
                            subject="Planificación de lapso {}".format(lapse),
                            startTime=lapsePlanning.meetingDate,
                            description="Fecha de reunión"
                        )
                    peca.save()
                    return schema.dump(lapsePlanning), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
