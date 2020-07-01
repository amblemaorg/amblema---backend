# app/services/peca_activities_slider_service.py

from flask import current_app
from marshmallow import ValidationError
import copy
import os
import os.path

from app.models.peca_project_model import PecaProject
from app.helpers.error_helpers import RegisterNotFound
from app.schemas.peca_activities_slider_schema import ActivitiesSliderSchema
from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.models.peca_activities_model import Approval
from app.models.request_content_approval_model import RequestContentApproval
from app.helpers.handler_images import upload_image
from resources.images import path_images


class ActivitiesSliderService():

    filesPath = 'activities_slider'

    def save(self, pecaId, userId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = ActivitiesSliderSchema()

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                activitiesSlider = peca.school.activitiesSlider
                newActivitiesSlider = copy.copy(activitiesSlider)
                if activitiesSlider.isInApproval:
                    return {
                        "status": "0",
                        "msg": "Record has a pending approval request"
                    }, 400

                folder = "school_years/{}/pecas/{}/{}".format(
                    peca.schoolYear.pk,
                    peca.pk,
                    self.filesPath
                )
                DIR = path_images + '/' + folder
                folder = folder + \
                    '/{}'.format(len([name for name in os.listdir(DIR)]) + 1
                                 if os.path.exists(DIR) else 1)
                if 'slider' in jsonData:
                    for i in range(len(jsonData['slider'])):
                        if jsonData['slider'][i].startswith('data'):
                            jsonData['slider'][i] = upload_image(
                                jsonData['slider'][i], folder, None)

                data = schema.load(jsonData)

                approvalRequired = False
                oldImages = []
                for image in activitiesSlider.slider:
                    oldImages.append(image)

                for field in data.keys():
                    if activitiesSlider[field] != data[field]:
                        if field == 'slider':
                            for image in data[field]:
                                # new image
                                if image not in oldImages:
                                    approvalRequired = True
                        newActivitiesSlider[field] = data[field]

                try:
                    if approvalRequired:
                        jsonData['pecaId'] = pecaId
                        request = RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="9",
                            detail=jsonData
                        ).save()
                        activitiesSlider.isInApproval = True
                        activitiesSlider.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user.id,
                                detail=jsonData
                            )
                        )
                    else:
                        activitiesSlider = newActivitiesSlider
                        SchoolUser.objects(id=peca.project.school.id).update(
                            activitiesSlider=activitiesSlider.slider)
                    peca.save()
                    return schema.dump(activitiesSlider), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
