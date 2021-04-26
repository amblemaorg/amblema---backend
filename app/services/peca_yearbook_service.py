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
from app.services.peca_project_service import PecaProjectService


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
                pecaService = PecaProjectService()
                school = SchoolUser.objects(id=peca.project.school.id).first()
                sponsor = SponsorUser.objects(id=peca.project.sponsor.id).first()
                coordinator = CoordinatorUser.objects(id=peca.project.coordinator.id).first()

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                folder = "school_years/{}/pecas/{}/{}".format(
                    peca.schoolYear.pk,
                    peca.pk,
                    self.filesPath
                )
                DIR = path_images + '/' + folder
                folder = folder + \
                    '/{}'.format(len([name for name in os.listdir(DIR)]) + 1
                                 if os.path.exists(DIR) else 1)
                if str(jsonData['historicalReview']['image']).startswith('data'):
                    jsonData['historicalReview']['image'] = upload_image(
                        jsonData['historicalReview']['image'], folder, None)
                if str(jsonData['sponsor']['image']).startswith('data'):
                    jsonData['sponsor']['image'] = upload_image(
                        jsonData['sponsor']['image'], folder, None)
                if str(jsonData['school']['image']).startswith('data'):
                    jsonData['school']['image'] = upload_image(
                        jsonData['school']['image'], folder, None)
                if str(jsonData['coordinator']['image']).startswith('data'):
                    jsonData['coordinator']['image'] = upload_image(
                        jsonData['coordinator']['image'], folder, None)
                
                for section in jsonData['sections']:
                    found = False
                    for oldSection in peca.school.sections:
                        if str(oldSection.id) == section['id']:
                            found = True
                            section['name'] = oldSection.name
                            section['grade'] = oldSection.grade
                            break
                    if not found:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"section": section['id']})
                    if str(section['image']).startswith('data'):
                        section['image'] = upload_image(
                            section['image'], folder, None)
                img_msg = []
                for lapse in [1, 2, 3]:
                    for activity in range(len(jsonData['lapse{}'.format(lapse)]['activities'])):
                        act = jsonData['lapse{}'.format(
                            lapse)]['activities'][activity]
                        images_save = []
                        for image in range(len(act['images'])):
                            img = act['images'][image]
                            if str(img).startswith('data'):
                                imgd = upload_image(
                                    img, folder, None, True)
                                if imgd != '' and imgd != None:
                                    images_save.append(imgd)
                                else:
                                    img_msg.append('La imagen '+str(image+1)+' es corrupta')
                        jsonData['lapse{}'.format(
                                        lapse)]['activities'][activity]['images'] = images_save
                schema.validate(jsonData)
                yearbook = peca.yearbook
                
                jsonData['pecaId'] = pecaId
                    
                try:
                    request = None
                    if "requestId" in jsonData:
                        if jsonData["requestId"] != "" and jsonData["requestId"]!=None:
                           request = RequestContentApproval.objects(id=jsonData["requestId"], project=peca.project, type="7", status="1", isDeleted=False).first()
                                        
                    if not request:
                        if yearbook.isInApproval:
                            return {
                                "status": "0",
                                "msg": "Record has a pending approval request"
                            }, 400
    
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
                    else:
                        del jsonData["requestId"]
                        request.detail = jsonData
                        request.save()
                        for history in yearbook.approvalHistory:
                            if history.id == str(request.id):
                                history.detail = jsonData
                    peca.save()
                    data = schema.dump(yearbook)
                    data = pecaService.getYearbookData(peca, school, sponsor, coordinator, data)
                    data["requestId"] = str(request.id)
                    data["msgs"] = img_msg
                    return data, 200
                except Exception as e:
                    print(e)
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
