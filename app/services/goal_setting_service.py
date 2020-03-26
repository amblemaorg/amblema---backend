# app/services/goal_setting_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import GoalSetting
from app.schemas.peca_setting_schema import GoalSettingSchema


class GoalSettingService():

    def get(self, schoolYearId=None):
        if not schoolYearId:
            schoolYear = SchoolYear.objects(
                isDeleted=False, status="1").only("pecaSetting").first()
        else:
            schoolYear = SchoolYear.objects(
                isDeleted=False, id=schoolYearId).only("pecaSetting").first()
        if schoolYear:
            schema = GoalSettingSchema()
            goalSetting = schoolYear.pecaSetting.goalSetting
            return schema.dump(goalSetting), 200

    def save(self, jsonData):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = GoalSettingSchema()
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                goalSetting = schoolYear.pecaSetting.goalSetting
                for field in schema.dump(data).keys():
                    goalSetting[field] = data[field]
                try:
                    schoolYear.pecaSetting.goalSetting = goalSetting
                    schoolYear.save()
                    return schema.dump(goalSetting), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
