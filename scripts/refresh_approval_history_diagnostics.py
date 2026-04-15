# -*- coding: utf-8 -*-
import os
import sys

sys.path.append('/home')

from app import create_app
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from mongoengine import get_db

def update_approval_history():
    config_instance = os.getenv('INSTANCE')
    app = create_app(config_instance)
    
    with app.app_context():
        school_year = SchoolYear.objects(status="1", isDeleted=False).first()
        if not school_year:
            print("No active school year found")
            return

        peca_ids = PecaProject.objects(
            schoolYear=school_year.id, 
            isDeleted=False
        ).scalar("id")
        
        print("Updating approval history for {0} Pecas".format(len(peca_ids)))

        for peca_id in peca_ids:
            peca = PecaProject.objects(id=peca_id).first()
            if not peca:
                continue
                
            print("Processing Peca: {0}".format(peca_id))

            if not peca.yearbook or not peca.yearbook.approvalHistory:
                continue

            modified = False
            for approval in peca.yearbook.approvalHistory:
                if not approval.detail:
                    continue
                
                for lapse in [1, 2, 3]:
                    lapse_key = 'lapse{0}'.format(lapse)
                    if lapse_key in approval.detail and 'diagnosticSummary' in approval.detail[lapse_key]:
                        diagnostic_summary = approval.detail[lapse_key]['diagnosticSummary']
                        
                        for summary in diagnostic_summary:
                            matched_section = None
                            for section in peca.school.sections:
                                if section.grade == summary.get('grade') and section.name == summary.get('name'):
                                    matched_section = section
                                    break
                            
                            if matched_section:
                                diag = getattr(matched_section.diagnostics, lapse_key, None)
                                if diag:
                                    summary['wordsPerMinCount'] = diag.wordsPerMinCount
                                    summary['multiplicationsPerMinCount'] = diag.multiplicationsPerMinCount
                                    summary['operationsPerMinCount'] = diag.operationsPerMinCount
                                    modified = True
                            else:
                                summary['wordsPerMinCount'] = 0
                                summary['multiplicationsPerMinCount'] = 0
                                summary['operationsPerMinCount'] = 0
                                modified = True

            if modified:
                peca.save()
                print("Updated approval variables for Peca {0}".format(peca.id))
            
        print("Finished updating approval history")


if __name__ == "__main__":
    update_approval_history()