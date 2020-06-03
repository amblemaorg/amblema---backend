# app/services/activity_service.py


import re

from flask import current_app
from marshmallow import ValidationError
from pymongo import UpdateOne

from app.models.school_year_model import SchoolYear
from app.models.peca_setting_model import Activity
from app.schemas.peca_setting_schema import ActivitySchema
from app.schemas.activity_schema import ActivitySummarySchema, ActivityHandleStatus
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class ActivityService():

    filesPath = 'activities'

    def get(self, lapse, id):
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only("pecaSetting").first()

        if schoolYear:
            schema = ActivitySchema()
            activities = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].activities

            for activity in activities:
                if str(activity.id) == str(id) and not activity.isDeleted:
                    return schema.dump(activity), 200
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": id})

    def save(self, lapse, jsonData, files=None):
        from app.models.peca_project_model import PecaProject
        from app.models.peca_activities_model import ActivityPeca, CheckElement
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = ActivitySchema()
                documentFiles = getFileFields(Activity)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData)

                if not schoolYear.pecaSetting:
                    schoolYear.initFirstPecaSetting()

                activity = Activity()
                for field in schema.dump(data).keys():
                    activity[field] = data[field]
                activity.devName = re.sub(
                    r'[\W_]', '_', activity.name.strip().lower())
                try:

                    schoolYear.pecaSetting['lapse{}'.format(lapse)].activities.append(
                        activity)
                    schoolYear.save()

                    bulk_operations = []
                    for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                        peca['lapse{}'.format(lapse)].activities.append(
                            ActivityPeca(
                                id=str(activity.id),
                                name=activity.name,
                                devName=activity.devName,
                                hasText=activity.hasText,
                                hasDate=activity.hasDate,
                                hasFile=activity.hasFile,
                                hasVideo=activity.hasVideo,
                                hasChecklist=activity.hasChecklist,
                                hasUpload=activity.hasUpload,
                                text=activity.text,
                                file=activity.file,
                                video=activity.video,
                                checklist=[CheckElement(
                                    id=c.id, name=c.name) for c in activity.checklist],
                                approvalType=activity.approvalType
                            )
                        )
                        bulk_operations.append(
                            UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                    if bulk_operations:
                        PecaProject._get_collection() \
                            .bulk_write(bulk_operations, ordered=False)

                    return schema.dump(activity), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400

    def update(self, lapse, id, jsonData, files=None):
        from app.models.peca_project_model import PecaProject
        from app.models.peca_activities_model import ActivityPeca, CheckElement

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            try:
                schema = ActivitySchema()
                documentFiles = getFileFields(Activity)
                if files and documentFiles:
                    validFiles = validate_files(files, documentFiles)
                    uploadedfiles = upload_files(validFiles, self.filesPath)
                    jsonData.update(uploadedfiles)
                data = schema.load(jsonData, partial=True)

                activities = schoolYear.pecaSetting['lapse{}'.format(
                    lapse)].activities

                found = False
                hasChanged = False
                for activity in activities:
                    if str(activity.id) == str(id) and not activity.isDeleted:
                        oldActivity = activity
                        found = True
                        for field in schema.dump(data).keys():
                            if activity[field] != data[field]:
                                hasChanged = True
                                activity[field] = data[field]
                        if hasChanged:
                            newActivity = activity
                        break
                if not found:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"recordId": id})

                if hasChanged:
                    try:
                        schoolYear.pecaSetting['lapse{}'.format(
                            lapse)].activities = activities
                        schoolYear.save()

                        if newActivity.status == "1":
                            bulk_operations = []
                            for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                                for activity in peca['lapse{}'.format(lapse)].activities:
                                    if str(activity.id) == id:
                                        activity.name = newActivity.name
                                        activity.devName = newActivity.devName
                                        activity.hasText = newActivity.hasText
                                        activity.hasDate = newActivity.hasDate
                                        activity.hasFile = newActivity.hasFile
                                        activity.hasVideo = newActivity.hasVideo
                                        activity.hasChecklist = newActivity.hasChecklist
                                        activity.hasUpload = newActivity.hasUpload
                                        activity.text = newActivity.text
                                        activity.file = newActivity.file
                                        activity.video = newActivity.video

                                        oldCheckIds = [str(c.id)
                                                       for c in oldActivity.checklist]
                                        newCheckIds = {}
                                        for c in newActivity.checklist:
                                            newCheckIds[str(c.id)] = c
                                        if activity.hasChecklist and oldActivity.checklist != newActivity.checklist:
                                            for c in activity.checklist:
                                                if str(c.id) not in newCheckIds:
                                                    activity.checklist.remove(
                                                        c)
                                            for k in newCheckIds.keys():
                                                if k not in oldCheckIds:
                                                    activity.checklist.append(
                                                        CheckElement(
                                                            id=newCheckIds[k].id, name=newCheckIds[k].name)
                                                    )
                                bulk_operations.append(
                                    UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                            if bulk_operations:
                                PecaProject._get_collection().bulk_write(bulk_operations, ordered=False)
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

                return schema.dump(activity), 200

            except ValidationError as err:
                return err.normalized_messages(), 400

    def delete(self, lapse, id):
        """
        Delete (change isDeleted to False) a record
        """
        from app.models.peca_project_model import PecaProject

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:

            activities = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].activities

            found = False
            for activity in activities:
                if str(activity.id) == str(id) and not activity.isDeleted:
                    found = True
                    try:
                        activity.isDeleted = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            lapse)].activities = activities
                        schoolYear.save()
                        bulk_operations = []
                        for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False):
                            for activity in peca['lapse{}'.format(lapse)].activities:
                                if str(activity.id) == id:
                                    peca['lapse{}'.format(lapse)].activities.remove(
                                        activity)
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection().bulk_write(bulk_operations, ordered=False)
                        return {"message": "Record deleted successfully"}, 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

            if not found:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"recordId": id})

    def getSumary(self, filters=()):

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            records = {
                'lapse1': [],
                'lapse2': [],
                'lapse3': []
            }
            schema = ActivitySummarySchema()
            for i in range(3):

                initialWorkshop = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].initialWorkshop
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and initialWorkshop.status == '1')
                ):
                    data = {
                        "id": 'initialWorkshop',
                        "name": "Taller inicial",
                        "devName": "initialWorkshop",
                        "isStandard": True,
                        "status": initialWorkshop.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                ambleCoins = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].ambleCoins
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and ambleCoins.status == '1')
                ):

                    data = {
                        "id": "amblecoins",
                        "name": "AmbLeMonedas",
                        "devName": "ambleCoins",
                        "isStandard": True,
                        "status": ambleCoins.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                lapsePlanning = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].lapsePlanning
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and lapsePlanning.status == '1')
                ):
                    data = {
                        "id": "lapseplanning",
                        "name": "Planificación de lapso",
                        "devName": "lapsePlanning",
                        "isStandard": True,
                        "status": lapsePlanning.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].annualConvention

                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and annualConvention.status == '1')
                ):

                    data = {
                        "id": "annualconvention",
                        "name": "Convención anual",
                        "devName": "annualConvention",
                        "isStandard": True,
                        "status": annualConvention.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                annualPreparation = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].annualPreparation

                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and annualPreparation.status == '1')
                ):

                    data = {
                        "id": "annualpreparation",
                        "name": "Preparación anual",
                        "devName": "annualPreparation",
                        "isStandard": True,
                        "status": annualPreparation.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                mathOlympic = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].mathOlympic

                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and mathOlympic.status == '1')
                ):

                    data = {
                        "id": "matholympic",
                        "name": "Olimpíadas matemáticas",
                        "devName": "mathOlympic",
                        "isStandard": True,
                        "status": mathOlympic.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                for activity in schoolYear.pecaSetting['lapse{}'.format(i+1)].activities:
                    if (
                        not activity.isDeleted and (
                            (not filters) or
                            ('status' in filters and filters['status']
                                == '1' and activity.status == '1')
                        )
                    ):
                        data = {
                            "id": str(activity.id),
                            "name": activity.name,
                            "devName": activity.devName,
                            "isStandard": False,
                            "status": activity.status
                        }
                        records['lapse{}'.format(
                            i+1)].append(schema.dump(data))
            return records, 200

        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404
                                   )

    def handleEnable(self, jsonData):
        """
        Update status active/inactive of activities per lapse
        Params:
          id: devName in case of standard. id in case of not standard
          jsonData:
              lapse: 1,2,3
              isStandard: boolean
              status: 1=active 2=inactive
        """
        from app.models.peca_project_model import PecaProject, AmblecoinsPeca, Olympics
        from app.models.peca_amblecoins_model import AmbleSection
        from app.models.peca_annual_preparation_model import AnnualPreparationPeca
        from app.models.peca_annual_convention_model import AnnualConventionPeca, CheckElement
        from app.models.peca_lapse_planning_model import LapsePlanningPeca
        from app.models.peca_initial_workshop_model import InitialWorkshopPeca
        from pymongo import UpdateOne

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            schema = ActivityHandleStatus()
            try:
                data = schema.load(jsonData)
                found = False
                if data['isStandard']:
                    if data['id'] == "initialWorkshop":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].initialWorkshop.status = data['status']
                        initialWorkshop = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].initialWorkshop
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)
                        if data['status'] == "1":
                            initialWorkshopStg = schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].initialWorkshop
                            initialWorkshop = InitialWorkshopPeca(
                                agreementFile=initialWorkshopStg.agreementFile,
                                agreementDescription=initialWorkshopStg.agreementDescription,
                                planningMeetingFile=initialWorkshopStg.planningMeetingFile,
                                planningMeetingDescription=initialWorkshopStg.planningMeetingDescription,
                                teachersMeetingFile=initialWorkshopStg.teachersMeetingFile,
                                teachersMeetingDescription=initialWorkshopStg.teachersMeetingDescription
                            )

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(
                                    data['lapse'])].initialWorkshop = initialWorkshop
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].initialWorkshop = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    elif data['id'] == "ambleCoins":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].ambleCoins.status = data['status']
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                ambleCoins = AmblecoinsPeca()
                                for section in peca.school.sections:
                                    ambleCoins.sections.append(
                                        AmbleSection(
                                            id=str(section.id),
                                            name=section.name,
                                            grade=section.grade,
                                            status="2"
                                        )
                                    )
                                peca['lapse{}'.format(
                                    data['lapse'])].ambleCoins = ambleCoins
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].ambleCoins = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    elif data['id'] == "lapsePlanning":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].lapsePlanning.status = data['status']

                        lapsePlanning = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].lapsePlanning
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)
                        if data['status'] == "1":
                            lapsePlanningStg = schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].lapsePlanning
                            lapsePlanning = LapsePlanningPeca(
                                proposalFundationFile=lapsePlanningStg.proposalFundationFile,
                                proposalFundationDescription=lapsePlanningStg.proposalFundationDescription,
                                meetingDescription=lapsePlanningStg.meetingDescription
                            )

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(
                                    data['lapse'])].lapsePlanning = lapsePlanning
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].lapsePlanning = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    elif data['id'] == "annualConvention":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualConvention.status = data['status']

                        annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualConvention
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)
                        if data['status'] == "1":
                            pecaSettingLapse = schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])]
                            annualConvention = AnnualConventionPeca()
                            for element in pecaSettingLapse.annualConvention.checklist:
                                annualConvention.checklist.append(
                                    CheckElement(
                                        id=str(element.id),
                                        name=element.name,
                                        checked=False
                                    ))
                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(
                                    data['lapse'])].annualConvention = annualConvention
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].annualConvention = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    elif data['id'] == "annualPreparation":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualPreparation.status = data['status']
                        annualPreparation = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualPreparation
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                annualPreparation = AnnualPreparationPeca(
                                    step1Description=annualPreparation.step1Description,
                                    step2Description=annualPreparation.step2Description,
                                    step3Description=annualPreparation.step3Description,
                                    step4Description=annualPreparation.step4Description,
                                )
                                peca['lapse{}'.format(
                                    data['lapse'])].annualPreparation = annualPreparation
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].annualPreparation = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    elif data['id'] == "mathOlympic":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].mathOlympic.status = data['status']

                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                olympics = Olympics(
                                    file=schoolYear.pecaSetting['lapse{}'.format(
                                        data['lapse'])].mathOlympic.file,
                                    description=schoolYear.pecaSetting['lapse{}'.format(
                                        data['lapse'])].mathOlympic.description
                                )
                                peca['lapse{}'.format(
                                    data['lapse'])].olympics = olympics
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].olympics = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                else:
                    from app.models.peca_activities_model import ActivityPeca, CheckElement
                    for activity in schoolYear.pecaSetting['lapse{}'.format(data['lapse'])].activities:
                        if str(activity.id) == data['id']:
                            found = True
                            activity.status = data['status']
                            bulk_operations = []
                            pecaProjects = PecaProject.objects(
                                schoolYear=schoolYear.id, isDeleted=False)

                            for peca in pecaProjects:
                                # is active
                                if data['status'] == "1":
                                    peca['lapse{}'.format(data['lapse'])].activities.append(
                                        ActivityPeca(
                                            id=str(activity.id),
                                            name=activity.name,
                                            devName=activity.devName,
                                            hasText=activity.hasText,
                                            hasDate=activity.hasDate,
                                            hasFile=activity.hasFile,
                                            hasVideo=activity.hasVideo,
                                            hasChecklist=activity.hasChecklist,
                                            hasUpload=activity.hasUpload,
                                            text=activity.text,
                                            file=activity.file,
                                            video=activity.video,
                                            checklist=None if not activity.hasChecklist else [CheckElement(
                                                id=chk.id, name=chk.name) for chk in activity.checklist],
                                            approvalType=activity.approvalType,
                                            isStandard=activity.isStandard,
                                            status=activity.status,
                                            createdAt=activity.createdAt,
                                            updatedAt=activity.updatedAt
                                        )
                                    )
                                # is inactive
                                else:
                                    for act in peca['lapse{}'.format(data['lapse'])].activities:
                                        if act.id == str(activity.id):
                                            peca['lapse{}'.format(
                                                data['lapse'])].activities.remove(act)
                                bulk_operations.append(
                                    UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                            if bulk_operations:
                                PecaProject._get_collection() \
                                    .bulk_write(bulk_operations, ordered=False)
                            break
                if found:
                    schoolYear.save()
                    schoolYear = SchoolYear.objects.get(id=schoolYear.id)
                    return {"msg": "Record updated"}, 200
                else:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"recordId": data['id']})

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Active school year not found",
                                   status_code=404)
