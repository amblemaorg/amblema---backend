# app/services/coordinator_service.py

from marshmallow import ValidationError

from app.schemas.coordinator_user_schema import TryAnswerSchema
from app.models.learning_module_model import LearningModule


class CoordinatorService():

    def tryAnswerModule(self, moduleId, jsonData):
        """Method for answers a learning module   
           params:
             moduleId: str,
             data: {"userId": "str", "answers":[{"quizId": "str", "option": "str"}]} 
        """
        schema = TryAnswerSchema()
        try:
            module = LearningModule.objects(
                id=moduleId, isDeleted=False).first()
            if not module:
                raise ValidationError(
                    {"moduleId": [{"status": "6",
                                   "msg": "Record not found"}]}
                )

            data = schema.load(jsonData)
            coordinator = data["coordinator"]
            return coordinator.tryAnswerLearningModule(module, data["answers"])

        except ValidationError as err:
            return err.normalized_messages(), 400
