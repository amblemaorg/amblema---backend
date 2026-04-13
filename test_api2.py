from app import create_app
from app.services.peca_yearbook_service import YearbookService
from app.models.peca_project_model import PecaProject

app = create_app('development')
with app.app_context():
    pecaId = "68daf9b498d6455346b6f554"
    peca = PecaProject.objects(isDeleted=False, id=pecaId).first()
    if peca:
        print("Raw DB Sections:")
        for s in peca.school.sections:
            print(f"- {s.name}: {s.groupedWith}")
