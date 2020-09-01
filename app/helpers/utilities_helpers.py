

def refresh_projects():
    from app.models.project_model import Project
    from app.models.peca_project_model import PecaProject
    from app.models.shared_embedded_documents import ResumeSchoolYear, ResumePeca
    from pymongo import UpdateOne
    from flask import current_app

    projects = Project.objects(isDeleted=False)
    projectsIds = {}
    for project in projects:
        project.schoolYears = []
        projectsIds[str(project.id)] = project
    pecas = PecaProject.objects(isDeleted=False, project__id__in=projectsIds.keys())
    for peca in pecas:
        schoolYear = peca.schoolYear.fetch()
        resumePeriod = ResumeSchoolYear(
            id=str(schoolYear.id),
            name=schoolYear.name,
            status=schoolYear.status
        )
        resumePeca = ResumePeca(
            pecaId=str(peca.id),
            schoolYear = resumePeriod,
            createdAt = peca.createdAt
        )
        projectsIds[peca.project.id].schoolYears.append(resumePeca)
    
    bulk_operations = []
    for project in projectsIds.values():
        bulk_operations.append(
            UpdateOne({'_id': project.id}, {'$set': project.to_mongo().to_dict()}))
    
    if bulk_operations:
        Project._get_collection() \
            .bulk_write(bulk_operations, ordered=False)

def refresh_users_projects():
    from app.models.project_model import Project
    from app.models.school_user_model import SchoolUser
    from app.models.sponsor_user_model import SponsorUser
    from app.models.coordinator_user_model import CoordinatorUser
    from pymongo import UpdateOne
    from flask import current_app

    schools = SchoolUser.objects(isDeleted=False)
    sponsors = SponsorUser.objects(isDeleted=False)
    coordinators = CoordinatorUser.objects(isDeleted=False)

    bulk_operations = []
    for school in schools:
        school.project = {}
        bulk_operations.append(
            UpdateOne({'_id': school.id}, {'$set': school.to_mongo().to_dict()}))
    if bulk_operations:
        SchoolUser._get_collection() \
            .bulk_write(bulk_operations, ordered=False)
    
    bulk_operations = []
    for sponsor in sponsors:
        sponsor.projects = []
        bulk_operations.append(
            UpdateOne({'_id': sponsor.id}, {'$set': sponsor.to_mongo().to_dict()}))
    if bulk_operations:
        SponsorUser._get_collection() \
            .bulk_write(bulk_operations, ordered=False)
    
    bulk_operations = []
    for coordinator in coordinators:
        coordinator.projects = []
        bulk_operations.append(
            UpdateOne({'_id': coordinator.id}, {'$set': coordinator.to_mongo().to_dict()}))
    if bulk_operations:
        CoordinatorUser._get_collection() \
            .bulk_write(bulk_operations, ordered=False)

    schoolBulk = []
    sponsorBulk = []
    sponsorDict = {}
    coordinatorBulk = []
    coordinatorDict = {}

    for project in Project.objects(isDeleted=False):
        if project.school:
            project.school.project = project.getReference()
            schoolBulk.append(
                UpdateOne({'_id': project.school.id}, {'$set': project.school.to_mongo().to_dict()}))
        if project.sponsor:
            if project.sponsor.id not in sponsorDict:
                project.sponsor.projects.append(project.getReference())
                sponsorDict[project.sponsor.id] = project.sponsor
            else:
                sponsorDict[project.sponsor.id].projects.append(project.getReference())
        if project.coordinator:
            if project.coordinator.id not in coordinatorDict:
                project.coordinator.projects.append(project.getReference())
                coordinatorDict[project.coordinator.id] = project.coordinator
            else:
                coordinatorDict[project.coordinator.id].projects.append(project.getReference())

    for sponsor in sponsorDict.values():
        sponsorBulk.append(
            UpdateOne({'_id': sponsor.id}, {'$set': sponsor.to_mongo().to_dict()}))
    for coordinator in coordinatorDict.values():
        coordinatorBulk.append(
                UpdateOne({'_id': coordinator.id}, {'$set': coordinator.to_mongo().to_dict()}))
    
    if schoolBulk:
        SchoolUser._get_collection() \
            .bulk_write(schoolBulk, ordered=False)
    if sponsorBulk:
        SponsorUser._get_collection() \
            .bulk_write(sponsorBulk, ordered=False)
    if coordinatorBulk:
        CoordinatorUser._get_collection() \
            .bulk_write(coordinatorBulk, ordered=False)

