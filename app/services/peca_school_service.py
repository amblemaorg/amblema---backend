# app/services/peca_school_service.py


import os
import os.path
import copy

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.schemas.peca_project_schema import SchoolSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.request_content_approval_model import RequestContentApproval
from resources.images import path_images
from app.helpers.handler_images import upload_image
from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.models.shared_embedded_documents import Approval


class SchoolService():

    filesFolder = 'slider'

    def get(self, pecaId):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).only('school').first()

        if peca:
            schema = SchoolSchema()
            return schema.dump(peca.school), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def save(self, pecaId, userId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                schema = SchoolSchema(partial=True)

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                school = peca.school
                newSchool = copy.copy(school)

                if 'slider' in jsonData:
                    self.filesFolder = "school_years/{}/pecas/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesFolder
                    )
                    DIR = path_images + '/' + self.filesFolder
                    self.filesFolder = self.filesFolder + \
                        '/{}'.format(len([name for name in os.listdir(DIR)])
                                     if os.path.exists(DIR) else 1)

                    for image in jsonData['slider']:
                        if str(image['image']).startswith('data'):
                            image['image'] = upload_image(
                                image['image'], self.filesFolder, None)

                data = schema.load(jsonData)

                approvalRequired = False
                oldImages = {}
                for image in school.slider:
                    oldImages[image.id] = image

                for field in data.keys():
                    if school[field] != data[field]:
                        if field == 'slider':
                            for image in data[field]:
                                # image was updated
                                if image.id in oldImages and image != oldImages[image.id]:
                                    approvalRequired = True
                                # new image
                                elif image.id not in oldImages:
                                    approvalRequired = True
                        else:
                            approvalRequired = True

                        newSchool[field] = data[field]

                try:
                    if approvalRequired:
                        if school.isInApproval:
                            return {
                                "status": "0",
                                "msg": "Record has a pending approval request"
                            }, 400
                        jsonData['pecaId'] = pecaId
                        request = RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="4",
                            detail=jsonData
                        ).save()
                        school.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user,
                                detail=jsonData)
                        )
                        school.isInApproval = True
                    else:
                        school = newSchool
                        schoolUser = SchoolUser.objects(
                            id=peca.project.school.id).first()
                        schoolUser.slider = school.slider
                        schoolUser.save()
                    peca.save()

                    return schema.dump(school), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})
