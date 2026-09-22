# /app/controllers/project_modules_controller.py

from flask_restful import Resource
from app.models.project_model import Project
from app.models.learning_module_model import LearningModule
from app.helpers.handler_authorization import jwt_required


class ProjectModulesController(Resource):

    @jwt_required
    def get(self, id):
        project = Project.objects(id=id, isDeleted=False).first()
        if not project:
            return {"message": "Project not found"}, 404

        coordinator = project.coordinator
        coordinator_data = None
        coordinator_learning_map = {}

        if coordinator:
            coordinator_data = {
                "id": str(coordinator.id),
                "name": coordinator.name,
                "email": coordinator.email,
                "phone": coordinator.phone,
                "instructed": getattr(coordinator, 'instructed', False),
                "curriculum": {
                    "name": coordinator.curriculum.name,
                    "url": coordinator.curriculum.url
                } if getattr(coordinator, 'curriculum', None) else None
            }
            if getattr(coordinator, 'learning', None):
                for lmod in coordinator.learning:
                    coordinator_learning_map[str(lmod.moduleId)] = lmod

        # Retrieve all active learning modules
        modules = LearningModule.objects(isDeleted=False).order_by('priority', 'createdAt')
        modules_list = []

        for mod in modules:
            mod_id_str = str(mod.id)
            coord_mod = coordinator_learning_map.get(mod_id_str)

            # Quizzes of the module
            quizzes_list = []
            for q in (mod.quizzes or []):
                quizzes_list.append({
                    "id": str(q.id),
                    "question": q.question,
                    "optionA": q.optionA,
                    "optionB": q.optionB,
                    "optionC": q.optionC,
                    "optionD": q.optionD,
                    "correctOption": q.correctOption
                })

            attempts_list = []
            status = "1"  # Not started / pending
            score = 0
            total_attempts = 0

            if coord_mod:
                status = coord_mod.status or "1"
                score = coord_mod.score or 0
                total_attempts = len(coord_mod.attempts) if coord_mod.attempts else 0
                for att in (coord_mod.attempts or []):
                    answers_list = []
                    for ans in (att.answers or []):
                        answers_list.append({
                            "quizId": str(ans.quizId),
                            "option": ans.option
                        })
                    attempts_list.append({
                        "status": att.status,
                        "createdAt": att.createdAt.isoformat() if getattr(att, 'createdAt', None) else None,
                        "answers": answers_list
                    })

            modules_list.append({
                "id": mod_id_str,
                "name": mod.name,
                "title": mod.title,
                "description": mod.description,
                "status": status,
                "isApproved": status == "3",
                "score": score,
                "totalAttempts": total_attempts,
                "attempts": attempts_list,
                "quizzes": quizzes_list
            })

        project_data = {
            "id": str(project.id),
            "code": str(project.code).zfill(7),
            "phase": project.phase,
            "status": project.status,
            "school": {
                "id": str(project.school.id),
                "name": project.school.name
            } if project.school else None,
            "sponsor": {
                "id": str(project.sponsor.id),
                "name": project.sponsor.name
            } if project.sponsor else None,
            "coordinator": coordinator_data
        }

        return {
            "project": project_data,
            "modules": modules_list
        }, 200
