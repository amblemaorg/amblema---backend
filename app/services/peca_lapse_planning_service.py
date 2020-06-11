# app/services/peca_lapse_planning_service.py

import copy

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_lapse_planning_model import LapsePlanningPeca
from app.schemas.peca_lapse_planning_schema import LapsePlanningPecaSchema
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields


class LapsePlanningService():

    filesPath = 'lapse_planning'

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

    def save(self, pecaId, lapse, jsonData, files=None):

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
                documentFiles = getFileFields(LapsePlanningPeca)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    self.filesPath = "school_years/{}/pecas/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesPath
                    )
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)

                data = schema.load(jsonData)

                lapsePlanning = peca['lapse{}'.format(
                    lapse)].lapsePlanning
                oldLapsePlanning = copy.copy(lapsePlanning)

                for field in schema.dump(data).keys():
                    lapsePlanning[field] = data[field]
                try:
                    peca['lapse{}'.format(
                        lapse)].lapsePlanning = lapsePlanning
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
