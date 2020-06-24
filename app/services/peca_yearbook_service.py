# app/services/peca_yearbook_service.py

from flask import current_app
from marshmallow import ValidationError
import copy
import os
import os.path

from app.models.peca_project_model import PecaProject
from app.models.peca_yearbook_model import Yearbook
from app.schemas.peca_yearbook_schema import YearbookSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.user_model import User
from app.models.peca_activities_model import Approval
from app.models.request_content_approval_model import RequestContentApproval
from app.helpers.handler_images import upload_image
from resources.images import path_images


class YearbookService():

    filesPath = 'yearbook'

    def save(self, pecaId, userId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = YearbookSchema()

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                self.filesPath = "school_years/{}/pecas/{}/{}".format(
                    peca.schoolYear.pk,
                    peca.pk,
                    self.filesPath
                )
                DIR = path_images + '/' + self.filesPath
                self.filesPath = self.filesPath + \
                    '/{}'.format(len([name for name in os.listdir(DIR)])
                                 if os.path.exists(DIR) else 1)
                if str(jsonData['historicalReview']['image']).startswith('data'):
                    jsonData['historicalReview']['image'] = upload_image(
                        jsonData['historicalReview']['image'], self.filesPath, None)
                if str(jsonData['sponsor']['image']).startswith('data'):
                    jsonData['sponsor']['image'] = upload_image(
                        jsonData['sponsor']['image'], self.filesPath, None)
                if str(jsonData['school']['image']).startswith('data'):
                    jsonData['school']['image'] = upload_image(
                        jsonData['school']['image'], self.filesPath, None)
                if str(jsonData['coordinator']['image']).startswith('data'):
                    jsonData['coordinator']['image'] = upload_image(
                        jsonData['coordinator']['image'], self.filesPath, None)
                for lapse in [1, 2, 3]:
                    for activity in range(len(jsonData['lapse{}'.format(lapse)]['activities'])):
                        act = jsonData['lapse{}'.format(
                            lapse)]['activities'][activity]
                        for image in range(len(act['images'])):
                            img = act['images'][image]
                            if str(img).startswith('data'):
                                img = upload_image(
                                    img, self.filesPath, None)
                                jsonData['lapse{}'.format(
                                    lapse)]['activities'][activity]['images'][image] = img

                schema.validate(jsonData)
                yearbook = peca.yearbook

                if yearbook.isInApproval:
                    return {
                        "status": "0",
                        "msg": "Record has a pending approval request"
                    }, 400

                jsonData['pecaId'] = pecaId

                try:
                    request = RequestContentApproval(
                        project=peca.project,
                        user=user,
                        type="7",
                        detail=jsonData
                    ).save()
                    yearbook.isInApproval = True
                    yearbook.approvalHistory.append(
                        Approval(
                            id=str(request.id),
                            user=user.id,
                            detail=jsonData
                        )
                    )
                    peca.save()
                    return schema.dump(yearbook), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
