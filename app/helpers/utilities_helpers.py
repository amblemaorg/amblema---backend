

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