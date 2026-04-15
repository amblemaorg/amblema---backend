# -*- coding: utf-8 -*-
import os
import sys

# Add the app directory to sys.path
sys.path.append('/home')

from app import create_app
from app.models.peca_project_model import PecaProject
from app.models.school_year_model import SchoolYear
from app.models.school_user_model import SchoolUser

def refresh_all_diagnostics():
    config_instance = os.getenv('INSTANCE')
    app = create_app(config_instance)
    
    with app.app_context():
        # Find the current school year
        school_year = SchoolYear.objects(status="1", isDeleted=False).first()
        if not school_year:
            print("No active school year found")
            return

        # Cambio de f-string a .format()
        print("Refreshing diagnostics for school year: {0}".format(school_year.name))

        # Corregido: se agregaron comas en el método .only()
        pecas = PecaProject.objects(schoolYear=school_year.id, isDeleted=False).only("id", "project", "school")
        print("Found {0} Pecas".format(len(pecas)))

        for peca in pecas:
            # Cambio de f-string a .format()
            print("Refreshing Peca for school: {0} ({1})".format(
                peca.project.school.name, 
                peca.id
            ))
            
            # Refresh each section
            for section in peca.school.sections:
                if not section.isDeleted:
                    section.refreshDiagnosticsSummary()
            
            # Refresh school summary
            peca.school.refreshDiagnosticsSummary()
            peca.save()

            # Update SchoolUser diagnostics (the graph uses this)
            school_user = SchoolUser.objects(id=peca.project.school.id).first()
            if school_user:
                school_user.diagnostics = peca.school.diagnostics
                school_user.save()
                print("Updated SchoolUser {0}".format(school_user.name))

        # Also refresh school year summary
        school_year.refreshDiagnosticsSummary()
        school_year.save()
        print("School year diagnostics refreshed")

if __name__ == "__main__":
    refresh_all_diagnostics()