import os
import sys

sys.path.append('/home')

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

with app.app_context():
    try:
        peca_projects = PecaProject.objects(isDeleted=False)
        peca_count = 0
        peca_updated_count = 0
        students_updated_count = 0

        for peca in peca_projects:
            peca_count += 1
            modified = False
            
            for i in range(1, 4):
                lapse_key = 'lapse{}'.format(i)
                lapse = peca[lapse_key]
                
                # Check Math Olympics
                if getattr(lapse, 'olympics', None) and lapse.olympics.students:
                    for student in lapse.olympics.students:
                        if student.status == "2":
                            student.status = "3"
                            modified = True
                            students_updated_count += 1
                        if student.statusNational == "2":
                            student.statusNational = "3"
                            modified = True
                            students_updated_count += 1
                
                # Check Reading Olympics
                if getattr(lapse, 'readingOlympics', None) and lapse.readingOlympics.students:
                    for student in lapse.readingOlympics.students:
                        if student.status == "2":
                            student.status = "3"
                            modified = True
                            students_updated_count += 1
                        if student.statusNational == "2":
                            student.statusNational = "3"
                            modified = True
                            students_updated_count += 1

            if modified:
                print("  Saving updates for PecaProject {}...".format(peca.id))
                peca.save()
                peca_updated_count += 1

        print("\nMigration complete.")
        print("Total PecaProjects checked: {}".format(peca_count))
        print("Total PecaProjects updated: {}".format(peca_updated_count))
        print("Total Students updated: {}".format(students_updated_count))

    except Exception as e:
        print("Error during migration: {}".format(e))
        import traceback
        traceback.print_exc()
