# app/models/role_model.py


from datetime import datetime
from bson import ObjectId
import re

from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)


class ActionHandler(EmbeddedDocument):
    name = fields.StringField(required=True)
    label = fields.StringField(required=True)
    sort = fields.IntField()
    allowed = fields.BooleanField(default=False)
    meta = {'ordering': ['+sort']}


class Permission(EmbeddedDocument):
    entityId = fields.StringField(required=True)
    entityName = fields.StringField(required=True)
    actions = fields.EmbeddedDocumentListField(ActionHandler, required=True)
    meta = {'ordering': ['+entityName']}


class Role(Document):
    name = fields.StringField(unique_c=True, required=True)
    devName = fields.StringField(unique_c=True)
    status = fields.StringField(max_length=1, default='1')
    isStandard = fields.BooleanField(default=False)
    isDeleted = fields.BooleanField(default=False)
    permissions = fields.EmbeddedDocumentListField(Permission)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {
        'ordering': ['+name', '+permissions__entityName'],
        'collection': 'roles'
    }

    def clean(self):
        from app.models.entity_model import Entity

        if not self.pk and not self.isStandard:
            self.devName = re.sub(
                r'[\W_]', '_', str(self.name).strip().lower())
            entities = Entity.objects(isDeleted=False)
            for entity in entities:
                permission = Permission(
                    entityId=str(entity.id),
                    entityName=entity.name
                )
                for action in entity.actions:
                    permission.actions.append(
                        ActionHandler(
                            name=action.name,
                            label=action.label,
                            sort=action.sort,
                            allowed=False
                        )
                    )
                self.permissions.append(permission)
