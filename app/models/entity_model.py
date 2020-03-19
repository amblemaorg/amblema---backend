# app/models/entity_model.py

from datetime import datetime

from pymongo import UpdateOne
from mongoengine import (
    Document,
    EmbeddedDocument,
    fields,
    signals)


class Action(EmbeddedDocument):
    name = fields.StringField(unique_c=True, required=True)
    label = fields.StringField(required=True)
    sort = fields.IntField()
    isDeleted = fields.BooleanField(default=False)
    meta = {'ordering': ['+sort']}


class Entity(Document):
    name = fields.StringField(unique_c=True, required=True)
    isDeleted = fields.BooleanField(default=False)
    actions = fields.EmbeddedDocumentListField(Action)
    createdAt = fields.DateTimeField(default=datetime.utcnow)
    updatedAt = fields.DateTimeField(default=datetime.utcnow)
    meta = {'collection': 'entities', 'ordering': ['+name']}

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        from app.models.role_model import Permission, ActionHandler, Role
        # after create
        if 'created' in kwargs and kwargs['created']:
            bulk_operations = []
            roles = Role.objects(isDeleted=False).all()
            for role in roles:
                permission = Permission(
                    entityId=str(document.id),
                    entityName=document.name)
                for action in document.actions:
                    actionHandler = ActionHandler(
                        name=action.name,
                        label=action.label,
                        sort=action.sort,
                        allowed=False)
                    permission.actions.append(actionHandler)
                role.permissions.append(permission)
                bulk_operations.append(
                    UpdateOne({'_id': role.id}, {'$set': role.to_mongo().to_dict()}))
            if bulk_operations:
                document.__class__._get_collection() \
                    .bulk_write(bulk_operations, ordered=False)
        # after delete
        elif document.isDeleted:
            Role.objects(
                isDeleted=False,
                permissions__entityId=str(document.id)).update(
                pull__permissions__entityId=str(document.id))

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        from app.models.role_model import Permission, ActionHandler, Role
        # before update
        if document.id:
            oldDocument = document.__class__.objects.get(id=document.id)
            if document.actions != oldDocument.actions or document.name != oldDocument.name:
                bulk_operations = []
                roles = Role.objects(
                    isDeleted=False,
                    permissions__entityId=str(document.id))

                newActions = {}
                for action in document.actions:
                    newActions[action.name] = action

                for role in roles:
                    permission = role.permissions.filter(
                        entityId=str(document.id)).first()
                    permission.entityName = document.name

                    oldActions = [
                        action.name for action in permission.actions]
                    for action in permission.actions:
                        if action.name not in newActions:
                            permission.actions.remove(action)
                        else:
                            action.label = newActions[action.name].label
                            action.sort = newActions[action.name].sort

                    for action in document.actions:
                        if action.name not in oldActions:
                            permission.actions.append(
                                ActionHandler(
                                    name=action.name,
                                    label=action.label,
                                    sort=action.sort,
                                    allowed=False)
                            )
                    bulk_operations.append(
                        UpdateOne({'_id': role.id}, {'$set': role.to_mongo().to_dict()}))
                if bulk_operations:
                    Role._get_collection() \
                        .bulk_write(bulk_operations, ordered=False)


signals.pre_save.connect(Entity.pre_save, sender=Entity)
signals.post_save.connect(Entity.post_save, sender=Entity)
