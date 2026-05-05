# -*- coding: utf-8 -*-
import os
import sys

sys.path.append('/home')

from flask import current_app
from app import create_app
app = create_app(os.getenv('INSTANCE', 'development'))

with app.app_context():
    from app.models.peca_project_model import PecaProject
    from app.models.school_year_model import SchoolYear
    from app.helpers.peca_yearbook_helper import update_yearbook_data_in_approval
    
    print("Starting diagnostics recalculation for all un-deleted PecaProjects...")
    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    peca_ids = PecaProject.objects(isDeleted=False, schoolYear=schoolYear).scalar('id')
    peca_ids_list = list(peca_ids)
    count = 0
    total = len(peca_ids_list)
    
    for peca_id in peca_ids_list:
        peca = PecaProject.objects(id=peca_id).first()
        if not peca:
            continue
        try:
            # Recalculate section-level
            for section in peca.school.sections:
                section.refreshDiagnosticsSummary()
            
            # Recalculate school-level
            peca.school.refreshDiagnosticsSummary()
            update_yearbook_data_in_approval(peca)
            peca.save(validate=False)
            
            # Recalculate schoolYear-level
            schoolYear = peca.schoolYear.fetch()
            schoolYear.refreshDiagnosticsSummary()
            schoolYear.save(validate=False)
            
            count += 1
            print("Processed {count}/{total}".format(count=count, total=total)) 
        except Exception as e:
            print("Error processing PecaProject {peca_id}: {e}".format(peca_id=peca.id, e=e))
            
    print("Finished processing {count}/{total} PecaProjects!".format(count=count, total=total))
