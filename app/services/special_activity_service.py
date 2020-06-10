# app/services/special_activity_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.models.special_activity_model import SpecialActivity
from app.models.peca_project_model import PecaProject, Lapse
from app.schemas.special_activity_schema import SpecialActivitySchema
from app.models.user_model import User

from app.models.request_content_approval_model import RequestContentApproval
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class SpecialActivityService():

    def save(self, pecaId, lapse, userId, jsonData):

        peca = PecaProject.objects(id=pecaId, isDeleted=False).only("project").first()

        if peca:
            try:
                schema = SpecialActivitySchema()
                data = schema.load(jsonData)

                user = User.objects(id=str(userId), isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})
                
                if lapse != "0":
                    print(peca['lapse{}'.format(lapse)])
                    specialActivity = SpecialActivity()
                    for field in schema.dump(data).keys():
                        specialActivity[field] = data[field]
                    print(specialActivity.activityDate)
                    print(specialActivity.itemsActivities)
                    try:                        
                        if not peca['lapse{}'.format(lapse)]:
                            print("ALGO")
                            peca['lapse{}'.format(lapse)] = Lapse()
                        peca['lapse{}'.format(lapse)].specialActivity = SpecialActivity()
                        peca['lapse{}'.format(lapse)].specialActivity = specialActivity
                        print(peca['lapse{}'.format(lapse)].specialActivity.activityDate)
                        peca.save()
                        RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="2",
                            detail=schema.dump(specialActivity)
                        ).save()
                        return schema.dump(specialActivity), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400
                else:
                    return {'status': 0, 'message': 'debe colocar un lapso'}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})