# app/tests/integration/roles_entities_test.py


import unittest
import json

from app import create_app
from app.tests.base import drop_testing_database
from app.helpers.handler_seeds import create_standard_roles
from app.models.admin_user_model import AdminUser
from app.models.entity_model import Entity
from app.models.role_model import Role
from app.models.state_model import State, Municipality


class RolesEntitiesTest(unittest.TestCase):
    """Roles (/roles) y entidades de permisos (/entities)."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        self.entity = Entity(
            name="Usuarios", devName="User",
            actions=[{"name": "user_view", "label": "Ver", "sort": 1}])
        self.entity.save()
        create_standard_roles()

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    # -- Roles --

    def test_standard_roles_get_entity_permissions(self):
        admin = Role.objects(devName="admin").first()
        self.assertTrue(admin.isStandard)
        self.assertEqual(admin.permissions[0].entityName, "Usuarios")
        self.assertTrue(admin.permissions[0].actions[0].allowed)

    def test_create_standard_roles_is_idempotent(self):
        create_standard_roles()
        self.assertEqual(Role.objects(devName="admin").count(), 1)
        self.assertEqual(len(Role.objects(devName="admin").first().permissions), 1)

    def test_list_hides_superadmin(self):
        res = self.client().get('/roles')
        self.assertEqual(res.status_code, 200)
        devNames = [r['devName'] for r in self.json(res)['records']]
        self.assertNotIn('superadmin', devNames)
        self.assertIn('admin', devNames)
        self.assertEqual(devNames, sorted(devNames, key=lambda d: {
            'admin': 'Administrador', 'coordinator': 'Coordinador', 'school': 'Escuela',
            'sponsor': 'Padrino'}[d]))

    def test_list_with_filter(self):
        res = self.client().get('/roles?devName=coordinator')
        self.assertEqual([r['devName'] for r in self.json(res)['records']], ['coordinator'])

    def test_delete_standard_role_is_rejected(self):
        role = Role.objects(devName="admin").first()
        res = self.client().delete('/roles/{}'.format(role.id))
        self.assertEqual(res.status_code, 400)

    def test_delete_role_in_use_is_blocked(self):
        role = Role(name="Revisor", devName="revisor")
        role.save()
        state = State(name="Lara")
        state.save()
        municipality = Municipality(state=state, name="Iribarren")
        municipality.save()
        AdminUser(
            firstName="A", lastName="B", cardType="1", cardId="1", function="x",
            email="a@test.com", password="12345678", userType="1", phone="0212",
            role=role, addressState=state, addressMunicipality=municipality).save()
        res = self.client().delete('/roles/{}'.format(role.id))
        self.assertEqual(res.status_code, 419)
        self.assertEqual(self.json(res)['entity'], 'AdminUser')

    def test_delete_unused_role(self):
        role = Role(name="Revisor", devName="revisor")
        role.save()
        res = self.client().delete('/roles/{}'.format(role.id))
        self.assertEqual(res.status_code, 200)
        role.reload()
        self.assertTrue(role.isDeleted)

    # -- Entidades --

    def test_entities_crud(self):
        res = self.client().get('/entities')
        self.assertEqual([e['name'] for e in self.json(res)['records']], ['Usuarios'])

        res = self.client().post('/entities', data=json.dumps({
            "name": "Escuelas", "devName": "School",
            "actions": [{"name": "school_view", "label": "Ver", "sort": 1}]}),
            content_type='application/json')
        self.assertEqual(res.status_code, 201)
        entityId = self.json(res)['id']

        res = self.client().get('/entities/{}'.format(entityId))
        self.assertEqual(self.json(res)['name'], "Escuelas")

        res = self.client().put('/entities/{}'.format(entityId), data=json.dumps({"name": "Planteles"}),
                                content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.json(res)['name'], "Planteles")

        res = self.client().delete('/entities/{}'.format(entityId))
        self.assertEqual(res.status_code, 200)
        res = self.client().get('/entities/{}'.format(entityId))
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
