

def refresh_users_projects():
    from app.models.project_model import Project
    from app.models.school_user_model import SchoolUser
    from app.models.sponsor_user_model import SponsorUser
    from app.models.coordinator_user_model import CoordinatorUser
    from pymongo import UpdateOne

    schools = SchoolUser.objects(isDeleted=False)
    sponsors = SponsorUser.objects(isDeleted=False)
    coordinators = CoordinatorUser.objects(isDeleted=False)

    bulk_operations = []
    for school in schools:
        school.project = None
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
        pecas = PecaProject.objects(isDeleted=False, schoolYear=schoolYear.id)
        for peca in pecas:
            schoolsIds[peca.project.school.id] = peca
            sponsorsIds[peca.project.sponsor.id] = peca
        schools = SchoolUser.objects(isDeleted=False, pk__in=schoolsIds.keys()).all()
        current_app.logger.info(len(pecas))
        current_app.logger.info(len(sponsorsIds.keys()))

        nStudents = 0
        nTeachers = 0
        bulk_operations = []

        for school in schools:
            peca = schoolsIds[str(school.id)]
            schoolStudents = 0
            for section in peca.school.sections.filter(isDeleted=False):
                schoolStudents += len(section.students.filter(isDeleted=False))
            school.nStudents = schoolStudents
            nStudents += schoolStudents
            school.nTeachers = len(school.teachers.filter(isDeleted=False))
            nTeachers += school.nTeachers
            bulk_operations.append(
                UpdateOne({'_id': school.id}, {'$set': school.to_mongo().to_dict()}))
        
        if bulk_operations:
            SchoolUser._get_collection() \
                .bulk_write(bulk_operations, ordered=False)

        schoolYear.nSchools = schools.count()
        schoolYear.nStudents = nStudents
        schoolYear.nTeachers = nTeachers
        schoolYear.nSponsors = len(sponsorsIds.keys())
        schoolYear.save()
    