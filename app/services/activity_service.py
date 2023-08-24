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
from app.helpers.handler_messages import HandlerMessages


class ActivityService():

    filesPath = 'activities'
    handlerMessages = HandlerMessages()

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
                dupActivity = schoolYear.pecaSetting['lapse{}'.format(lapse)].activities.filter(
                    isDeleted=False, devName=activity.devName).first()
                if dupActivity:
                    raise ValidationError(
                        {"name": [{"status": "5",
                                   "msg": "Duplicated record found"}]}
                    )
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
                                    id=c.id, name=c.name) for c in activity.checklist] if activity.checklist else [],
                                approvalType=activity.approvalType,
                                order=activity.order
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
                print(jsonData)
                data = schema.load(jsonData, partial=True)
                print(data)
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
                            activity.devName = re.sub(
                                r'[\W_]', '_', activity.name.strip().lower())
                            dupActivities = schoolYear.pecaSetting['lapse{}'.format(lapse)].activities.filter(
                                isDeleted=False, devName=activity.devName)
                            for dup in dupActivities:
                                if str(dup.id) != str(id):
                                    raise ValidationError(
                                        {"name": [{"status": "5",
                                                   "msg": "Duplicated record found"}]}
                                    )
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
                                        activity.description = newActivity.description
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
                                        activity.order = newActivity.order
                                        if oldActivity.checklist != None:
                                            oldCheckIds = [str(c.id)
                                                       for c in oldActivity.checklist]
                                        else:
                                            oldCheckIds = []
                                        newCheckIds = {}
                                        if newActivity.checklist:
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
                
                if newActivity:
                    return schema.dump(newActivity), 200
                return schema.dump(oldActivity), 200
                 
            except ValidationError as err:
                print(err)
                return err.normalized_messages(), 400

    def delete(self, lapse, id):
        """
        Delete (change isDeleted to False) a record
        """
        from app.models.peca_project_model import PecaProject
        from app.models.request_content_approval_model import RequestContentApproval

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()
                    
        if schoolYear:

            activities = schoolYear.pecaSetting['lapse{}'.format(
                lapse)].activities

            found = False
            for activity in activities:
                if str(activity.id) == str(id) and not activity.isDeleted:
                    found = True

                    # validate delete
                    entity = ''
                    contentRequest = RequestContentApproval.objects(
                        isDeleted=False, type="3", detail__id=id, status="1").first()
                    if contentRequest:
                        entity = 'RequestContentApproval'
                    if entity:
                        return {
                            'status': '0',
                            'entity': entity,
                            'msg': self.handlerMessages.getDeleteEntityMsg(entity)
                        }, 419

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
                        "order": initialWorkshop.order,
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
                        "order": ambleCoins.order,
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
                        "order": lapsePlanning.order,
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
                        "order": annualConvention.order,
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
                        "order": annualPreparation.order,
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
                        "order": mathOlympic.order,
                        "isStandard": True,
                        "status": mathOlympic.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))

                specialLapseActivity = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].specialLapseActivity
                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and specialLapseActivity.status == '1')
                ):

                    data = {
                        "id": "speciallapseactivity",
                        "name": "Actividad especial de lapso",
                        "devName": "specialLapseActivity",
                        "order": specialLapseActivity.order,
                        "isStandard": True,
                        "status": specialLapseActivity.status
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
                            "order": activity.order,
                            "isStandard": False,
                            "status": activity.status,
                            "hasText": activity.hasText,
                            "hasDate": activity.hasDate,
                            "hasFile": activity.hasFile,
                            "hasVideo": activity.hasVideo,
                            "hasChecklist": activity.hasChecklist,
                            "hasUpload": activity.hasUpload,
                            "approvalType": activity.approvalType,
                            "checklist": activity.checklist,
                            "text": activity.text,
                            "file": activity.file,
                            "video": activity.video
                        }
                        records['lapse{}'.format(
                            i+1)].append(schema.dump(data))
                records['lapse{}'.format(i+1)] = sorted(records['lapse{}'.format(i+1)], key=lambda d: d['order']) 
        
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
        from app.models.peca_special_lapse_activity_model import SpecialActivityPeca
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
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].initialWorkshop.order = data['order']
                        
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)
                        if data['status'] == "1":
                            initialWorkshop = InitialWorkshopPeca()
                            if "order" in data:        
                                initialWorkshop.order = data['order']
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
                        ambleCoinsStg = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].ambleCoins
                        ambleCoinsStg.status = data['status']
                        if "order" in data:        
                            ambleCoinsStg.order = data['order']

                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                ambleCoins = AmblecoinsPeca()
                                if "order" in data:        
                                    ambleCoins.order = data['order']
                                for section in peca.school.sections:
                                    ambleCoins.sections.append(
                                        AmbleSection(
                                            id=str(section.id),
                                            name=section.name,
                                            grade=section.grade,
                                            status="2"
                                        )
                                    )
                                    ambleCoins.teachersMeetingFile = ambleCoinsStg.teachersMeetingFile
                                    ambleCoins.teachersMeetingDescription = ambleCoinsStg.teachersMeetingDescription
                                    ambleCoins.piggyBankDescription = ambleCoinsStg.piggyBankDescription
                                    ambleCoins.piggyBankSlider = ambleCoinsStg.piggyBankSlider
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
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].lapsePlanning.order = data["order"]
                        
                        lapsePlanning = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].lapsePlanning
                        
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)
                        if data['status'] == "1":
                            lapsePlanningStg = schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].lapsePlanning
                            if "order" in data:        
                                lapsePlanningStg.order = data["order"]
                            lapsePlanning = LapsePlanningPeca(
                                proposalFundationFile=lapsePlanningStg.proposalFundationFile,
                                proposalFundationDescription=lapsePlanningStg.proposalFundationDescription,
                                meetingDescription=lapsePlanningStg.meetingDescription,
                                order=data["order"]
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
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].annualConvention.order = data['order']

                        annualConvention = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualConvention
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)
                        if data['status'] == "1":
                            pecaSettingLapse = schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])]
                            annualConvention = AnnualConventionPeca()
                            if "order" in data:        
                                annualConvention.order = data["order"]

                            for element in pecaSettingLapse.annualConvention.checklist:
                                annualConvention.checklist.append(
                                    CheckElement(
                                        id=str(element.id),
                                        name=element.name,
                                        checked=False
                                    ))
                            for i in ['1','2','3']:
                                if data['lapse'] != i:
                                    schoolYear.pecaSetting['lapse{}'.format(i)].annualConvention.status = '2'

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(
                                    data['lapse'])].annualConvention = annualConvention
                                for i in ['1','2','3']:
                                    if i != data['lapse']:
                                        peca['lapse{}'.format(
                                            i)].annualConvention = None

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
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].annualPreparation.order = data['order']
                        
                        annualPreparation = schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].annualPreparation
                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        if data['status'] == "1":
                            for i in ['1','2','3']:
                                if data['lapse'] != i:
                                    schoolYear.pecaSetting['lapse{}'.format(
                                        i)].annualPreparation.status = '2'

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                annualPreparation = AnnualPreparationPeca(
                                    step1Description=annualPreparation.step1Description,
                                    step2Description=annualPreparation.step2Description,
                                    step3Description=annualPreparation.step3Description,
                                    step4Description=annualPreparation.step4Description,
                                )
                                if "order" in data:        
                                    annualPreparation.order = data["order"]

                                peca['lapse{}'.format(
                                    data['lapse'])].annualPreparation = annualPreparation
                                for i in ['1','2','3']:
                                    if i != data['lapse']:
                                        peca['lapse{}'.format(
                                            i)].annualPreparation = None
                                
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
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].mathOlympic.order = data['order']

                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        #if data['status'] == "1":
                        #    for i in ['1','2','3']:
                        #        if data['lapse'] != i:
                        #            schoolYear.pecaSetting['lapse{}'.format(
                        #                i)].mathOlympic.status = '2'

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                olympics = Olympics(
                                    file=schoolYear.pecaSetting['lapse{}'.format(
                                        data['lapse'])].mathOlympic.file,
                                    description=schoolYear.pecaSetting['lapse{}'.format(
                                        data['lapse'])].mathOlympic.description,
                                    date=schoolYear.pecaSetting['lapse{}'.format(
                                        data['lapse'])].mathOlympic.date
                                )
                                if "order" in data:        
                                    olympics.order = data["order"]

                                peca['lapse{}'.format(
                                    data['lapse'])].olympics = olympics
                                if olympics.date:
                                    peca.scheduleActivity(
                                        devName="olympics__date",
                                        activityId="mathOlympic",
                                        subject="Olimpíadas matemáticas",
                                        startTime=olympics.date,
                                        description=olympics.description
                                    )
                                #for i in ['1','2','3']:
                                #    if i != data['lapse']:
                                #        peca['lapse{}'.format(
                                #            i)].olympics = None
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].olympics = None
                                peca.scheduleRemoveActivity('olympics__date')
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)
                    elif data['id'] == "specialLapseActivity":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].specialLapseActivity.status = data['status']
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].specialLapseActivity.order = data['order']

                        bulk_operations = []

                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False)

                        if data['status'] == "1":
                            specialActivity = SpecialActivityPeca()
                            if "order" in data:        
                                specialActivity.order = data["order"]
                            
                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(
                                    data['lapse'])].specialActivity = specialActivity
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].specialActivity = None

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
                                schoolYear=schoolYear.id, isDeleted=False).only("id", "lapse1", "lapse2", "lapse3")

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
                                            updatedAt=activity.updatedAt,
                                            order=activity.order
                                        )
                                    )
                                # is inactive
                                else:
                                    for act in peca['lapse{}'.format(data['lapse'])].activities:
                                        if act.id == str(activity.id):
                                            act.status = "2"
                                            #peca['lapse{}'.format(
                                            #    data['lapse'])].activities.remove(act)
                                peca.save()
                                #bulk_operations.append(
                                #    UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
                            #if bulk_operations:
                            #    PecaProject._get_collection() \
                            #        .bulk_write(bulk_operations, ordered=False)
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
