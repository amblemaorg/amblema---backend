# app/services/monitoring_activities_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.monitoring_activity_model import (
    MonitoringActivity, DetailActivity)
from app.schemas.monitoring_activity_schema import MonitoringActivitySchema
from app.models.school_year_model import SchoolYear
from app.helpers.error_helpers import RegisterNotFound


class MonitoringActivitiesService():

    def get(self):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = MonitoringActivitySchema()
            monitoringActivities = schoolYear.pecaSetting.monitoringActivities
            return schema.dump(monitoringActivities), 200
        else:
            raise RegisterNotFound(
                message="Active school year not found", status_code=404)

    def save(self, jsonData):

        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        if schoolYear:
            try:
                schema = MonitoringActivitySchema()
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                monitoringActivities = MonitoringActivity()

                for field in schema.dump(data).keys():
                    for item in data[field]:
                        detail = DetailActivity()
                        detail.image = item['image']
                        detail.description = item['description']
                        monitoringActivities[field].append(detail)

                try:
                    schoolYear.pecaSetting.monitoringActivities = monitoringActivities
                    schoolYear.save()
                    return schema.dump(monitoringActivities), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(
                message="Active school year not found", status_code=404)
