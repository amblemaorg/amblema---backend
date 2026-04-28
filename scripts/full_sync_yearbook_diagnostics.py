# -*- coding: utf-8 -*-
import os
import sys

sys.path.append('/home')

from flask import current_app
from app import create_app
app = create_app(os.getenv('INSTANCE', 'development'))

with app.app_context():
    from app.models.peca_project_model import PecaProject
    from app.models.request_content_approval_model import RequestContentApproval
    
    pecas = PecaProject.objects(isDeleted=False)
    
    print(f"Refreshing latest approved yearbook diagnostic summaries for {len(pecas)} projects...")
    
    project_count = 0
    updated_reqs = 0
    updated_pecas = 0
    
    for peca in pecas:
        peca_changed = False
        
        # Traverse approvalHistory from newest to oldest
        for approval in reversed(peca.yearbook.approvalHistory):
            req = RequestContentApproval.objects(id=approval.id).first()
            
            # Type 7 = Yearbook, Status 2 = Approved
            if req and req.type == "7" and req.status == "2":
                detail = approval.detail
                changed_approval = False
                
                for lapse_idx in [1, 2, 3]:
                    lapse_key = 'lapse{}'.format(lapse_idx)
                    if lapse_key in detail and 'diagnosticSummary' in detail[lapse_key]:
                        new_summary = []
                        for section in sorted(peca.school.sections.filter(isDeleted=False), key=lambda x: (x.grade, x.name)):
                            summary = section.diagnostics[lapse_key]
                            new_summary.append({
                                'grade': section.grade,
                                'name': section.name,
                                'wordsPerMin': summary.wordsPerMin,
                                'wordsPerMinIndex': float(summary.wordsPerMinIndex) if summary.wordsPerMinIndex is not None else 0,
                                'wordsPerMinCount': summary.wordsPerMinCount,
                                'multiplicationsPerMin': summary.multiplicationsPerMin,
                                'multiplicationsPerMinIndex': float(summary.multiplicationsPerMinIndex) if summary.multiplicationsPerMinIndex is not None else 0,
                                'multiplicationsPerMinCount': summary.multiplicationsPerMinCount,
                                'operationsPerMin': summary.operationsPerMin,
                                'operationsPerMinIndex': float(summary.operationsPerMinIndex) if summary.operationsPerMinIndex is not None else 0,
                                'operationsPerMinCount': summary.operationsPerMinCount
                            })
                        detail[lapse_key]['diagnosticSummary'] = new_summary
                        changed_approval = True
                
                if changed_approval:
                    # Update embedded in PecaProject
                    approval.detail = detail
                    peca_changed = True
                    
                    # Update separate RequestContentApproval doc
                    req_detail = req.detail
                    for lapse_idx in [1, 2, 3]:
                        lapse_key = 'lapse{}'.format(lapse_idx)
                        if lapse_key in req_detail:
                             req_detail[lapse_key]['diagnosticSummary'] = detail[lapse_key]['diagnosticSummary']
                    req.detail = req_detail
                    req.save(validate=False)
                    updated_reqs += 1
                
                # Only update the MOST RECENT APPROVED one, so break here
                break
        
        if peca_changed:
            try:
                peca.save(validate=False)
                updated_pecas += 1
            except Exception as e:
                print("Error saving peca {peca_id}: {e}".format(peca_id=peca.id, e=e))
            
        project_count += 1
        if project_count % 50 == 0:
            print("Processed {count}/{total} projects...".format(count=project_count, total=len(pecas)))

    print("Finished. Processed {count} projects. Total pecas updated: {updated_pecas}, total requests updated: {updated_reqs}".format(count=project_count, updated_pecas=updated_pecas, updated_reqs=updated_reqs))
