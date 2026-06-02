import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env
env_file = '.env'
if os.path.exists(env_file):
    print("Loading {0}".format(env_file))
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
    from app.models.school_year_model import SchoolYear
    from app.models.school_user_model import SchoolUser
    from app.models.peca_project_model import PecaProject
except ImportError as e:
    print("Import Error: {0}".format(e))
    sys.exit(1)

try:
    print("Creating app with config: {0}".format(os.getenv('INSTANCE')))
    app = create_app(os.getenv('INSTANCE'))
except Exception as e:
    print("Failed to create app: {0}".format(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("App created. Entering app context...")

with app.app_context():
    try:
        active_sy = SchoolYear.objects(isDeleted=False, status="1").first()
        if not active_sy:
            print("No active school year found.")
            sys.exit(0)

        print("Recalculating olympics summaries for SchoolYear: {0} ({1})".format(active_sy.name, active_sy.id))

        pecas = PecaProject.objects(schoolYear=active_sy.id, isDeleted=False)

        count = 0
        for peca in pecas:
            if not peca.project or not peca.project.school:
                continue

            school_id = peca.project.school.id
            school = SchoolUser.objects(id=school_id, isDeleted=False).first()
            
            if not school:
                continue
            
            count += 1
            print("Processing School: {0}".format(school.name))

            math_summary = {
                'inscribed': 0, 'participant': 0, 'classified': 0,
                'medalsGold': 0, 'medalsSilver': 0, 'medalsBronze': 0,
                'participantRegional': 0, 'classifiedRegional': 0,
                'inscribedNational': 0, 'classifiedNational': 0,
                'medalsGoldNational': 0, 'medalsSilverNational': 0, 'medalsBronzeNational': 0
            }
            
            reading_summary = {
                'inscribed': 0, 'participant': 0, 'classified': 0,
                'medalsGold': 0, 'medalsSilver': 0, 'medalsBronze': 0,
                'participantRegional': 0, 'classifiedRegional': 0,
                'inscribedNational': 0, 'classifiedNational': 0,
                'medalsGoldNational': 0, 'medalsSilverNational': 0, 'medalsBronzeNational': 0
            }

            for lapse in range(1, 4):
                # Math Olympics
                olympics = getattr(peca, 'lapse{0}'.format(lapse)).olympics
                if olympics and olympics.students:
                    for student in olympics.students:
                        math_summary['inscribed'] += 1
                        if student.status in ["2", "3"]:
                            math_summary['participant'] += 1
                        if student.status == "3":
                            math_summary['classified'] += 1
                        
                        if student.statusRegional in ["1", "2"]:
                            math_summary['participantRegional'] += 1
                        if student.statusRegional == "2":
                            math_summary['classifiedRegional'] += 1
                            if student.result == "1":
                                math_summary['medalsGold'] += 1
                            elif student.result == "2":
                                math_summary['medalsSilver'] += 1
                            elif student.result == "3":
                                math_summary['medalsBronze'] += 1
                        
                        if student.statusNational in ["1", "2"]:
                            math_summary['inscribedNational'] += 1
                        if student.statusNational == "2":
                            math_summary['classifiedNational'] += 1
                            if student.resultNational == "1":
                                math_summary['medalsGoldNational'] += 1
                            elif student.resultNational == "2":
                                math_summary['medalsSilverNational'] += 1
                            elif student.resultNational == "3":
                                math_summary['medalsBronzeNational'] += 1

                # Reading Olympics
                reading_olympics = getattr(peca, 'lapse{0}'.format(lapse)).readingOlympics
                if reading_olympics and reading_olympics.students:
                    for student in reading_olympics.students:
                        reading_summary['inscribed'] += 1
                        if student.status in ["2", "3"]:
                            reading_summary['participant'] += 1
                        if student.status == "3":
                            reading_summary['classified'] += 1
                        
                        if student.statusRegional in ["1", "2"]:
                            reading_summary['participantRegional'] += 1
                        if student.statusRegional == "2":
                            reading_summary['classifiedRegional'] += 1
                            if student.result == "1":
                                reading_summary['medalsGold'] += 1
                            elif student.result == "2":
                                reading_summary['medalsSilver'] += 1
                            elif student.result == "3":
                                reading_summary['medalsBronze'] += 1
                        
                        if student.statusNational in ["1", "2"]:
                            reading_summary['inscribedNational'] += 1
                        if student.statusNational == "2":
                            reading_summary['classifiedNational'] += 1
                            if student.resultNational == "1":
                                reading_summary['medalsGoldNational'] += 1
                            elif student.resultNational == "2":
                                reading_summary['medalsSilverNational'] += 1
                            elif student.resultNational == "3":
                                reading_summary['medalsBronzeNational'] += 1

            # Update SchoolUser
            for k, v in math_summary.items():
                setattr(school.olympicsSummary, k, v)
            
            for k, v in reading_summary.items():
                setattr(school.olympicsReadingSummary, k, v)
            
            school.save()

        print("Total Schools Processed: {0}".format(count))

        print("Recalculating SchoolYear olympics summary...")
        active_sy.refreshOlympicsSummary()
        active_sy.save()
        print("Done!")

    except Exception as e:
        print("Error during recalculation: {0}".format(e))
        import traceback
        traceback.print_exc()
