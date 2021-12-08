# app/services/school_year_service.py


import re
import datetime

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.schemas.project_schema import ProjectSchema
from app.helpers.error_helpers import RegisterNotFound
from app.services.generic_service import GenericServices
from app.models.peca_setting_model import EnvironmentalProject
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.helpers.handler_messages import HandlerMessages
from app.models.step_model import Step
from app.models.peca_student_model import Diagnostic

class SchoolYearService(GenericServices):

    handlerMessages = HandlerMessages()

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
                newYearEnds = date.year + 1 if date.month > 8 else date.year
                newSchoolYear = SchoolYear(
                    name="{} - {}".format(date.year, date.year+1),
                    startDate=date,
                    endDate=date.replace(newYearEnds, 8, 31),
                    pecaSetting=oldSchoolYear.pecaSetting
                )
                newSchoolYear.pecaSetting.environmentalProject = EnvironmentalProject()
                newSchoolYear.save()
                oldSchoolYear.status = "2"
                oldSchoolYear.endDate = date
                oldSchoolYear.save()
                bulkSteps = []
                steps = Step.objects(schoolYear=str(oldSchoolYear.id),
                                     isDeleted=False).all()
                for step in steps:
                    step.id = None
                    step.schoolYear = newSchoolYear.id
                    bulkSteps.append(
                        step
                    )
                if bulkSteps:
                    Step.objects.insert(bulkSteps)

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
        from app.models.request_content_approval_model import RequestContentApproval

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
            entity = ''
            contentRequest = RequestContentApproval.objects(
                isDeleted=False, detail__pecaId=str(peca.id), status="1").first()
            if contentRequest:
                entity = 'RequestContentApproval'
            if entity:
                return {
                    'status': '0',
                    'entity': entity,
                    'msg': self.handlerMessages.getDeleteEntityMsg(entity)
                }, 419

            try:
                for resume in project.schoolYears:
                    if resume.pecaId == str(peca.id):
                        project.schoolYears.remove(resume)
                        break

                project.save()
                peca.isDeleted = True
                peca.save()
                
                project.sponsor.updateProject(project)
                project.coordinator.updateProject(project)
                project.school.nStudents = 0
                project.school.nGrades = 0
                project.school.nSections = 0
                project.school.updateProject(project)
                
                # update counts for home page
                sponsorPecas = len(PecaProject.objects(
                    schoolYear=schoolYear.id,
                    project__sponsor__id=str(project.sponsor.id),
                    isDeleted=False).only('id'))
                coordinatorPecas = len(PecaProject.objects(
                    schoolYear=schoolYear.id,
                    project__coordinator__id=str(project.coordinator.id),
                    isDeleted=False).only('id'))
                schoolYear.nSchools -= 1
                schoolYear.nStudents -= peca.school.nStudents
                schoolYear.nTeachers -= peca.school.nTeachers
                schoolYear.nSponsors -= 1 if sponsorPecas == 0 else 0
                schoolYear.nCoordinators -= 1 if coordinatorPecas == 0 else 0
                schoolYear.refreshDiagnosticsSummary()
                schoolYear.save()
                school = SchoolUser.objects(isDeleted=False, code=project.school.code).first()
                if school:
                    school.nStudents = 0
                    school.olympicsSummary.medalsGold = 0
                    school.olympicsSummary.classified = 0
                    school.olympicsSummary.medalsSilver = 0
                    school.olympicsSummary.medalsBronze = 0
                    school.olympicsSummary.inscribed = 0
                    school.save()

                return {'msg': 'Record deleted'}, 200
            except Exception as e:
                print(e)
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
                
                project.sponsor.updateProject(project)
                project.school.updateProject(project)
                project.coordinator.updateProject(project)
                
                # update counts for home page
                sponsorPecas = len(PecaProject.objects(
                    schoolYear=schoolYear.id,
                    project__sponsor__id=str(project.sponsor.id),
                    isDeleted=False).only('id'))
                coordinatorPecas = len(PecaProject.objects(
                    schoolYear=schoolYear.id,
                    project__coordinator__id=str(project.coordinator.id),
                    isDeleted=False).only('id'))
                schoolYear.nSchools += 1
                schoolYear.nTeachers += project.school.nTeachers if project.school.nTeachers else 0
                schoolYear.nSponsors += 1 if sponsorPecas == 1 else 0
                schoolYear.nCoordinators += 1 if coordinatorPecas == 1 else 0
                schoolYear.save()
                school = SchoolUser.objects(isDeleted=False, code=project.school.code).first()
                if school:
                    school.nStudents = 0
                    school.olympicsSummary.medalsGold = 0
                    school.olympicsSummary.classified = 0
                    school.olympicsSummary.medalsSilver = 0
                    school.olympicsSummary.medalsBronze = 0
                    school.olympicsSummary.inscribed = 0
                    school.save()
                
                return ProjectSchema(exclude=['stepsProgress']).dump(project)
            except Exception as e:
                print(e)
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

    def updateStastistics(self):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        if schoolYear:
            pecas = PecaProject.objects(
                schoolYear=schoolYear.id, isDeleted=False).only('school', 'project')
            nTeachers = 0
            nStudents = 0
            for peca in pecas:
                schoolUser = SchoolUser.objects(isDeleted=False, id=peca.project.school.id).first()
                peca.school.nTeachers = len(schoolUser.teachers.filter(isDeleted=False))
                schoolUser.nTeachers = peca.school.nTeachers
                peca.school.nStudents = 0
                for section in peca.school.sections.filter(isDeleted=False):
                    peca.school.nStudents += len(section.students.filter(isDeleted=False))
                schoolUser.nStudents = peca.school.nStudents
                peca.save()
                schoolUser.save()
                nTeachers += peca.school.nTeachers
                nStudents += peca.school.nStudents
            schoolYear.nStudents = nStudents
            schoolYear.nTeachers = nTeachers
            schoolYear.save()
        return {"message": "Update Stastistics"}, 200
    
    def emptySchools(self):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        if schoolYear:
            pecas = PecaProject.objects(
                schoolYear=schoolYear.id, isDeleted=False).only('school', 'project')
            for peca in pecas:
                school = SchoolUser.objects(isDeleted=False, code=peca.school.code).first()
                if school:
                    school.nStudents = 0
                    school.olympicsSummary.medalsGold = 0
                    school.olympicsSummary.classified = 0
                    school.olympicsSummary.medalsSilver = 0
                    school.olympicsSummary.medalsBronze = 0
                    school.olympicsSummary.inscribed = 0
                    school.save()
        return {"message": "schools clear"}, 200
    
