# app/services/peca_activities_service.py

import copy
import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_activities_model import ActivityFields, ActivityPeca, CheckElement
from app.schemas.peca_activities_schema import ActivityFieldsSchema, ActivityPecaSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.request_content_approval_model import RequestContentApproval
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.models.school_year_model import SchoolYear


class ActivitiesPecaService():

    filesPath = 'activities'

    def get(self, pecaId, lapse, activityId):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            activity = peca['lapse{}'.format(lapse)].activities.filter(
                id=activityId, isDeleted=False).first()
            if activity:
                schema = ActivityPecaSchema()
                return schema.dump(activity), 200
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"activityId": activityId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def save(self, pecaId, lapse, activityId, userId, jsonData, files=None):
        from app.models.peca_activities_model import Approval, ActivityFields
        from app.models.user_model import User
        from app.models.project_model import Project
        from app.models.shared_embedded_documents import ProjectReference

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = ActivityFieldsSchema()

                user = User.objects(id=userId, isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                activity = peca['lapse{}'.format(lapse)].activities.filter(
                    id=activityId).first()
                oldActivity = copy.copy(activity)
                newActivity = copy.copy(activity)
                if not activity:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"activityId":  "{} lapse: {}".format(activityId, lapse)})

                jsonData['name'] = activity.name
                jsonData['devName'] = activity.devName
                jsonData['hasText'] = activity.hasText
                jsonData['hasDate'] = activity.hasDate
                jsonData['hasFile'] = activity.hasFile
                jsonData['hasVideo'] = activity.hasVideo
                jsonData['hasChecklist'] = activity.hasChecklist
                jsonData['hasUpload'] = activity.hasUpload
                if activity.hasText:
                    jsonData['text'] = activity.text
                if activity.hasFile:
                    jsonData['file'] = {
                        "name": activity.file.name,
                        "url": activity.file.url
                    }
                if activity.hasVideo:
                    jsonData['video'] = {
                        "name": activity.video.name,
                        "url": activity.video.url
                    }

                documentFiles = getFileFields(ActivityFields)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    folder = "school_years/{}/pecas/{}/{}/{}".format(
                        peca.schoolYear.pk,
                        peca.pk,
                        self.filesPath,
                        activityId
                    )
                    uploadedfiles = upload_files(validFiles, folder)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                try:

                    # generate an approval request
                    if activity.approvalType == "3":
                        if 'date' in data or 'uploadedFile' in data:
                            if activity.status == "2":
                                return {
                                    "status": 0, "message": "An activity approval is pending"
                                }, 400

                        for key in data.keys():
                            newActivity[key] = data[key]
                        data = schema.dump(newActivity)

                        jsonData['pecaId'] = pecaId
                        jsonData['lapse'] = lapse
                        jsonData['id'] = activityId

                        if jsonData["hasChecklist"]:
                            percent = 0
                            for act in data["checklist"]:
                                if act["checked"]:
                                    percent = percent + 1
                            if percent > 0:
                                percent = (percent/len(data["checklist"]))*100
                            jsonData["percent"] = percent

                        if 'date' in jsonData or 'uploadedFile' in jsonData:
                            request = RequestContentApproval(
                                project=peca.project,
                                user=user,
                                type="3",
                                detail=jsonData
                            ).save()
                            activity.status = "2"
                            activity.approvalHistory.append(
                                Approval(
                                    id=str(request.id),
                                    user=user.id,
                                    detail=jsonData
                                )
                            )
                            if activity.hasDate and 'date' in jsonData and jsonData['date']:
                                schAct = schema.load(jsonData)
                                peca.scheduleActivity(
                                    devName="activities__{}".format(
                                        activityId),
                                    activityId=str(activityId),
                                    subject=activity.name,
                                    startTime=schAct['date'],
                                    description=""
                                )
                        activity.checklist = newActivity.checklist
                        activity.checkStatus()

                    else:
                        # approve only on fill all fields
                        if activity.approvalType == "2":
                            data.pop('status', None)
                        if activity.hasChecklist:
                            percent = 0
                            for act in data["checklist"]:
                                if act["checked"]:
                                    percent = percent + 1
                            if percent > 0:
                                percent = (
                                    percent/len(data["checklist"]))*100
                            data["percent"] = percent
                            
                        for field in data.keys():
                            activity[field] = data[field]
                        activity.checkStatus()
                        if activity.hasDate and activity.date != oldActivity.date:
                            peca.scheduleActivity(
                                devName="activities__{}".format(activityId),
                                activityId=str(activityId),
                                subject=activity.name,
                                startTime=activity.date,
                                description=""
                            )
                    peca.save()
                    return ActivityPecaSchema().dump(activity), 200

                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})


