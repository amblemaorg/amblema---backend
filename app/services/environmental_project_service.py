# app/services/environmental_project_service.py

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import EnvironmentalProject
from app.schemas.peca_setting_schema import EnvironmentalProjectSchema
from app.helpers.error_helpers import RegisterNotFound
from pymongo import UpdateOne
from app.models.shared_embedded_documents import CheckElement


class EnvironmentalProjectService():

    def get(self):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = EnvironmentalProjectSchema()
            environmentalProject = schoolYear.pecaSetting.environmentalProject
            return schema.dump(environmentalProject), 200
        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404
                                   )

    def save(self, jsonData):

        from app.models.peca_project_model import PecaProject
        from app.models.peca_environmental_project_model import EnvironmentalProjectPeca, Lapse, Topic, LevelDetail, Level

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = EnvironmentalProjectSchema()
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()
                environmentalProject = schoolYear.pecaSetting.environmentalProject
                if not environmentalProject:
                    environmentalProject = EnvironmentalProject()
                for field in schema.dump(data).keys():
                    environmentalProject[field] = data[field]
                environmentalProject.validateTarget()
                try:

                    schoolYear.pecaSetting.environmentalProject = environmentalProject
                    schoolYear.save()
                    bulk_operations = []
                    for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                        peca.environmentalProject = environmentalProject
                        peca.environmentalProject.__class__ = EnvironmentalProjectPeca
                        for i in range(1, 4):
                            lapse = peca.environmentalProject['lapse{}'.format(
                                i)]
                            if lapse:
                                lapse.__class__ = Lapse
                                for topic in lapse.topics:
                                    topic.__class__ = Topic
                                    for level in topic.levels:
                                        level.__class__ = LevelDetail
                                        for target in level.target:
                                            target.__class__ = Level
                                        level.activities = [CheckElement(
                                            id=c.id, name=c.name) for c in level.activities] if level.activities else []
                        bulk_operations.append(
                            UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                    if bulk_operations:
                        PecaProject._get_collection() \
                            .bulk_write(bulk_operations, ordered=False)
                    return schema.dump(environmentalProject), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404
                                   )
