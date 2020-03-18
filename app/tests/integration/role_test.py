# app/tests/integration/role_test.py


import unittest
import json

from app import create_app, db

from app.models.role_model import Role, Permission, ActionHandler
from app.models.entity_model import Entity
from app.helpers.handler_seeds import create_entities


class RoleTest(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

        Entity(
            name="Rol",
            actions=[
                {
                    "name": "role_view",
                    "label": "Ver",
                    "sort": 1
                },
                {
                    "name": "role_create",
                    "label": "Crear",
                    "sort": 2
                },
                {
                    "name": "role_edit",
                    "label": "Editar",
                    "sort": 3
                },
                {
                    "name": "role_delete",
                    "label": "Eliminar",
                    "sort": 4
                }
            ]
        ).save()

        Entity(
            name="Municipio",
            actions=[
                {
                    "name": "municipality_view",
                    "label": "Ver",
                    "sort": 1
                },
                {
                    "name": "municipality_create",
                    "label": "Crear",
                    "sort": 2
                },
                {
                    "name": "municipality_edit",
                    "label": "Editar",
                    "sort": 3
                },
                {
                    "name": "municipality_delete",
                    "label": "Eliminar",
                    "sort": 4
                }
            ]
        ).save()

    def test_endpoint_rol(self):

        newRole = dict(
            name="New one",
            permissions=[]
        )
        entities = Entity.objects(isDeleted=False)
        for entity in entities:
            newRole["permissions"].append(
                {
                    "entityId": str(entity.id),
                    "entityName": entity.name,
                    "actions": [
                        {
                            "name": action.name,
                            "label": action.label,
                            "sort": 1,
                            "allowed": True
                        }
                        for action in entity.actions]
                }
            )
        res = self.client().post(
            '/roles',
            data=json.dumps(newRole),
            content_type='application/json')
        json_res = json.loads(
            res.data.decode('utf8').replace("'", '"'))
        self.assertEqual(res.status_code, 201)
        self.assertEqual('new_one', json_res["devName"])

    def test_entities(self):

        role = Role(
            name="New one",
            permissions=[]
        )
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
                        sort=1,
                        allowed=True
                    )
                )
            role.permissions.append(permission)
        role.save()

        self.assertEqual('Rol', role.permissions[1].entityName)

        entity = Entity.objects(name="Rol").first()
        entity.name = "Roles"
        entity.save()

        role = Role.objects.get(id=role.pk)
        self.assertEqual('Roles', role.permissions[1].entityName)

        entity = Entity.objects(name="Roles").first()
        entity.isDeleted = True
        entity.save()

        role = Role.objects.get(id=role.pk)
        self.assertEqual(1, len(role.permissions))

        entity = Entity.objects(name="Municipio").first()
        entity.actions[0].label = "Ver municipio"
        entity.save()

        role = Role.objects.get(id=role.pk)
        self.assertEqual("Ver municipio", role.permissions[0].actions[0].label)

    def tearDown(self):
        """teardown all initialized variables."""
        self.db.connection.drop_database('amblema_testing')
