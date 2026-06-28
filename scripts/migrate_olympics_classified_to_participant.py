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
    from app.models.peca_project_model import PecaProject
    from app.models.school_user_model import SchoolUser
    from app.models.school_year_model import SchoolYear
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
        pecas = PecaProject.objects(isDeleted=False)
        print("Found {0} PecaProjects.".format(len(pecas)))

        modified_pecas_count = 0
        modified_students_count = 0

        for peca in pecas:
            peca_modified = False
            for lapse in range(1, 4):
                # Math Olympics
                math_olympics = getattr(peca, 'lapse{0}'.format(lapse)).olympics
                if math_olympics and math_olympics.students:
                    for student in math_olympics.students:
                        if student.statusRegional == "2":
                            student.statusRegional = "1"
                            peca_modified = True
                            modified_students_count += 1
                        if student.statusNational == "2":
                            student.statusNational = "1"
                            peca_modified = True
                            modified_students_count += 1

                # Reading Olympics
                reading_olympics = getattr(peca, 'lapse{0}'.format(lapse)).readingOlympics
                if reading_olympics and reading_olympics.students:
                    for student in reading_olympics.students:
                        if student.statusRegional == "2":
                            student.statusRegional = "1"
                            peca_modified = True
                            modified_students_count += 1
                        if student.statusNational == "2":
                            student.statusNational = "1"
                            peca_modified = True
                            modified_students_count += 1

            if peca_modified:
                peca.save()
                modified_pecas_count += 1
                print("Updated student statuses in PecaProject: {0}".format(peca.id))

        print("Total PecaProjects updated: {0}".format(modified_pecas_count))
        print("Total student statuses migrated: {0}".format(modified_students_count))

        # Now recalculate all school summaries
        print("Recalculating school summaries...")
        schools_count = 0
        for peca in pecas:
            if not peca.project or not peca.project.school:
                continue
            school_id = peca.project.school.id
            school = SchoolUser.objects(id=school_id, isDeleted=False).first()
            if not school:
                continue

            schools_count += 1
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
                math_olympics = getattr(peca, 'lapse{0}'.format(lapse)).olympics
                if math_olympics and math_olympics.students:
                    for student in math_olympics.students:
                        math_summary['inscribed'] += 1
                        if student.status in ["2", "3"]:
                            math_summary['participant'] += 1
                        if student.status == "3":
                            math_summary['classified'] += 1
                        
                        if student.statusRegional in ["1", "2"]:
                            math_summary['participantRegional'] += 1
                        if student.statusRegional == "1":
                            if student.result == "1":
                                math_summary['medalsGold'] += 1
                            elif student.result == "2":
                                math_summary['medalsSilver'] += 1
                            elif student.result == "3":
                                math_summary['medalsBronze'] += 1
                        
                        if student.statusNational in ["1", "2"]:
                            math_summary['inscribedNational'] += 1
                        if student.statusNational == "1":
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
                        if student.statusRegional == "1":
                            if student.result == "1":
                                reading_summary['medalsGold'] += 1
                            elif student.result == "2":
                                reading_summary['medalsSilver'] += 1
                            elif student.result == "3":
                                reading_summary['medalsBronze'] += 1
                        
                        if student.statusNational in ["1", "2"]:
                            reading_summary['inscribedNational'] += 1
                        if student.statusNational == "1":
                            if student.resultNational == "1":
                                reading_summary['medalsGoldNational'] += 1
                            elif student.resultNational == "2":
                                reading_summary['medalsSilverNational'] += 1
                            elif student.resultNational == "3":
                                reading_summary['medalsBronzeNational'] += 1

            for k, v in math_summary.items():
                setattr(school.olympicsSummary, k, v)
            for k, v in reading_summary.items():
                setattr(school.olympicsReadingSummary, k, v)
            school.save()

        print("Recalculated {0} school summaries.".format(schools_count))

        # Recalculate SchoolYear summaries
        print("Recalculating SchoolYear summaries...")
        school_years = SchoolYear.objects(isDeleted=False)
        for sy in school_years:
            sy.refreshOlympicsSummary()
            sy.save()
            print("Recalculated SchoolYear: {0}".format(sy.name))

        print("Migration and recalculation completed successfully!")

    except Exception as e:
        print("Error during migration: {0}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
