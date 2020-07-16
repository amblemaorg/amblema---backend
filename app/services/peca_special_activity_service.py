# app/services/special_activity_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

from app.models.peca_special_lapse_activity_model import (
    SpecialActivityPeca, ItemSpecialActivity)
from app.models.peca_project_model import PecaProject, Lapse
from app.schemas.peca_special_lapse_activity_schema import SpecialActivitySchema
from app.models.user_model import User
from app.models.shared_embedded_documents import Approval

from app.models.request_content_approval_model import RequestContentApproval
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class PecaSpecialActivityService():

    def save(self, pecaId, lapse, userId, jsonData):

        peca = PecaProject.objects(
            id=pecaId, isDeleted=False).first()

        if peca:
            try:
                schema = SpecialActivitySchema()
                schema.validate(jsonData)

                user = User.objects(id=str(userId), isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                if lapse in ("1", "2", "3"):

                    specialActivity = peca['lapse{}'.format(
                        lapse)].specialActivity
                    if specialActivity.isInApproval:
                        return {
                            "status": "0",
                            "msg": "Record has a pending approval request"
                        }, 400

                    try:
                        jsonData['pecaId'] = pecaId
                        jsonData['lapse'] = lapse
                        request = RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="6",
                            detail=jsonData
                        ).save()

                        specialActivity.isInApproval = True
                        specialActivity.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user.id,
                                detail=jsonData
                            )
                        )
                        peca.save()
                        return schema.dump(specialActivity), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400
                else:
                    return {'status': 0, 'message': 'The lapse is not valid'}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def get(self, pecaId, lapse):

        peca = PecaProject.objects(id=pecaId, isDeleted=False).only(
            "lapse{}".format(lapse)).first()

        if peca:
            if lapse in ("1", "2", "3"):
                if peca['lapse{}'.format(lapse)].specialActivity and not peca['lapse{}'.format(lapse)].specialActivity.isDeleted:
                    specialActivity = SpecialActivityPeca()

                    specialActivity.id = peca['lapse{}'.format(
                        lapse)].specialActivity.id
                    specialActivity.name = peca['lapse{}'.format(
                        lapse)].specialActivity.name
                    specialActivity.activityDate = peca['lapse{}'.format(
                        lapse)].specialActivity.activityDate
                    specialActivity.approvalStatus = peca['lapse{}'.format(
                        lapse)].specialActivity.approvalStatus
                    specialActivity.itemsActivities = peca['lapse{}'.format(
                        lapse)].specialActivity.itemsActivities
                    specialActivity.total = peca['lapse{}'.format(
                        lapse)].specialActivity.total
                    specialActivity.isDeleted = peca['lapse{}'.format(
                        lapse)].specialActivity.isDeleted
                    specialActivity.createdAt = peca['lapse{}'.format(
                        lapse)].specialActivity.createdAt
                    specialActivity.updatedAt = peca['lapse{}'.format(
                        lapse)].specialActivity.updatedAt

                    schema = SpecialActivitySchema()
                    return schema.dump(specialActivity), 200
                else:
                    return {'status': 0, 'message': 'There is no special activity in the lapse'}, 400
            else:
                return {'status': 0, 'message': 'The lapse is not valid'}, 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def update(self, pecaId, lapse, jsonData):

        peca = PecaProject.objects(id=pecaId, isDeleted=False).only(
            "lapse{}".format(lapse)).first()

        if peca:
            try:
                schema = SpecialActivitySchema()
                data = schema.load(jsonData)
                hasChanged = False

                if lapse in ("1", "2", "3"):
                    specialActivity = peca['lapse{}'.format(
                        lapse)].specialActivity
                    if specialActivity and not specialActivity.isDeleted:
                        for field in schema.dump(data).keys():
                            if field == "itemsActivities":
                                del specialActivity[field][:]
                                for item in data[field]:
                                    itemActivitity = ItemSpecialActivity()
                                    itemActivitity.name = item["name"]
                                    itemActivitity.description = item["description"]
                                    itemActivitity.quantity = item["quantity"]
                                    itemActivitity.unitPrice = item["unitPrice"]
                                    itemActivitity.tax = item["tax"]
                                    itemActivitity.subtotal = item["subtotal"]
                                    specialActivity[field].append(
                                        itemActivitity)
                                    hasChanged = True
                            else:
                                if specialActivity[field] != data[field]:
                                    hasChanged = True
                                    specialActivity[field] = data[field]

                        if hasChanged:
                            try:
                                peca.save()
                                return schema.dump(specialActivity), 200
                            except Exception as e:
                                return {'status': 0, 'message': str(e)}, 400
                    else:
                        return {'status': 0, 'message': 'There is no special activity in the lapse'}, 400
                else:
                    return {'status': 0, 'message': 'The lapse is not valid'}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def delete(self, pecaId, lapse):
        """
        Delete (change isDeleted to True) a record
        """

        peca = PecaProject.objects(id=pecaId, isDeleted=False).only(
            "lapse{}".format(lapse)).first()

        if peca:
            try:
                if peca['lapse{}'.format(lapse)].specialActivity:
                    peca['lapse{}'.format(
                        lapse)].specialActivity.isDeleted = True
                    peca.save()
                    return {"message": "Record deleted successfully"}, 200
                else:
                    return {'status': 0, 'message': 'There is no special activity in the lapse'}, 400
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