class CronPecaActivitiesService():
    def cronPecaActivities(self, limit, skip):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("id").first()
        if schoolYear:
            pecas = PecaProject.objects(
                isDeleted=False, schoolYear=schoolYear.id).limit(limit).skip(skip)
            count_pecas = PecaProject.objects(
                isDeleted=False, schoolYear=schoolYear.id).count()
            for peca in pecas:
                for i in range(1, 4):
                    for activity in peca['lapse{}'.format(i)].activities:
                        # if activity.approvalType == "5":
                        if activity.hasChecklist:
                            percent = 0
                            for act in activity.checklist:
                                if act.checked:
                                    percent = percent + 1
                            if percent > 0:
                                percent = (percent/len(activity.checklist))*100
                            activity["percent"] = percent
                peca.save()
            return {"status_code": "200", "message": "Sincronizacion exitosa", "cantidad": count_pecas}, 200
        else:
            return {"status_code": "400", "message": "Sincronizacion fallida, año escolar inactivo"}, 200


class ReportActivityService():
    def getDataInicial(self):
        schoolYears = SchoolYear.objects(
            isDeleted=False)
        data = {"schoolYears": []}
        if len(schoolYears) > 0:
            for schoolYear in schoolYears:
                data_schoolyear = {"name": schoolYear.name, "status": schoolYear.status, "id": str(
                    schoolYear.id), "lapses": []}
                for i in range(1, 4):
                    lapseN = {"name": "Lapso "+str(i), "activities": []}
                    lapse = schoolYear.pecaSetting['lapse{}'.format(i)]
                    """if lapse.initialWorkshop:
                        if lapse.initialWorkshop.status == "1":
                            lapseN["activities"].append({"name": lapse.initialWorkshop.name, "devName": "initialWorkshop", "isStandard": lapse.initialWorkshop.isStandard})

                    if lapse.ambleCoins:
                        if lapse.ambleCoins.status == "1":
                            lapseN["activities"].append({"name": lapse.ambleCoins.name, "devName": "ambleCoins", "isStandard": lapse.ambleCoins.isStandard})
                    if lapse.lapsePlanning:
                        if lapse.lapsePlanning.status == "1":
                            lapseN["activities"].append({"name": lapse.lapsePlanning.name, "devName": "lapsePlanning", "isStandard": lapse.lapsePlanning.isStandard})
                    if lapse.annualConvention:
                        if lapse.annualConvention.status == "1":
                            lapseN["activities"].append({"name": lapse.annualConvention.name, "devName": "annualConvention", "isStandard": lapse.annualConvention.isStandard})
                    if lapse.annualPreparation:
                        if lapse.annualPreparation.status == "1":
                            lapseN["activities"].append({"name": lapse.annualPreparation.name, "devName": "annualPreparation", "isStandard": lapse.annualPreparation.isStandard})
                    if lapse.mathOlympic:
                        if lapse.mathOlympic.status == "1":
                            lapseN["activities"].append({"name": lapse.mathOlympic.name, "devName": "mathOlympic", "isStandard": lapse.mathOlympic.isStandard})
                    if lapse.specialLapseActivity:
                        if lapse.specialLapseActivity.status == "1":
                            lapseN["activities"].append({"name": lapse.specialLapseActivity.name, "devName": "specialLapseActivity", "isStandard": lapse.specialLapseActivity.isStandard})
                    """
                    for activity in lapse.activities:
                        if activity.status == "1" and activity.isDeleted == False:
                            lapseN["activities"].append(
                                {"name": activity.name, "devName": activity.devName, "isStandard": activity.isStandard})
                    data_schoolyear["lapses"].append(lapseN)

                pecas = PecaProject.objects(
                    isDeleted=False, schoolYear=schoolYear.id).only("id", "project")
                data_schoolyear["coordinators"] = []
                data_schoolyear["sponsors"] = []
                data_schoolyear["schools"] = []
                for peca in pecas:
                    if peca.project.coordinator:
                        data_schoolyear["coordinators"].append({"id": str(
                            peca.project.coordinator.id), "name": str(peca.project.coordinator.name)})
                    if peca.project.sponsor:
                        data_schoolyear["sponsors"].append(
                            {"id": str(peca.project.sponsor.id), "name": str(peca.project.sponsor.name)})
                    if peca.project.school:
                        data_schoolyear["schools"].append(
                            {"id": str(peca.project.school.id), "name": str(peca.project.school.name)})
                data_schoolyear["schools"] = self.remove_duplicates(
                    data_schoolyear["schools"])
                data_schoolyear["coordinators"] = self.remove_duplicates(
                    data_schoolyear["coordinators"])
                data_schoolyear["sponsors"] = self.remove_duplicates(
                    data_schoolyear["sponsors"])
                data["schoolYears"].append(data_schoolyear)

            return {"status_code": "200", "message": "Actividades", "data": data}, 200

        else:
            return {"status_code": "404", "message": "No hay año escolar activo"}, 200

    def generateReport(self, jsonData):
        try:
            if jsonData["type_filter"] == "schoolYear":
                if "schoolYear" in jsonData:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, id=jsonData["schoolYear"]).first()
                    if schoolYear:
                        lapses = []
                        activities = []
                        lapses_req = []
                        for lap in jsonData["lapses"]:
                            if lap == "Lapso 1":
                                lapses_req.append(1)
                            if lap == "Lapso 2":
                                lapses_req.append(2)
                            if lap == "Lapso 3":
                                lapses_req.append(3)

                        for i in lapses_req:
                            activities.append(
                                {"name": "Lapso "+str(i), "title": True, "lapse": i})
                            lapse = schoolYear.pecaSetting['lapse{}'.format(i)]
                            """
                            if lapse.initialWorkshop:
                                if lapse.initialWorkshop.status == "1":
                                    activities.append({"name": lapse.initialWorkshop.name, "title": False, "lapse": i})

                            if lapse.ambleCoins:
                                if lapse.ambleCoins.status == "1":
                                    activities.append({"name": lapse.ambleCoins.name, "title": False, "lapse": i})
                            
                            if lapse.lapsePlanning:
                                if lapse.lapsePlanning.status == "1":
                                    activities.append({"name": lapse.lapsePlanning.name, "title": False, "lapse": i})
                            
                            if lapse.annualConvention:
                                if lapse.annualConvention.status == "1":
                                    activities.append({"name": lapse.annualConvention.name, "title": False, "lapse": i})
                            
                            if lapse.annualPreparation:
                                if lapse.annualPreparation.status == "1":
                                    activities.append({"name": lapse.annualPreparation.name, "title": False, "lapse": i})
                            
                            if lapse.mathOlympic:
                                if lapse.mathOlympic.status == "1":
                                    activities.append({"name": lapse.mathOlympic.name, "title": False, "lapse": i})
                            if lapse.specialLapseActivity:
                                if lapse.specialLapseActivity.status == "1":
                                    activities.append({"name": lapse.specialLapseActivity.name, "title": False, "lapse": i})
                            """

                            for activity in lapse.activities:
                                if activity.status == "1" and activity.isDeleted == False:
                                    activities.append(
                                        {"name": activity.name, "title": False, "lapse": i})

                        # lapses.append(lapseN)

                        pecas = PecaProject.objects(isDeleted=False, schoolYear=schoolYear.id).only(
                            "id", "project", "lapse1", "lapse2", "lapse3")
                        schools = []
                        peca_active = []
                        for peca in pecas:
                            if peca.project.school:
                                schools.append(
                                    {"id": str(peca.project.school.id), "name": str(peca.project.school.name)})
                                peca_active.append(peca)
                        # pecas = PecaProject.objects(isDeleted=False, schoolYear: jsonData["schoolYear"]).only("lapse1", "lapse2", "lapse3", "school")
                        # for peca in pecas:
                        matriz = []
                        for i in range(0, len(activities)):
                            matriz.append(
                                {"activity": activities[i]["name"], "columns": []})
                            for j in range(0, len(schools)):
                                """
                                if peca_active[i]["lapse{}".format(activities[i]["lapse"])].initialWorkshop.name == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                elif "AmbLeMonedas" == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                elif peca_active[i]["lapse{}".format(activities[i]["lapse"])].lapsePlanning.name == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                elif peca_active[i]["lapse{}".format(activities[i]["lapse"])].annualConvention.name == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                elif peca_active[i]["lapse{}".format(activities[i]["lapse"])].annualPreparation.name == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                elif peca_active[i]["lapse{}".format(activities[i]["lapse"])].mathOlympic.name == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                elif peca_active[i]["lapse{}".format(activities[i]["lapse"])].specialLapseActivity.name == activities[i]["name"]:
                                    matriz[i]["columns"].append({"value": 100})
                                else:
                                """
                                for acti in peca_active[j]["lapse{}".format(activities[i]["lapse"])].activities:
                                    if acti.name == activities[i]["name"]:
                                        matriz[i]["columns"].append(
                                            {"value": int(acti.percent)})
                                        break

                        return {"status_code": "201", "message": "Reporte", "rows": activities, "columns": schools, "matriz": matriz}, 201
                    else:
                        return {"status_code": "404", "message": "Debe enviar un año escolar válido"}, 201

                else:
                    return {"status_code": "404", "message": "Debe enviar un año escolar"}, 201
            elif jsonData["type_filter"] == "coordinator":
                if "coordinators" in jsonData:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, id=jsonData["schoolYear"]).first()
                    if schoolYear:
                        lapses = []
                        activities = []
                        lapses_req = []
                        for lap in jsonData["lapses"]:
                            if lap == "Lapso 1":
                                lapses_req.append(1)
                            if lap == "Lapso 2":
                                lapses_req.append(2)
                            if lap == "Lapso 3":
                                lapses_req.append(3)

                        for i in lapses_req:
                            activities.append(
                                {"name": "Lapso "+str(i), "title": True, "lapse": i})
                            lapse = schoolYear.pecaSetting['lapse{}'.format(i)]

                            for activity in lapse.activities:
                                if activity.status == "1" and activity.isDeleted == False:
                                    activities.append(
                                        {"name": activity.name, "title": False, "lapse": i})
                        
                        pecas = PecaProject.objects(isDeleted=False, project__coordinator__id__in=jsonData["coordinators"], schoolYear=schoolYear.id).only(
                            "id", "project", "lapse1", "lapse2", "lapse3")
                        coordinators = []
                        peca_active = []
                        for peca in pecas:
                            if peca.project.school:
                                coordinators.append({"id": str(peca.project.coordinator.id), "name": str(
                                    peca.project.coordinator.name)+" - "+str(peca.project.school.name)})
                                peca_active.append(peca)
                        matriz = []
                        for i in range(0, len(activities)):
                            matriz.append(
                                {"activity": activities[i]["name"], "columns": []})
                            for j in range(0, len(coordinators)):
                                for acti in peca_active[j]["lapse{}".format(activities[i]["lapse"])].activities:
                                    if acti.name == activities[i]["name"]:
                                        matriz[i]["columns"].append(
                                            {"value": int(acti.percent)})
                                        break
                        return {"status_code": "201", "message": "Reporte", "rows": activities, "columns": coordinators, "matriz": matriz}, 201
                    else:
                        return {"status_code": "404", "message": "El año escolar no es válido"}, 201
                else:
                    return {"status_code": "404", "message": "Debe enviar por lo menos un coordinador"}, 201
            elif jsonData["type_filter"] == "school":
                if "schools" in jsonData:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, id=jsonData["schoolYear"]).first()
                    if schoolYear:
                        lapses = []
                        activities = []
                        lapses_req = []
                        for lap in jsonData["lapses"]:
                            if lap == "Lapso 1":
                                lapses_req.append(1)
                            if lap == "Lapso 2":
                                lapses_req.append(2)
                            if lap == "Lapso 3":
                                lapses_req.append(3)

                        for i in lapses_req:
                            activities.append(
                                {"name": "Lapso "+str(i), "title": True, "lapse": i})
                            lapse = schoolYear.pecaSetting['lapse{}'.format(i)]

                            for activity in lapse.activities:
                                if activity.status == "1" and activity.isDeleted == False:
                                    activities.append(
                                        {"name": activity.name, "title": False, "lapse": i})
                        pecas = PecaProject.objects(isDeleted=False, project__school__id__in=jsonData["schools"], schoolYear=schoolYear.id).only(
                            "id", "project", "lapse1", "lapse2", "lapse3")
                        schools = []
                        peca_active = []
                        for peca in pecas:
                            if peca.project.school:
                                schools.append(
                                    {"id": str(peca.project.school.id), "name": str(peca.project.school.name)})
                                peca_active.append(peca)
                        matriz = []
                        for i in range(0, len(activities)):
                            matriz.append(
                                {"activity": activities[i]["name"], "columns": []})
                            for j in range(0, len(schools)):
                                for acti in peca_active[j]["lapse{}".format(activities[i]["lapse"])].activities:
                                    if acti.name == activities[i]["name"]:
                                        matriz[i]["columns"].append(
                                            {"value": int(acti.percent)})
                                        break
                        return {"status_code": "201", "message": "Reporte", "rows": activities, "columns": schools, "matriz": matriz}, 201
                    else:
                        return {"status_code": "404", "message": "El año escolar no es válido"}, 201
                else:
                    return {"status_code": "404", "message": "Debe enviar por lo menos una escuela"}, 201

            elif jsonData["type_filter"] == "activity":
                if "activities" in jsonData:
                    schoolYear = SchoolYear.objects(
                        isDeleted=False, id=jsonData["schoolYear"]).first()
                    if schoolYear:
                        lapses = []
                        activities = []
                        lapses_req = []
                        for lap in jsonData["lapses"]:
                            if lap == "Lapso 1":
                                lapses_req.append(1)
                            if lap == "Lapso 2":
                                lapses_req.append(2)
                            if lap == "Lapso 3":
                                lapses_req.append(3)

                        for i in lapses_req:
                            activities.append(
                                {"name": "Lapso "+str(i), "title": True, "lapse": i})
                            lapse = schoolYear.pecaSetting['lapse{}'.format(i)]

                            for activity in lapse.activities:
                                if activity.status == "1" and activity.isDeleted == False and activity.devName in jsonData["activities"]:
                                    activities.append(
                                        {"name": activity.name, "title": False, "lapse": i})
                        pecas = PecaProject.objects(isDeleted=False, schoolYear=schoolYear.id).only(
                            "id", "project", "lapse1", "lapse2", "lapse3")
                        schools = []
                        peca_active = []
                        for peca in pecas:
                            if peca.project.school:
                                schools.append(
                                    {"id": str(peca.project.school.id), "name": str(peca.project.school.name)})
                                peca_active.append(peca)
                        matriz = []
                        for i in range(0, len(activities)):
                            matriz.append(
                                {"activity": activities[i]["name"], "columns": []})
                            for j in range(0, len(schools)):
                                for acti in peca_active[j]["lapse{}".format(activities[i]["lapse"])].activities:
                                    if acti.name == activities[i]["name"]:
                                        matriz[i]["columns"].append(
                                            {"value": int(acti.percent)})
                                        break
                        return {"status_code": "201", "message": "Reporte", "rows": activities, "columns": schools, "matriz": matriz}, 201
        except Exception as e:
            
            return {"status_code": "500", "message": "Ha ocurrido un error"}, 201

    def remove_duplicates(self, list):
        id_clean = []
        list_clean = []
        for item in list:
            if not item["id"] in id_clean:
                id_clean.append(item["id"])
                list_clean.append(item)
        return list_clean
