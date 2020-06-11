# app/services/peca_schedule_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_schedule_model import ScheduleActivity
from app.schemas.peca_schedule_schema import ScheduleActivitySchema
from app.helpers.error_helpers import RegisterNotFound


class ScheduleService():

    def getSchedule(self, pecaId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).only('schedule').first()

        if peca:
            schema = ScheduleActivitySchema()
            activities = peca.schedule
            activities = sorted(activities, key=lambda x: x['startTime'])
            return {"records": schema.dump(activities, many=True)}, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, jsonData):
        """
        create an activity into schedule array in peca_projects
        params: 
          jsonData: {
              subject: str,
              startTime: datetime,
              endTime: datetime,
              description: str
          }
        """

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).only('schedule').first()

        if peca:
            try:
                schema = ScheduleActivitySchema()

                data = schema.load(jsonData)
                activity = ScheduleActivity()
                for key in data.keys():
                    activity[key] = data[key]
                try:
                    peca.schedule.append(activity)
                    peca.save()
                    return schema.dump(activity), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
