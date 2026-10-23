# app/services/activity_service.py


import re, copy

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
                    activity_peca = ActivityPeca(
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
                    activity_peca_dict = activity_peca.to_mongo().to_dict()
                    for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only('id'):
                        bulk_operations.append(
                            UpdateOne({'_id': peca.id}, {'$push': {'lapse{}.activities'.format(lapse): activity_peca_dict}}))
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
                        oldActivity = copy.deepcopy(activity)
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
                            for peca in PecaProject.objects(schoolYear=schoolYear.id, isDeleted=False).only('lapse1', 'lapse2', 'lapse3'):
                                for i, activity in enumerate(peca['lapse{}'.format(lapse)].activities):
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
                                        newCheckIds_id = []
                                        
                                        if newActivity.checklist:
                                            for c in newActivity.checklist:
                                                newCheckIds[str(c.id)] = c
                                                newCheckIds_id.append(str(c.id))
                                        
                                        if activity.hasChecklist and oldActivity.checklist != newActivity.checklist:
                                            activity_copy = copy.deepcopy(activity)
                                            for c in activity.checklist:
                                                if str(c.id) not in newCheckIds_id:
                                                    activity_copy.checklist.remove(
                                                        c)
                                            activity.checklist = activity_copy.checklist
                                            for k in newCheckIds.keys():
                                                if k not in oldCheckIds:
                                                    activity.checklist.append(
                                                        CheckElement(
                                                            id=newCheckIds[k].id, name=newCheckIds[k].name)
                                                    )
                                        set_query = {
                                            'lapse{}.activities.{}'.format(lapse, i): activity.to_mongo().to_dict()
                                        }
                                        bulk_operations.append(
                                            UpdateOne({'_id': peca.id}, {'$set': set_query}))
                                        break
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
                        # One update_many instead of reading ids + one op per PECA; also drop the
                        # activity's date from the PECA schedule so it doesn't stay orphaned
                        PecaProject._get_collection().update_many(
                            {'schoolYear': schoolYear.id, 'isDeleted': False},
                            {'$pull': {
                                'lapse{}.activities'.format(lapse): {'id': id},
                                'schedule': {'devName': 'activities__{}'.format(id)}
                            }})
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
                        "name": "Olimpíada Recreativas de Matemática",
                        "devName": "mathOlympic",
                        "order": mathOlympic.order,
                        "isStandard": True,
                        "status": mathOlympic.status
                    }
                    records['lapse{}'.format(i+1)].append(schema.dump(data))
                
                readingOlympics = schoolYear.pecaSetting['lapse{}'.format(
                    i+1)].readingOlympics

                if (
                    (not filters) or
                    ('status' in filters and filters['status']
                     == '1' and readingOlympics.status == '1')
                ):

                    data = {
                        "id": "readingolympics",
                        "name": "Olimpíada Recreativas de Lengua",
                        "devName": "readingolympics",
                        "order": readingOlympics.order,
                        "isStandard": True,
                        "status": readingOlympics.status
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

    @staticmethod
    def peca_set(peca, *paths):
        """$set only the given paths (e.g. 'lapse2.ambleCoins', 'schedule').
        PECAs are loaded partially, so a full-document $set would overwrite the fields
        not loaded with their defaults (e.g. an empty yearbook) in every PECA of the year.
        """
        update = {}
        for path in paths:
            owner = peca
            keys = path.split('.')
            for key in keys[:-1]:
                owner = owner[key]
            value = owner[keys[-1]]
            update[path] = owner._fields[keys[-1]].to_mongo(value) if value is not None else None
        return {'$set': update}

    @staticmethod
    def new_amble_coins(peca, ambleCoinsStg, data):
        from app.models.peca_amblecoins_model import AmblecoinsPeca, AmbleSection
        from app.models.peca_project_model import PecaProject
        ambleCoins = AmblecoinsPeca()
        if "order" in data:
            ambleCoins.order = data['order']
        # handleEnable loads PECAs without 'school' (heavy); read the sections only when needed
        school = PecaProject.objects(id=peca.id).only('school.sections').first().school
        for section in school.sections:
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
        return ambleCoins

    @staticmethod
    def keep_or_create(current, data, create):
        """Activation/reorder must not wipe what the school already loaded:
        reuse the existing activity and only update its order
        """
        if current is not None:
            if "order" in data:
                current.order = data['order']
            return current
        activity = create()
        if "order" in data:
            activity.order = data['order']
        return activity

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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')
                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(data['lapse'])].initialWorkshop = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].initialWorkshop, data, InitialWorkshopPeca)
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].initialWorkshop = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.initialWorkshop'.format(data['lapse']))))
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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                ambleCoins = peca['lapse{}'.format(data['lapse'])].ambleCoins
                                if ambleCoins is not None:
                                    if "order" in data:
                                        ambleCoins.order = data['order']
                                else:
                                    ambleCoins = self.new_amble_coins(peca, ambleCoinsStg, data)
                                peca['lapse{}'.format(
                                    data['lapse'])].ambleCoins = ambleCoins
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].ambleCoins = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.ambleCoins'.format(data['lapse']))))
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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')
                        lapsePlanningStg = lapsePlanning
                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(data['lapse'])].lapsePlanning = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].lapsePlanning, data,
                                    lambda: LapsePlanningPeca(
                                        proposalFundationFile=lapsePlanningStg.proposalFundationFile,
                                        proposalFundationDescription=lapsePlanningStg.proposalFundationDescription,
                                        meetingDescription=lapsePlanningStg.meetingDescription,
                                    ))
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].lapsePlanning = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.lapsePlanning'.format(data['lapse']))))
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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')
                        if data['status'] == "1":
                            pecaSettingLapse = schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])]
                            def newAnnualConvention():
                                convention = AnnualConventionPeca()
                                for element in pecaSettingLapse.annualConvention.checklist:
                                    convention.checklist.append(
                                        CheckElement(
                                            id=str(element.id),
                                            name=element.name,
                                            checked=False
                                        ))
                                return convention
                            for i in ['1','2','3']:
                                if data['lapse'] != i:
                                    schoolYear.pecaSetting['lapse{}'.format(i)].annualConvention.status = '2'

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(data['lapse'])].annualConvention = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].annualConvention, data, newAnnualConvention)
                                for i in ['1','2','3']:
                                    if i != data['lapse']:
                                        peca['lapse{}'.format(
                                            i)].annualConvention = None

                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].annualConvention = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, *['lapse{}.annualConvention'.format(i) for i in ('1', '2', '3')])))
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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')

                        if data['status'] == "1":
                            for i in ['1','2','3']:
                                if data['lapse'] != i:
                                    schoolYear.pecaSetting['lapse{}'.format(
                                        i)].annualPreparation.status = '2'

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                annualPreparationStg = annualPreparation
                                peca['lapse{}'.format(data['lapse'])].annualPreparation = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].annualPreparation, data,
                                    lambda: AnnualPreparationPeca(
                                        step1Description=annualPreparationStg.step1Description,
                                        step2Description=annualPreparationStg.step2Description,
                                        step3Description=annualPreparationStg.step3Description,
                                        step4Description=annualPreparationStg.step4Description,
                                    ))
                                for i in ['1','2','3']:
                                    if i != data['lapse']:
                                        peca['lapse{}'.format(
                                            i)].annualPreparation = None
                                
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].annualPreparation = None
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, *['lapse{}.annualPreparation'.format(i) for i in ('1', '2', '3')])))
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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')

                        #if data['status'] == "1":
                        #    for i in ['1','2','3']:
                        #        if data['lapse'] != i:
                        #            schoolYear.pecaSetting['lapse{}'.format(
                        #                i)].mathOlympic.status = '2'

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                isNew = peca['lapse{}'.format(data['lapse'])].olympics is None
                                olympics = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].olympics, data,
                                    lambda: Olympics(
                                        file=schoolYear.pecaSetting['lapse{}'.format(
                                            data['lapse'])].mathOlympic.file,
                                        description=schoolYear.pecaSetting['lapse{}'.format(
                                            data['lapse'])].mathOlympic.description,
                                        date=schoolYear.pecaSetting['lapse{}'.format(
                                            data['lapse'])].mathOlympic.date
                                    ))
                                peca['lapse{}'.format(
                                    data['lapse'])].olympics = olympics
                                if isNew and olympics.date:
                                    peca.scheduleActivity(
                                        devName="olympics__date",
                                        activityId="mathOlympic",
                                        subject="Olimpíada Recreativas de Matemática",
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
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.olympics'.format(data['lapse']), 'schedule')))
                        if bulk_operations:
                            PecaProject._get_collection() \
                                .bulk_write(bulk_operations, ordered=False)

                    elif data['id'] == "readingolympics":
                        found = True
                        schoolYear.pecaSetting['lapse{}'.format(
                            data['lapse'])].readingOlympics.status = data['status']
                        if "order" in data:        
                            schoolYear.pecaSetting['lapse{}'.format(
                                data['lapse'])].readingOlympics.order = data['order']

                        bulk_operations = []
                        pecaProjects = PecaProject.objects(
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                isNew = peca['lapse{}'.format(data['lapse'])].readingOlympics is None
                                olympics = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].readingOlympics, data,
                                    lambda: Olympics(
                                        file=schoolYear.pecaSetting['lapse{}'.format(
                                            data['lapse'])].readingOlympics.file,
                                        description=schoolYear.pecaSetting['lapse{}'.format(
                                            data['lapse'])].readingOlympics.description,
                                        date=schoolYear.pecaSetting['lapse{}'.format(
                                            data['lapse'])].readingOlympics.date
                                    ))
                                peca['lapse{}'.format(
                                    data['lapse'])].readingOlympics = olympics
                                if isNew and olympics.date:
                                    peca.scheduleActivity(
                                        devName="readingOlympics__date",
                                        activityId="readingolympics",
                                        subject="Olimpíada Recreativas de Lengua",
                                        startTime=olympics.date,
                                        description=olympics.description
                                    )
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].readingOlympics = None
                                peca.scheduleRemoveActivity('readingOlympics__date')
                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.readingOlympics'.format(data['lapse']), 'schedule')))
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
                            schoolYear=schoolYear.id, isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'schedule')

                        for peca in pecaProjects:
                            # is active
                            if data['status'] == "1":
                                peca['lapse{}'.format(data['lapse'])].specialActivity = self.keep_or_create(
                                    peca['lapse{}'.format(data['lapse'])].specialActivity, data, SpecialActivityPeca)
                            # is inactive
                            else:
                                peca['lapse{}'.format(
                                    data['lapse'])].specialActivity = None

                            bulk_operations.append(
                                UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.specialActivity'.format(data['lapse']))))

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
                                # Deactivation only sets status "2", so reactivating must reuse that
                                # entry (keeping what the school loaded) instead of appending a duplicate
                                existing = next((act for act in peca['lapse{}'.format(data['lapse'])].activities
                                                 if act.id == str(activity.id)), None)
                                # is active
                                if data['status'] == "1" and existing is not None:
                                    existing.status = "1"
                                    existing.order = activity.order
                                elif data['status'] == "1":
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
                                bulk_operations.append(
                                    UpdateOne({'_id': peca.id}, self.peca_set(peca, 'lapse{}.activities'.format(data['lapse']))))
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