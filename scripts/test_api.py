from app import create_app
from app.services.peca_project_service import PecaProjectService
import json

app = create_app('development')
with app.app_context():
    pecaId = "68daf9b498d6455346b6f554"
    service = PecaProjectService()
    data, code = service.get(pecaId)
    sections = data['school']['sections']
    for section in sections:
        print("ID:", section['id'], "Grp:", section.get('groupedWith'))
