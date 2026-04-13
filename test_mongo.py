from app import create_app
from app.models.peca_project_model import PecaProject

app = create_app('development')
with app.app_context():
    pecaId = "68daf9b498d6455346b6f554"
    peca = PecaProject.objects(isDeleted=False, id=pecaId).first()
    if peca:
        print("Found Project!")
        for section in peca.school.sections:
            print("Section:", section.id, section.name, section.grade, "GroupedWith:", getattr(section, 'groupedWith', None))
        
        # modify the first one
        if len(peca.school.sections) > 0:
            first = peca.school.sections[0]
            first.groupedWith = "TEST"
            peca.save()
            print("Saved with TEST")
            
            # verify
            peca2 = PecaProject.objects(isDeleted=False, id=pecaId).first()
            print("After fetch:", getattr(peca2.school.sections[0], 'groupedWith', None))
            
            # fix it back
            first.groupedWith = None
            peca.save()
