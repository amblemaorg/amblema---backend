# app/services/olympics_history_service.py

from datetime import datetime
from app.models.olympics_history_model import OlympicsHistory
from app.schemas.olympics_history_schema import OlympicsHistorySchema
from app.services.generic_service import GenericServices
from marshmallow import ValidationError

class OlympicsHistoryService(GenericServices):

    def getRecord(self, id=None):
        """
        Get the single history record
        """
        record = self.Model.objects(isDeleted=False).first()
        if not record:
            record = self.Model()
            record.save()

        schema = self.Schema()
        return schema.dump(record), 200

    def saveRecord(self, jsonData, files=None):
        """
        Save/Update the single history record
        """
        schema = self.Schema()
        try:
            # We ignore any ID and always update the first one found or create it
            record = self.Model.objects(isDeleted=False).first()
            if not record:
                record = self.Model()
            
            # partial=True allows updating only provided fields
            data = schema.load(jsonData, partial=True)
            
            for key, value in data.items():
                if key in ['mathOlympics', 'readingOlympics']:
                    # Update embedded document fields
                    # Mongoengine expects EmbeddedDocument instances, not dicts
                    embedded = getattr(record, key)
                    for field, val in value.items():
                        setattr(embedded, field, val)
                else:
                    setattr(record, key, value)
            
            record.updatedAt = datetime.utcnow()
            record.save()

            return schema.dump(record), 200

        except ValidationError as err:
            return err.normalized_messages(), 400
