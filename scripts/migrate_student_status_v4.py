import os
import sys

# Load .env
env_file = '.env'
if os.path.exists(env_file):
    print("Loading {}".format(env_file))
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, value = line.strip().split('=', 1)
                    if not os.getenv(key):
                        os.environ[key] = value
                except ValueError:
                    continue

# Set INSTANCE if not set
if not os.getenv('INSTANCE'):
    os.environ['INSTANCE'] = 'development'

try:
    from app import create_app
    from app.models.peca_project_model import PecaProject
    from app.models.school_user_model import SchoolUser
except ImportError as e:
    print("Import Error: {}".format(e))
    sys.exit(1)

try:
    print("Creating app with config: {}".format(os.getenv('INSTANCE')))
    app = create_app(os.getenv('INSTANCE'))
except Exception as e:
    print("Failed to create app: {}".format(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("App created. Entering app context...")

def recalculate_summary(lapse_olympics, summary):
    if not lapse_olympics or not lapse_olympics.students:
        return
    summary.inscribed = len(lapse_olympics.students)
    summary.participant = len(lapse_olympics.students.filter(status="2")) + len(lapse_olympics.students.filter(status="3"))
    summary.classified = len(lapse_olympics.students.filter(status="3"))
    summary.medalsGold = len(lapse_olympics.students.filter(result="1", status="3"))
    summary.medalsSilver = len(lapse_olympics.students.filter(result="2", status="3"))
    summary.medalsBronze = len(lapse_olympics.students.filter(result="3", status="3"))
    
    summary.inscribedNational = len(lapse_olympics.students.filter(result="1"))
    summary.classifiedNational = len(lapse_olympics.students.filter(statusNational="2"))
    summary.medalsGoldNational = len(lapse_olympics.students.filter(resultNational="1", statusNational="2"))
    summary.medalsSilverNational = len(lapse_olympics.students.filter(resultNational="2", statusNational="2"))
    summary.medalsBronzeNational = len(lapse_olympics.students.filter(resultNational="3", statusNational="2"))

with app.app_context():
    try:
        peca_projects = PecaProject.objects(isDeleted=False).only('id', 'lapse1', 'lapse2', 'lapse3', 'project')
        peca_count = 0
        peca_updated_count = 0
        students_updated_count = 0
        schools_updated_count = 0

        for peca in peca_projects:
            peca_count += 1
            modified = False
            
            for i in range(1, 4):
                lapse_key = 'lapse{}'.format(i)
                lapse = peca[lapse_key]
                
                # Update Math Olympics statuses
                if getattr(lapse, 'olympics', None) and lapse.olympics.students:
                    for student in lapse.olympics.students:
                        if student.status == "2":
                            student.status = "3"
                            modified = True
                            students_updated_count += 1
                
                # Update Reading Olympics statuses
                if getattr(lapse, 'readingOlympics', None) and lapse.readingOlympics.students:
                    for student in lapse.readingOlympics.students:
                        if student.status == "2":
                            student.status = "3"
                            modified = True
                            students_updated_count += 1

            if modified:
                print("  Saving updates for PecaProject {}...".format(peca.id))
                peca.save()
                peca_updated_count += 1
            
            # Recalculate SchoolUser summaries regardless of whether student statuses were modified (to populate the new 'participant' field)
            school = SchoolUser.objects(id=peca.project.school.id, isDeleted=False).first()
            if school:
                for i in range(1, 4):
                    lapse = peca['lapse{}'.format(i)]
                    if getattr(lapse, 'olympics', None) and lapse.olympics.students:
                        recalculate_summary(lapse.olympics, school.olympicsSummary)
                    if getattr(lapse, 'readingOlympics', None) and lapse.readingOlympics.students:
                        recalculate_summary(lapse.readingOlympics, school.olympicsReadingSummary)
                
                school.save()
                schools_updated_count += 1

        print("\nMigration complete.")
        print("Total PecaProjects checked: {}".format(peca_count))
        print("Total PecaProjects updated: {}".format(peca_updated_count))
        print("Total Students updated: {}".format(students_updated_count))
        print("Total School summaries updated: {}".format(schools_updated_count))

    except Exception as e:
        print("Error during migration: {}".format(e))
        import traceback
        traceback.print_exc()
