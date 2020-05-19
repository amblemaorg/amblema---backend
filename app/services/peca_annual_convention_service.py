# app/services/peca_annual_convention_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject

from app.schemas.peca_annual_convention_schema import AnnualConventionSchema
from app.helpers.error_helpers import RegisterNotFound


class AnnualConventionService():

    def get(self, pecaId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = AnnualConventionSchema()
            for i in range(1, 4):
                if peca['lapse{}'.format(i)].annualConvention:
                    annualConvention = peca['lapse{}'.format(
                        i)].annualConvention
                    data = schema.dump(annualConvention)
                    return schema.dump(data), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = AnnualConventionSchema()
            try:
                data = schema.load(jsonData)
                for i in range(1, 4):
                    if peca['lapse{}'.format(i)].annualConvention:
                        record = peca['lapse{}'.format(i)].annualConvention
                        has_changed = False
                        for field in data.keys():
                            if data[field] != record[field]:
                                record[field] = data[field]
                                has_changed = True
                        if has_changed:

                            try:
                                peca['lapse{}'.format(
                                    i)].annualConvention = record
                                peca.save()
                            except Exception as e:
                                return {'status': 0, 'message': str(e)}, 400

                        return schema.dump(record), 200
            except ValidationError as err:
                return err.normalized_messages(), 400

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
