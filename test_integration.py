from app import create_app
from app.services.peca_project_service import PecaProjectService
import requests

app = create_app('development')
with app.app_context():
    pecaId = "68daf9b498d6455346b6f554"
    
    # 1. Do the PATCH over HTTP to simulate frontend exactly
    data = {
        "sections": [
            {
                "id": "68e3c6bb98d6455346b7103a", # Section A 5
                "groupedWith": "TESTING_HTTP_PATCH"
            }
        ]
    }
    resp = requests.patch(f'http://localhost:5000/pecaprojects/yearbook/sectiongrouping/{pecaId}', json=data)
    print("PATCH Status:", resp.status_code)
    print("PATCH text:", resp.text)
    
    # 2. Use service.get to read the DB exactly like GET /pecaprojects/<id> will
    service = PecaProjectService()
    data, code = service.get(pecaId)
    sections = data['school']['sections']
    
    found = False
    for section in sections:
        if section['id'] == "68e3c6bb98d6455346b7103a":
            print("FETCHED Grp AFTER PATCH:", section.get('groupedWith'))
            found = True
            
    if not found:
        print("Section not found in dump!")
