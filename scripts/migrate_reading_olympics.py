
import os
import sys

sys.path.append('/home')
# Load .env
env_file = '.env'
if os.path.exists(env_file):
    print(f"Loading {env_file}")
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
    from app.models.peca_setting_model import ReadingOlympics
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

try:
    print(f"Creating app with config: {os.getenv('INSTANCE')}")
    app = create_app(os.getenv('INSTANCE'))
except Exception as e:
    print(f"Failed to create app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("App created. Entering app context...")

with app.app_context():
    try:
        school_years = SchoolYear.objects(isDeleted=False)
        count = 0
        updated_count = 0
        
        for sy in school_years:
            count += 1
            modified = False
            print(f"Checking SchoolYear: {sy.name} ({sy.id})")
            
            if not sy.pecaSetting:
                print(f"  Skipping {sy.name}: No pecaSetting")
                continue

            for i in range(1, 4):
                lapse_key = f'lapse{i}'
                lapse = sy.pecaSetting[lapse_key]
                print(f"  Checking {lapse_key}...")
                
                # Check for readingOlympics field existence or None value
                if not getattr(lapse, 'readingOlympics', None):
                    print(f"    Adding ReadingOlympics to {lapse_key}")
                    reading_olympics = ReadingOlympics(
                        status="2", # Default status: hidden/inactive
                        isStandard=True,
                        order=100
                    )
                    lapse.readingOlympics = reading_olympics
                    modified = True
                else:
                    print(f"    ReadingOlympics already exists in {lapse_key}")

            if modified:
                print(f"  Saving updates for SchoolYear {sy.name}...")
                sy.save()
                updated_count += 1
            else:
                print(f"  No changes needed for SchoolYear {sy.name}")
        """
        # PecaProject Migration
        from app.models.peca_project_model import PecaProject
        from app.models.peca_olympics_model import Olympics
        
        school_years = SchoolYear.objects(isDeleted=False, status="1").first()

        peca_projects = PecaProject.objects(isDeleted=False, schoolYear=school_years.id).only('lapse1', 'lapse2', 'lapse3')
        print("Optimized query: Fetching only lapse fields for PecaProjects.")
        peca_count = 0
        peca_updated_count = 0

        for peca in peca_projects:
            peca_count += 1
            modified = False
            print(f"Checking PecaProject: {peca.id}")

            for i in range(1, 4):
                lapse_key = f'lapse{i}'
                lapse = peca[lapse_key]
                # print(f"  Checking {lapse_key}...")
                
                if not getattr(lapse, 'readingOlympics', None):
                    print(f"    Adding ReadingOlympics to {lapse_key}")
                    olympics = Olympics(
                        description="Olimpíada de Lectura",
                        date=None,
                        file=None
                    )
                    lapse.readingOlympics = olympics
                    modified = True
                else:
                    # print(f"    ReadingOlympics already exists in {lapse_key}")
                    pass

            if modified:
                print(f"  Saving updates for PecaProject {peca.id}...")
                peca.save()
                peca_updated_count += 1
            else:
                # print(f"  No changes needed for PecaProject {peca.id}")
                pass

        print(f"\nMigration complete.")
        print(f"Total SchoolYears checked: {count}")
        print(f"Total SchoolYears updated: {updated_count}")
        print(f"Total PecaProjects checked: {peca_count}")
        print(f"Total PecaProjects updated: {peca_updated_count}")
        """
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()