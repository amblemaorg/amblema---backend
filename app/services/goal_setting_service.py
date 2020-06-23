# app/services/goal_setting_service.py

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

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
        from app.models.peca_project_model import PecaProject

        inverseGrades = {
            '1': 'grade1',
            '2': 'grade2',
            '3': 'grade3',
            '4': 'grade4',
            '5': 'grade5',
            '6': 'grade6'
        }
        grades = {
            'grade1': '1',
            'grade2': '2',
            'grade3': '3',
            'grade4': '4',
            'grade5': '5',
            'grade6': '6'
        }
        updatedGrades = []
        updatedGoals = {}

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
                    if goalSetting[field] != data[field]:
                        goalSetting[field] = data[field]
                        updatedGoals[field] = data[field]
                        updatedGrades.append(grades[field])
                # try:
                schoolYear.save()
                bulk_operations = []
                pecas = PecaProject.objects(
                    schoolYear=schoolYear.id, isDeleted=False, school__sections__grade__in=updatedGrades)
                for peca in pecas:
                    updated = False
                    for reg in peca.school.sections:
                        if inverseGrades[reg.grade] in updatedGoals and not reg.isDeleted:
                            updated = True
                            #reg.goals = updatedGoals[inverseGrades[reg.grade]]
                            reg.refreshDiagnosticsSummary()
                    if updated:
                        bulk_operations.append(
                            UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))

                if bulk_operations:
                    PecaProject._get_collection() \
                        .bulk_write(bulk_operations, ordered=False)
                return schema.dump(goalSetting), 200
                # except Exception as e:
                #    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
