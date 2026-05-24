
import os
import sys
import logging
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db():
    db_url = os.getenv('DB_URL')
    
    # Check for testing DB URL if not set (for local testing)
    if not db_url:
        db_url = os.getenv('TESTING_DB_URL')

    if not db_url:
        logger.error("DB_URL environment variable not set")
        sys.exit(1)
    
    # Handle authSource if needed
    if 'authSource' not in db_url and 'admin' not in db_url:
         # Append authSource if missing and likely needed (e.g., standard mongo container)
         # But be careful not to break existing connection strings
         pass

    try:
        client = MongoClient(db_url)
        # Extract db name from URL
        db_name = db_url.split('/')[-1].split('?')[0]
        db = client[db_name]
        logger.info("Connected to database: {}".format(db_name))
        return db
    except Exception as e:
        logger.error("Failed to connect to database: {}".format(e))
        sys.exit(1)

def migrate_approvals():
    db = get_db()
    peca_project_collection = db['peca_project']
    yearbook_approval_collection = db['yearbook_approval']

    # Find PecaProjects with non-empty approvalHistory
    query = {
        "yearbook.approvalHistory": {
            "$exists": True, 
            "$not": {"$size": 0}
        }
    }
    
    # Find PecaProjects with non-empty approvalHistory, fetching only _id
    projects_cursor = peca_project_collection.find(query, projection={'_id': 1})
    
    # Count is deprecated in newer pymongo, use count_documents
    try:
        count = peca_project_collection.count_documents(query)
    except:
        count = projects_cursor.count()
    
    logger.info("Found {} PecaProjects with approvalHistory to migrate.".format(count))

    if count == 0:
        logger.info("No projects to migrate.")
        return

    migrated_total = 0
    errors = 0
    
    # Convert cursor to list of IDs to avoid long-running cursor issues if needed, 
    # though iterating cursor is usually fine. 
    # Given user request "obtain ids ... and then query each", we'll do exactly that.
    project_ids = [doc['_id'] for doc in projects_cursor]

    for pid in project_ids:
        # Fetch the full project document individually
        project = peca_project_collection.find_one({"_id": pid})
        if not project:
            logger.warning("Project {} not found during iteration.".format(pid))
            continue

        peca_id = str(project['_id'])
        approval_history = project.get('yearbook', {}).get('approvalHistory', [])
        
        logger.info("Processing PecaProject {} with {} approvals.".format(peca_id, len(approval_history)))
        
        project_approvals_migrated = 0
        try:
            for approval in approval_history:
                # Prepare new document
                # Ensure approval data is compatible
                new_doc = {
                    "pecaId": peca_id,
                    "approval": approval,
                    "createdAt": approval.get('createdAt', datetime.utcnow()),
                    "updatedAt": approval.get('updatedAt', datetime.utcnow())
                }
                
                # Insert into yearbook_approval
                yearbook_approval_collection.insert_one(new_doc)
                project_approvals_migrated += 1
            
            # Verify migration before deleting
            saved_count = yearbook_approval_collection.count_documents({"pecaId": peca_id})
            
            # We check if we have AT LEAST the number of history items. 
            # (In case script was run partially before)
            if saved_count >= len(approval_history):
                # Remove approvalHistory from PecaProject
                result = peca_project_collection.update_one(
                    {"_id": project['_id']},
                    {"$unset": {"yearbook.approvalHistory": ""}}
                )
                if result.modified_count > 0:
                    logger.info("Successfully migrated {} approvals for {}. Removed field from PecaProject.".format(project_approvals_migrated, peca_id))
                    migrated_total += project_approvals_migrated
                else:
                     logger.warning("Migrated data but failed to unset field for {} (maybe already unset?).".format(peca_id))
            else:
                logger.error("Mismatch in count for {}: Expected {}, found {}. NOT removing old data.".format(peca_id, len(approval_history), saved_count))
                errors += 1

        except Exception as e:
            logger.error("Error migrating PecaProject {}: {}".format(peca_id, e))
            errors += 1

    logger.info("Migration completed. Total approvals migrated: {}. Errors: {}".format(migrated_total, errors))

if __name__ == "__main__":
    try:
        input_func = raw_input
    except NameError:
        input_func = input
        
    confirm = input_func("Are you sure you want to run this migration? (yes/no): ")
    if confirm.lower() == 'yes':
        migrate_approvals()
    else:
        logger.info("Migration cancelled.")
