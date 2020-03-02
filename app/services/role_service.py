# app/services/entity_service.py


from functools import reduce
import operator

from marshmallow import ValidationError
from mongoengine import Q

from app.helpers.error_helpers import RegisterNotFound
from app.helpers.document_metadata import getUniqueFields
from app.services.generic_service import GenericServices
from app.models.role_model import Role, ActionHandler, Permission


class RoleService(GenericServices):
    def getAllRecords(self, filters=None, only=None, exclude=()):
        """
        get all available roles records
        """
        schema = self.Schema(only=only, exclude=exclude)

        if filters:
            filterList = []
            for f in filters:
                filterList.append(Q(**{f['field']: f['value']}))
            records = self.Model.objects(isDeleted=False, name__ne='SuperAdmin').filter(
                reduce(operator.and_, filterList)).all()
        else:
            records = self.Model.objects(
                isDeleted=False, name__ne='SuperAdmin').all()

        return {"records": schema.dump(records, many=True)}, 200


class EntityService(GenericServices):

    def saveRecord(self, jsonData):
        """
        Method that saves a new record.   
        params: jsonData
        """
        schema = self.Schema()
        try:
            data = schema.load(jsonData)
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            record = self.Model()
            for field in data.keys():
                record[field] = data[field]
                if field in uniquesFields:
                    fieldsForCheckDuplicates.append(
                        {"field": field, "value": data[field]})
            isDuplicated = self.checkForDuplicates(fieldsForCheckDuplicates)
            if isDuplicated:
                for field in isDuplicated:
                    raise ValidationError(
                        {field["field"]: [{"status": "5",
                                           "msg": "Duplicated record found: '{}'".format(field["value"])}]}
                    )
            try:
                record.save()
                roles = Role.objects(isDeleted=False).all()
                for role in roles:
                    permission = Permission(
                        entityId=str(record.id),
                        entityName=record.name)
                    for action in record.actions:
                        actionHandler = ActionHandler(
                            name=action.name,
                            label=action.label,
                            sort=action.sort,
                            allowed=False)
                        permission.actions.append(actionHandler)
                    role.permissions.append(permission)
                    role.save()
                return schema.dump(record), 201
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        except ValidationError as err:
            return err.messages, 400

    def updateRecord(self, recordId, jsonData, partial=False):
        """
        Update a record
        """
        schema = self.Schema()
        try:
            data = schema.load(jsonData, partial=partial)
            record = self.getOr404(recordId)
            has_changed = False
            uniquesFields = getUniqueFields(self.Model)
            fieldsForCheckDuplicates = []
            for field in data.keys():
                if data[field] != record[field]:
                    record[field] = data[field]
                    has_changed = True
                    if field in uniquesFields:
                        fieldsForCheckDuplicates.append(
                            {"field": field, "value": data[field]})

            if has_changed:
                isDuplicated = self.checkForDuplicates(
                    fieldsForCheckDuplicates)
                if isDuplicated:
                    for field in isDuplicated:
                        raise ValidationError(
                            {field["field"]: [{"status": "5",
                                               "msg": "Duplicated record found: '{}'".format(field["value"])}]}
                        )
                try:
                    record.save()
                    roles = Role.objects(
                        isDeleted=False,
                        permissions__entityId=str(record.id))

                    newActions = {}
                    for action in record.actions:
                        newActions[action.name] = action

                    for role in roles:
                        permission = role.permissions.filter(
                            entityId=str(recordId)).first()
                        permission.entityName = record.name

                        oldActions = [
                            action.name for action in permission.actions]
                        for action in permission.actions:
                            if action.name not in newActions:
                                permission.actions.remove(action)
                            else:
                                action.label = newActions[action.name].label
                                action.sort = newActions[action.name].sort

                        for action in record.actions:
                            if action.name not in oldActions:
                                permission.actions.append(
                                    ActionHandler(
                                        name=action.name,
                                        label=action.label,
                                        sort=action.sort,
                                        allowed=False)
                                )
                        role.save()

                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            return schema.dump(record), 200
        except ValidationError as err:
            return err.messages, 400

    def deleteRecord(self, recordId):
        """
        Delete (change isDelete True) a record
        """
        record = self.getOr404(recordId)
        try:
            record.isDeleted = True
            record.save()
            for role in Role.objects(isDeleted=False, permissions__entityId=recordId):
                permission = role.permissions.filter(
                    entityId=str(recordId)).first()
                role.permissions.remove(permission)
                role.save()

        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

        return {"message": "Record deleted successfully"}, 200
