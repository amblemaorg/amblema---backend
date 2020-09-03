# app/services/peca_initial_workshop_service.py

from flask import current_app
from marshmallow import ValidationError
import os
import os.path
import copy

from app.models.peca_project_model import PecaProject
from app.models.peca_initial_workshop_model import InitialWorkshopPeca
from app.models.request_content_approval_model import RequestContentApproval
from app.models.shared_embedded_documents import Approval
from app.models.user_model import User
from app.schemas.peca_initial_workshop_schema import InitialWorkshopPecaSchema
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.handler_images import upload_image
from app.helpers.document_metadata import getFileFields
from resources.images import path_images


class InitialWorkshopService():

    filesFolder = 'initial_workshop'

    def get(self, pecaId, lapse):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = InitialWorkshopPecaSchema()
            initialWorkshop = peca['lapse{}'.format(
                lapse)].initialWorkshop
            return schema.dump(initialWorkshop), 200
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
                schema = InitialWorkshopPecaSchema()

                if not peca['lapse{}'.format(lapse)].initialWorkshop:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"initialWorkshop lapse: ": lapse})

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                initialWorkshop = peca['lapse{}'.format(
                    lapse)].initialWorkshop
                oldInitialWorkshop = copy.copy(initialWorkshop)

                if initialWorkshop.isInApproval and ('description' in jsonData or 'images' in jsonData):
                    return {
                        "status": "0",
                        "msg": "Record has a pending approval request"
                    }, 400

                if 'images' in jsonData:
                    folder = "school_years/{}/pecas/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesFolder
                    )
                    DIR = path_images + '/' + folder
                    folder = folder + \
                        '/{}'.format(len([name for name in os.listdir(DIR)]) + 1
                                     if os.path.exists(DIR) else 1)
                    for image in jsonData['images']:
                        if str(image['image']).startswith('data'):
                            image['image'] = upload_image(
                                image['image'], folder, None)

                data = schema.load(jsonData)

                approval = False
                if 'description' in data or 'images' in data:
                    approval = True

                try:
                    if approval:
                        jsonData['pecaId'] = pecaId
                        jsonData['lapse'] = lapse
                        request = RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="5",
                            detail=jsonData
                        ).save()
                        initialWorkshop.isInApproval = True
                        initialWorkshop.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user.id,
                                detail=jsonData
                            )
                        )
                    else:
                        for field in data.keys():
                            initialWorkshop[field] = data[field]
                    if initialWorkshop.workshopDate != oldInitialWorkshop.workshopDate:
                        peca.scheduleActivity(
                            devName="initialworkshol__workshopDate",
                            activityId="initialWorkshop",
                            subject="Taller inicial",
                            startTime=initialWorkshop.workshopDate,
                            description="Fecha del taller"
                        )
                    peca['lapse{}'.format(
                        lapse)].initialWorkshop = initialWorkshop
                    peca.save()
                    return schema.dump(initialWorkshop), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
