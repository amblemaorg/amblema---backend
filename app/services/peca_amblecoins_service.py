# app/services/peca_amblecoins_service.py

import copy

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_amblecoins_model import AmblecoinsPeca
from app.schemas.peca_amblecoins_schema import AmblecoinsPecaSchema
from app.helpers.error_helpers import RegisterNotFound
from app.services.peca_schedule_service import ScheduleService


class AmblecoinsPecaService():

    def get(self, pecaId, lapse):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = AmblecoinsPecaSchema()
            ambleCoins = peca['lapse{}'.format(
                lapse)].ambleCoins
            return schema.dump(ambleCoins), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, lapse, jsonData):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = AmblecoinsPecaSchema()
                data = schema.load(jsonData)

                if not peca['lapse{}'.format(lapse)].ambleCoins:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"ambleCoins lapse: ": lapse})

                ambleCoins = peca['lapse{}'.format(
                    lapse)].ambleCoins
                oldAmblecoins = copy.copy(ambleCoins)
                for field in schema.dump(data).keys():
                    ambleCoins[field] = data[field]
                try:
                    peca['lapse{}'.format(
                        lapse)].ambleCoins = ambleCoins
                    if ambleCoins.meetingDate != oldAmblecoins.meetingDate:
                        peca.scheduleActivity(
                            devName="amblecoins__meetingDate",
                            subject="AmbleMonedas",
                            startTime=ambleCoins.meetingDate,
                            description="Fecha de reunión"
                        )
                    if ambleCoins.elaborationDate != oldAmblecoins.elaborationDate:
                        peca.scheduleActivity(
                            devName="amblecoins__elaborationDate",
                            subject="AmbleMonedas",
                            startTime=ambleCoins.elaborationDate,
                            description="Fecha de elaboración"
                        )
                    peca.save()
                    return schema.dump(ambleCoins), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
