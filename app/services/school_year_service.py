# app/services/school_year_service.py


import re
import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.schemas.project_schema import ProjectSchema
from app.helpers.error_helpers import RegisterNotFound
from app.services.generic_service import GenericServices


class SchoolYearService(GenericServices):

    def getAllRecords(self, filters=None, only=None, exclude=()):
        """
        get all available records
        """
        schema = self.Schema(only=only, exclude=exclude)

        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records = self.Model.objects(isDeleted=False).filter(
                reduce(operator.and_, filterList)).all()
        else:
            records = self.Model.objects(isDeleted=False).all()

        return {"dates": schema.dump(records, many=True)}, 200

    def saveRecord(self, jsonData, files=None):
        schema = self.Schema()
        try:
            data = schema.load(jsonData)
            oldSchoolYear = SchoolYear.objects(
                isDeleted=False, status="1").first()
            if oldSchoolYear:
                if oldSchoolYear.endDate > datetime.date.today():
                    return {
                        "status": "0",
                        "msg": "Current school year has not finished yet"
                    }, 400
                date = datetime.datetime.now()
                newSchoolYear = SchoolYear(
                    name="{} - {}".format(date.year, date.year+1),
                    startDate=date,
                    endDate=date.replace(date.year + 1),
                    pecaSetting=oldSchoolYear.pecaSetting
                ).save()
                oldSchoolYear.status = "2"
                oldSchoolYear.endDate = date
                oldSchoolYear.save()
            else:
                date = datetime.datetime.now()
                newSchoolYear = SchoolYear(
                    name="{} - {}".format(date.year, date.year+1),
                    startDate=date,
                    endDate=date.replace(date.year + 1)
                )
                newSchoolYear.initFirstPecaSetting()
                newSchoolYear.save()
            return schema.dump(newSchoolYear), 201
        except ValidationError as err:
            return err.normalized_messages(), 400

    def schoolEnroll(self, projectId, action=None):
        """
        Params:
          projectId: str
          action: str "add" or "delete"
        """

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()
        if not schoolYear:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404,
                                   payload={})
        project = Project.objects(
            id=projectId, isDeleted=False, phase="2").first()
        if not project:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={'projectId': projectId})

        if action and action == "delete":
            peca = PecaProject.objects(
                schoolYear=schoolYear.id,
                project__id=str(project.id),
                isDeleted=False).first()
            if not peca:
                return {
                    "status": "0",
                    "msg": "School is not enrolled in active school year"
                }, 400

            try:
                for resume in project.schoolYears:
                    if resume.pecaId == str(peca.id):
                        project.schoolYears.remove(resume)
                        break

                project.save()
                peca.isDeleted = True
                peca.save()
                return {'msg': 'Record deleted'}, 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

        else:

            peca = PecaProject.objects(
                schoolYear=schoolYear.id,
                project__id=str(project.id),
                isDeleted=False).first()
            if peca:
                return {
                    "status": "0",
                    "msg": "School already enrolled in active school year"
                }, 400

            try:
                project.createPeca()
                return ProjectSchema(exclude=['stepsProgress']).dump(project)
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

    def availableSchools(self):

        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        availableSchools = []
        enrolledSchools = []
        enrolledSchoolsIds = []
        if schoolYear:
            pecas = PecaProject.objects(
                schoolYear=schoolYear.id, isDeleted=False).only('project__school', 'project__id')
            for peca in pecas:
                enrolledSchools.append(
                    {
                        "id": str(peca.project.school.id),
                        "name": peca.project.school.name,
                        "code": peca.project.school.code,
                        "projectId": peca.project.id
                    }
                )
                enrolledSchoolsIds.append(peca.project.id)
            projects = Project.objects(
                isDeleted=False, phase="2", pk__nin=enrolledSchoolsIds)

            for project in projects:
                availableSchools.append(
                    {
                        "id": str(project.school.id),
                        "name": project.school.name,
                        "code": project.school.code,
                        "projectId": str(project.id)
                    }
                )
        return {
            "availableSchools": availableSchools,
            "enrolledSchools": enrolledSchools
        }, 200
