# -*- coding: utf-8 -*-
# app/tests/integration/vademecum_permission_test.py
"""Permiso "Vademécum" en roles para el backoffice (BO-01)."""

import unittest

from app.tests.integration.vademecum_base import VademecumAdminTestBase


def allowed_in(role, action="vademecum_admin"):
    for permission in role.permissions:
        for handler in permission.actions:
            if handler.name == action:
                return handler.allowed
    return None  # el rol no tiene la entidad


class VademecumPermissionSeedTest(VademecumAdminTestBase):
    """La base ya corrió create_standard_roles y ensure_vademecum_permission."""

    def roles(self):
        from app.models.role_model import Role
        return {r.devName: r for r in Role.objects(isDeleted=False)}

    def test_entity_and_default_roles(self):
        from app.models.entity_model import Entity
        entity = Entity.objects(devName="vademecum").get()
        self.assertEqual(entity.name, u"Vademécum")
        self.assertEqual([a.name for a in entity.actions], ["vademecum_admin"])
        roles = self.roles()
        self.assertEqual({name: allowed_in(role) for name, role in roles.items()}, {
            "superadmin": True, "admin": True, "coordinator": False, "sponsor": False,
            "school": False})

    def test_is_idempotent_and_respects_changes(self):
        from app.helpers.vademecum_seeds import ensure_vademecum_permission
        from app.models.entity_model import Entity
        admin = self.roles()["admin"]
        for handler in admin.permissions.filter(entityName=u"Vademécum").first().actions:
            handler.allowed = False  # AmbLeMa se lo quitó desde "Roles"
        admin.save()

        self.assertEqual(ensure_vademecum_permission(), {
            "entityCreated": False, "rolesAdded": [], "rolesGranted": []})
        self.assertEqual(Entity.objects(devName="vademecum").count(), 1)
        self.assertFalse(allowed_in(self.roles()["admin"]))

    def test_new_role_gets_it_disabled(self):
        from app.models.role_model import Role
        role = Role(name="Editor de contenido", permissions=[])
        role.save()  # Role.clean copia todas las entidades, sin permiso
        self.assertFalse(allowed_in(Role.objects.get(id=role.id)))

    def test_old_role_without_the_entity_gets_it_disabled(self):
        from app.helpers.vademecum_seeds import ensure_vademecum_permission
        from app.models.role_model import Role
        Role.objects(devName="coordinator").update_one(
            pull__permissions__entityName=u"Vademécum")
        self.assertIsNone(allowed_in(Role.objects.get(devName="coordinator")))
        self.assertEqual(ensure_vademecum_permission()["rolesAdded"], ["coordinator"])
        self.assertFalse(allowed_in(Role.objects.get(devName="coordinator")))

    def test_the_permission_reaches_the_login_payload(self):
        self.assertIn("vademecum_admin", self.admin.get_permissions())
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        self.assertNotIn("vademecum_admin", coordinator.get_permissions())


class VademecumPermissionApiTest(VademecumAdminTestBase):

    def set_allowed(self, devName, allowed):
        from app.models.role_model import Role
        role = Role.objects(devName=devName).get()
        for handler in role.permissions.filter(entityName=u"Vademécum").first().actions:
            handler.allowed = allowed
        role.save()

    def list_uploads(self, headers):
        return self.client.get("/vademecum/admin/sheets", headers=headers)

    def test_admin_role_without_the_permission_is_rejected(self):
        self.assertEqual(self.list_uploads(self.adminHeaders).status_code, 200)
        self.set_allowed("admin", False)
        # Se lee del rol en la BD: el mismo token deja de servir
        self.assertEqual(self.list_uploads(self.adminHeaders).status_code, 403)

    def test_other_role_with_the_permission_is_accepted(self):
        coordinator = self.create_user("coord@test.com", "10000002", "coordinator")
        headers = self.headers(coordinator)
        self.assertEqual(self.list_uploads(headers).status_code, 403)
        self.set_allowed("coordinator", True)
        self.assertEqual(self.list_uploads(headers).status_code, 200)

    def test_inactive_role_is_rejected(self):
        from app.models.role_model import Role
        Role.objects(devName="admin").update_one(set__status="2")
        self.assertEqual(self.list_uploads(self.adminHeaders).status_code, 403)


if __name__ == "__main__":
    unittest.main()
