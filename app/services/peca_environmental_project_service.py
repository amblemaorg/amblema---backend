# app/services/peca_environmental_project_service.py

import copy

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.schemas.peca_environmental_project_schema import EnvironmentalProjectPecaSchema
from app.helpers.error_helpers import RegisterNotFound


class EnvironmentalProjectPecaService():

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = EnvironmentalProjectPecaSchema()
                data = schema.load(jsonData)

                project = peca.environmentalProject
                for field in schema.dump(data).keys():
                    project[field] = data[field]
                try:
                    peca.save()
                    return schema.dump(project), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
