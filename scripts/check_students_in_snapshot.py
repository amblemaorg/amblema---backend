# -*- coding: utf-8 -*-
import os
import sys

sys.path.append('/home')

from flask import current_app
from app import create_app
app = create_app(os.getenv('INSTANCE', 'development'))

with app.app_context():
    from app.models.peca_project_model import PecaProject
    peca = PecaProject.objects(id="68dafa3198d6455346b6f570").first()
    
    if peca.yearbook.approvalHistory:
        approval = peca.yearbook.approvalHistory[-1]
        print(f"Approval ID: {approval.id}")
        if 'sections' in approval.detail:
            sections = approval.detail['sections']
            print(f"Number of sections in snapshot: {len(sections)}")
            if sections:
                first_section = sections[0]
                print(f"Fields in section snapshot: {first_section.keys()}")
                if 'students' in first_section:
                    print(f"Number of students in first section: {len(first_section['students'])}")
                else:
                    print("No 'students' field in section snapshot.")
        else:
            print("No 'sections' field in approval snapshot.")