def refresh_home_statistics():
    from app.blueprints.web_content.models.web_content import WebContent
    from app.models.school_user_model import SchoolUser
    from app.models.peca_project_model import PecaProject
    from app.models.school_year_model import SchoolYear
    from pymongo import UpdateOne
    from flask import current_app

    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    if schoolYear:
        schoolsIds = {}
        sponsorsIds = {}
        coordinatorsIds = {}
        pecas = PecaProject.objects(isDeleted=False, schoolYear=schoolYear.id)
        for peca in pecas:
            schoolsIds[peca.project.school.id] = peca
            sponsorsIds[peca.project.sponsor.id] = peca
            coordinatorsIds[peca.project.coordinator.id] = peca
        schools = SchoolUser.objects(isDeleted=False, pk__in=schoolsIds.keys()).all()

        nStudents = 0
        nTeachers = 0
        bulk_operations = []
        bulk_peca_operations = []

        for school in schools:
            peca = schoolsIds[str(school.id)]
            schoolStudents = 0
            for section in peca.school.sections.filter(isDeleted=False):
                schoolStudents += len(section.students.filter(isDeleted=False))
                section.refreshDiagnosticsSummary()
            peca.school.refreshDiagnosticsSummary()
            school.nStudents = schoolStudents
            nStudents += schoolStudents
            school.nTeachers = len(school.teachers.filter(isDeleted=False))
            nTeachers += school.nTeachers
            bulk_operations.append(
                UpdateOne({'_id': school.id}, {'$set': school.to_mongo().to_dict()}))
            bulk_peca_operations.append(
                UpdateOne({'_id': peca.id}, {'$set': peca.to_mongo().to_dict()}))
        
        if bulk_operations:
            SchoolUser._get_collection() \
                .bulk_write(bulk_operations, ordered=False)
        if bulk_peca_operations:
            PecaProject._get_collection() \
                .bulk_write(bulk_peca_operations, ordered=False)

        schoolYear.nSchools = schools.count()
        schoolYear.nStudents = nStudents
        schoolYear.nTeachers = nTeachers
        schoolYear.nSponsors = len(sponsorsIds.keys())
        schoolYear.nCoordinators = len(coordinatorsIds.keys())
        schoolYear.refreshDiagnosticsSummary()
        schoolYear.save()
        current_app.logger.info('ok')

def refresh_role_permissions():
    from app.models.role_model import Role, Permission, ActionHandler
    from app.models.entity_model import Entity, Action
    from pymongo import UpdateOne
    from flask import current_app

    entities = Entity.objects(isDeleted=False)
    entitiesDict = {}
    for entity in entities:
        entitiesDict[str(entity.id)] = entity
    
    roles = Role.objects(isDeleted=False)
    bulk_operations = []
    for role in roles:
        for entity in entities:
            found = False
            for permission in role.permissions:
                if permission.entityId == str(entity.id):
                    found = True
                    for action in entity.actions:
                        actionFound = False
                        for pAction in permission.actions:
                            if pAction.name == action.name:
                                actionFound = True
                                pAction.label = action.label
                                pAction.sort = action.sort
                        if not actionFound:
                            permission.actions.append(
                                ActionHandler(
                                    name=action.name,
                                    label=action.label,
                                    sort=action.sort
                                )
                            )
            if not found:
                permission = Permission(
                    entityId=str(entity.id),
                    entityName=entity.name,
                    actions = [ActionHandler(name=action.name, label=action.label, sort=action.sort) for action in entity.actions]
                )
                role.permissions.append(permission)
        bulk_operations.append(
                UpdateOne({'_id': role.id}, {'$set': role.to_mongo().to_dict()}))

    if bulk_operations:
            Role._get_collection() \
                .bulk_write(bulk_operations, ordered=False)

