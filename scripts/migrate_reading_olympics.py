
import os
import sys
sys.path.append('/home')

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
    from app.models.peca_setting_model import ReadingOlympics
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
        school_years = SchoolYear.objects(isDeleted=False)
        count = 0
        updated_count = 0
        
        for sy in school_years:
            count += 1
            modified = False
            print("Checking SchoolYear: {0} ({1})".format(sy.name, sy.id))
            
            if not sy.pecaSetting:
                print("  Skipping {0}: No pecaSetting".format(sy.name))
                continue

            for i in range(1, 4):
                lapse_key = 'lapse{0}'.format(i)
                lapse = sy.pecaSetting[lapse_key]
                print("  Checking {0}...".format(lapse_key))
                
                # Check for readingOlympics field existence or None value
                if not getattr(lapse, 'readingOlympics', None):
                    print("    Adding ReadingOlympics to {0}".format(lapse_key))
                    reading_olympics = ReadingOlympics(
                        status="2", # Default status: hidden/inactive
                        isStandard=True,
                        order=100
                    )
                    lapse.readingOlympics = reading_olympics
                    modified = True
                else:
                    print("    ReadingOlympics already exists in {0}".format(lapse_key))

            if modified:
                print("  Saving updates for SchoolYear {0}...".format(sy.name))
                sy.save()
                updated_count += 1
            else:
                print("  No changes needed for SchoolYear {0}".format(sy.name))
    except Exception as e:
        print("Error during migration: {0}".format(e))
        import traceback
        traceback.print_exc()