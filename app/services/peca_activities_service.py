# -*- coding: utf-8 -*-
# app/services/peca_activities_service.py

import copy
import datetime
from bson import ObjectId

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
                            # Si la peticion no trae checklist (p. ej. solo status) se usa el guardado
                            checklist = data["checklist"] if "checklist" in data else activity.checklist
                            percent = 0
                            for act in checklist:
                                if act["checked"]:
                                    percent = percent + 1
                            if percent > 0:
                                percent = (
                                    percent/len(checklist))*100
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
    LAPSE_NUMBERS = {"Lapso 1": 1, "Lapso 2": 2, "Lapso 3": 3}

    # type_filter -> (clave del body con los ids, filtro de PecaProject, mensaje si viene vacío)
    FILTERS = {
        "schoolYear": (None, None, None),
        "coordinator": ("coordinators", "project__coordinator__id__in",
                        "Debe enviar por lo menos un coordinador"),
        "school": ("schools", "project__school__id__in",
                   "Debe enviar por lo menos una escuela"),
        "activity": ("activities", None,
                     "Debe enviar por lo menos una actividad"),
    }

    def _settingActivities(self, schoolYear, lapse):
        """Actividades activas del pecaSetting del año escolar para un lapso (1..3)."""
        if not schoolYear.pecaSetting:
            return []
        lapseSetting = schoolYear.pecaSetting['lapse{}'.format(lapse)]
        if not lapseSetting:
            return []
        return [a for a in lapseSetting.activities
                if a.status == "1" and not a.isDeleted]

    def getDataInicial(self):
        schoolYears = SchoolYear.objects(isDeleted=False).only(
            "id", "name", "status", "pecaSetting")
        if not schoolYears:
            return {"status_code": "404", "message": "No hay año escolar activo"}, 200

        # Una sola consulta (sin instanciar documentos) para los PECA de todos los años
        pecasBySchoolYear = {}
        pecas = PecaProject.objects(isDeleted=False).only(
            "schoolYear", "project.coordinator", "project.sponsor",
            "project.school").as_pymongo()
        for peca in pecas:
            pecasBySchoolYear.setdefault(
                str(peca.get("schoolYear")), []).append(peca.get("project") or {})

        data = {"schoolYears": []}
        for schoolYear in schoolYears:
            dataSchoolYear = {"name": schoolYear.name, "status": schoolYear.status,
                              "id": str(schoolYear.id), "lapses": [],
                              "coordinators": [], "sponsors": [], "schools": []}
            for i in range(1, 4):
                dataSchoolYear["lapses"].append({
                    "name": "Lapso " + str(i),
                    "activities": [{"name": a.name, "devName": a.devName, "isStandard": a.isStandard}
                                   for a in self._settingActivities(schoolYear, i)]})

            for project in pecasBySchoolYear.get(str(schoolYear.id), []):
                for key, target in (("coordinator", "coordinators"), ("sponsor", "sponsors"),
                                    ("school", "schools")):
                    ref = project.get(key)
                    if ref and ref.get("id"):
                        dataSchoolYear[target].append(
                            {"id": str(ref["id"]), "name": ref.get("name") or ""})
            for target in ("coordinators", "sponsors", "schools"):
                dataSchoolYear[target] = self.remove_duplicates(dataSchoolYear[target])
            data["schoolYears"].append(dataSchoolYear)

        return {"status_code": "200", "message": "Actividades", "data": data}, 200

    def generateReport(self, jsonData):
        try:
            return self._generateReport(jsonData or {})
        except Exception:
            current_app.logger.exception("Error generando el reporte de actividades PECA")
            return {"status_code": "500", "message": "Ha ocurrido un error al generar el reporte"}, 500

    def _generateReport(self, jsonData):
        typeFilter = jsonData.get("type_filter")
        if typeFilter not in self.FILTERS:
            return {"status_code": "400", "message": "Tipo de filtro no válido"}, 400
        bodyKey, pecaLookup, emptyMessage = self.FILTERS[typeFilter]

        schoolYearId = jsonData.get("schoolYear")
        if not schoolYearId:
            return {"status_code": "400", "message": "Debe enviar un año escolar"}, 400
        schoolYear = None
        if ObjectId.is_valid(str(schoolYearId)):
            schoolYear = SchoolYear.objects(isDeleted=False, id=schoolYearId).only(
                "id", "pecaSetting").first()
        if not schoolYear:
            return {"status_code": "404", "message": "El año escolar no es válido"}, 404

        lapses = sorted(set(self.LAPSE_NUMBERS[name] for name in (jsonData.get("lapses") or [])
                            if name in self.LAPSE_NUMBERS))
        if not lapses:
            return {"status_code": "400", "message": "Debe enviar por lo menos un lapso"}, 400

        selected = []
        if bodyKey:
            selected = [str(value) for value in (jsonData.get(bodyKey) or [])]
            if not selected:
                return {"status_code": "400", "message": emptyMessage}, 400
        activityFilter = set(selected) if typeFilter == "activity" else None

        # Filas: encabezado por lapso + sus actividades. Con filtro de actividades se omiten
        # los lapsos que no tienen ninguna de las elegidas.
        rows = []
        for lapse in lapses:
            activities = [a for a in self._settingActivities(schoolYear, lapse)
                          if activityFilter is None or a.devName in activityFilter]
            if activityFilter is not None and not activities:
                continue
            rows.append({"name": "Lapso " + str(lapse), "title": True, "lapse": lapse})
            for activity in activities:
                rows.append({"name": activity.name, "devName": activity.devName,
                             "title": False, "lapse": lapse})

        query = {"isDeleted": False, "schoolYear": schoolYear.id}
        if pecaLookup:
            query[pecaLookup] = selected
        pecas = PecaProject.objects(**query).only(
            "id", "project.coordinator", "project.school",
            "lapse1.activities.devName", "lapse1.activities.percent",
            "lapse2.activities.devName", "lapse2.activities.percent",
            "lapse3.activities.devName", "lapse3.activities.percent").as_pymongo()

        # Columnas: un PECA por columna, identificado por el id del PECA (único aunque
        # se repita el nombre de la escuela o el coordinador tenga varias escuelas)
        columns = []
        percents = []
        for peca in pecas:
            project = peca.get("project") or {}
            school = project.get("school") or {}
            if not school.get("id"):
                continue
            name = school.get("name") or ""
            if typeFilter == "coordinator":
                coordinator = project.get("coordinator") or {}
                name = (coordinator.get("name") or "") + " - " + name
            columns.append({"id": str(peca["_id"]), "name": name})

            pecaPercents = {}
            for lapse in lapses:
                for activity in ((peca.get("lapse{}".format(lapse)) or {}).get("activities") or []):
                    pecaPercents[(lapse, activity.get("devName"))] = activity.get("percent")
            percents.append(pecaPercents)

        order = sorted(range(len(columns)), key=lambda idx: columns[idx]["name"].lower())
        columns = [columns[idx] for idx in order]
        percents = [percents[idx] for idx in order]

        # Siempre una celda por columna: None = el PECA no tiene la actividad (no aplica)
        matriz = []
        for row in rows:
            cells = []
            for pecaPercents in percents:
                value = None
                key = (row["lapse"], row.get("devName"))
                if not row["title"] and key in pecaPercents:
                    value = self._formatPercent(pecaPercents[key])
                cells.append({"value": value})
            matriz.append({"activity": row["name"], "title": row["title"], "columns": cells})

        return {"status_code": "201", "message": "Reporte", "rows": rows,
                "columns": columns, "matriz": matriz}, 201

    def _formatPercent(self, percent):
        """Porcentaje con un decimal (sin truncar 99.9 a 99); vacío en BD cuenta como 0."""
        value = round(float(percent or 0), 1)
        return int(value) if value == int(value) else value

    def remove_duplicates(self, list):
        id_clean = []
        list_clean = []
        for item in list:
            if not item["id"] in id_clean:
                id_clean.append(item["id"])
                list_clean.append(item)
        return list_clean
