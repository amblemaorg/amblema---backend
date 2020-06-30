# app/services/peca_activities_service.py

import copy
import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_activities_model import ActivityFields, ActivityPeca, CheckElement
from app.schemas.peca_activities_schema import ActivityFieldsSchema, ActivityPecaSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.request_content_approval_model import RequestContentApproval
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class ActivitiesPecaService():

    filesPath = 'activities'

    def get(self, pecaId, lapse, activityId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            activity = peca['lapse{}'.format(lapse)].activities.filter(
                id=activityId, isDeleted=False).first()
            if activity:
                schema = ActivityPecaSchema()
                return schema.dump(activity), 200
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"activityId": activityId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, lapse, activityId, userId, jsonData, files=None):
        from app.models.peca_activities_model import Approval, ActivityFields
        from app.models.user_model import User
        from app.models.project_model import Project
        from app.models.shared_embedded_documents import ProjectReference

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = ActivityFieldsSchema()

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                activity = peca['lapse{}'.format(lapse)].activities.filter(
                    id=activityId).first()
                oldActivity = copy.copy(activity)
                if not activity:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"activityId":  "{} lapse: {}".format(activityId, lapse)})

                documentFiles = getFileFields(ActivityFields)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    folder = "school_years/{}/pecas/{}/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesPath,
                        activityId
                    )
                    uploadedfiles = upload_files(validFiles, folder)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                try:
                    # generate an approval request
                    if activity.approvalType == "3":
                        if activity.status == "2":
                            return {
                                "status": 0, "message": "An activity approval is pending"
                            }, 400
                        act = activity
                        for key in data.keys():
                            act[key] = data[key]
                        data = schema.dump(act)

                        data['pecaId'] = pecaId
                        data['lapse'] = lapse
                        #data['id'] = activityId
                        request = RequestContentApproval(
                            project=peca.project,
                            user=user,
                            type="3",
                            detail=data
                        ).save()
                        activity.status = "2"
                        activity.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user.id,
                                detail=data
                            )
                        )
                        if activity.hasDate and 'date' in data and data['date']:
                            schAct = schema.load(jsonData)
                            peca.scheduleActivity(
                                devName="activities__{}".format(activityId),
                                subject=activity.name,
                                startTime=schAct['date'],
                                description=""
                            )

                    else:
                        # approve only on fill all fields
                        if activity.approvalType == "2":
                            data.pop('status', None)

                        for field in data.keys():
                            activity[field] = data[field]
                        activity.checkStatus()
                        if activity.hasDate and activity.date != oldActivity.date:
                            peca.scheduleActivity(
                                devName="activities__{}".format(activityId),
                                subject=activity.name,
                                startTime=activity.date,
                                description=""
                            )
                    peca.save()
                    return ActivityPecaSchema().dump(activity), 200

                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