class CronDiagnosticosService():
    def run(self, limit, skip):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        if schoolYear:
            pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only('id','school','schoolYear').limit(limit).skip(skip)
            for peca in pecas:
                for section in peca.school.sections.filter(isDeleted=False):
                    section.refreshDiagnosticsSummary()
                    peca.school.refreshDiagnosticsSummary()
                peca.save()
                peca.reload()
                schoolYearPeca = peca.schoolYear.fetch()
                schoolYearPeca.refreshDiagnosticsSummary()
                schoolYearPeca.save()
            return {"message": "Cron ejecutado"}, 200            
        else:
            return {"message": "No hay año escolar activo"}, 200

class CronAddDiagnosticsService():
    def run(self, limit, skip):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        if schoolYear:
            pecas = PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only('id','school','schoolYear').limit(limit).skip(skip)
            for peca in pecas:
                for section in peca.school.sections.filter(isDeleted=False):
                    for student in section.students.filter():
                        if student.lapse1 == None:
                            student.lapse1 = Diagnostic()
                        if student.lapse2 == None:
                            student.lapse2 = Diagnostic()
                        if student.lapse3 == None:
                            student.lapse3 = Diagnostic()
                peca.save()
            return {"message": "Cron ejecutado"}, 200            
        else:
            return {"message": "No hay año escolar activo"}, 200
