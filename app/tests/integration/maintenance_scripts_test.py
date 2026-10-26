# app/tests/integration/maintenance_scripts_test.py


import unittest
from datetime import datetime

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.helpers.handler_seeds import create_entities, create_states_and_municipalities
from app.helpers.utilities_helpers import (
    refresh_projects, refresh_users_projects, refresh_home_statistics, copy_steps,
    refresh_role_permissions)
from app.helpers.peca_yearbook_helper import update_yearbook_data_in_approval
from app.models.entity_model import Entity, Action
from app.models.peca_project_model import PecaProject
from app.models.peca_section_model import Section
from app.models.peca_student_model import Student
from app.models.project_model import Project
from app.models.request_content_approval_model import RequestContentApproval
from app.models.role_model import Role
from app.models.school_year_model import SchoolYear
from app.models.state_model import State, Municipality
from app.models.step_model import Step


class MaintenanceScriptsTest(unittest.TestCase):
    """Comandos de manage.py (utilities_helpers / handler_seeds) y sincronización del AmbLeMario."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        seed_base()

    def tearDown(self):
        drop_testing_database(self.db)

    def enrolledProject(self, code="OD0001"):
        state, municipality = create_location()
        project = Project(
            coordinator=create_coordinator(state, municipality, email="c{}@test.com".format(code),
                                           cardId="c{}".format(code)),
            sponsor=create_sponsor(state, municipality, email="s{}@test.com".format(code)),
            school=create_school(state, municipality, email="e{}@test.com".format(code), code=code),
            phase="2")
        project.save()
        project.createPeca()
        project.reload()
        return project, PecaProject.objects(project__id=str(project.id)).first()

    # -- Semillas --

    def test_create_states_and_municipalities(self):
        create_states_and_municipalities()
        self.assertGreaterEqual(State.objects.count(), 24)
        lara = State.objects(name="Lara").first()
        self.assertTrue(Municipality.objects(state=lara, name="Iribarren").first())

    def test_create_entities(self):
        create_entities()
        self.assertGreater(Entity.objects.count(), 10)
        self.assertTrue(Entity.objects(devName="ActivityPeca").first().actions)
        # name es único: correrlo dos veces falla en vez de duplicar entidades
        with self.assertRaises(Exception):
            create_entities()

    # -- utilities_helpers --

    def test_refresh_projects_rebuilds_school_years(self):
        create_school_year()
        project, peca = self.enrolledProject()
        Project.objects(id=project.id).update(schoolYears=[])

        refresh_projects()
        project.reload()
        self.assertEqual([r.pecaId for r in project.schoolYears], [str(peca.id)])
        self.assertEqual(project.schoolYears[0].schoolYear.name, "2025 - 2026")

    def test_refresh_users_projects_rebuilds_references(self):
        create_school_year()
        project, _ = self.enrolledProject()
        project.sponsor.projects = []
        project.sponsor.save()
        project.school.project = None
        project.school.save()

        refresh_users_projects()
        project.sponsor.reload()
        project.school.reload()
        project.coordinator.reload()
        self.assertEqual([p.id for p in project.sponsor.projects], [str(project.id)])
        self.assertEqual([p.id for p in project.coordinator.projects], [str(project.id)])
        self.assertEqual(project.school.project.id, str(project.id))

    def test_refresh_home_statistics(self):
        schoolYear = create_school_year()
        project, peca = self.enrolledProject()
        peca.school.sections = [Section(grade="1", name="A", students=[
            Student(firstName="A", lastName="B"), Student(firstName="C", lastName="D"),
            Student(firstName="E", lastName="F", isDeleted=True)])]
        peca.save()
        self.enrolledProject(code="OD0002")

        refresh_home_statistics()
        schoolYear.reload()
        self.assertEqual((schoolYear.nSchools, schoolYear.nStudents, schoolYear.nSponsors,
                          schoolYear.nCoordinators), (2, 2, 2, 2))
        project.school.reload()
        self.assertEqual(project.school.nStudents, 2)

    def test_copy_steps_from_previous_year(self):
        previous = create_school_year(name="2024 - 2025", start=datetime(2024, 9, 1),
                                      end=datetime(2025, 7, 31), status="2")
        Step.objects.update(schoolYear=previous.id)
        steps = Step.objects(schoolYear=previous.id).count()
        current = create_school_year()

        copy_steps()
        self.assertEqual(Step.objects(schoolYear=current.id).count(), steps)
        self.assertEqual(Step.objects(schoolYear=previous.id).count(), steps)

    def test_refresh_role_permissions_adds_new_entity_and_actions(self):
        entity = Entity(name="Reportes", devName="Report",
                        actions=[Action(name="report_view", label="Ver", sort=1)])
        entity.save()
        admin = Role.objects(devName="admin").first()
        self.assertNotIn(str(entity.id), [p.entityId for p in admin.permissions])

        entity.actions.append(Action(name="report_export", label="Exportar", sort=2))
        entity.actions[0].label = "Consultar"
        entity.save()
        refresh_role_permissions()

        admin.reload()
        permission = [p for p in admin.permissions if p.entityId == str(entity.id)][0]
        self.assertEqual([(a.name, a.label) for a in permission.actions],
                         [("report_view", "Consultar"), ("report_export", "Exportar")])

        refresh_role_permissions()
        admin.reload()
        self.assertEqual(len([p for p in admin.permissions if p.entityId == str(entity.id)]), 1)

    # -- Sincronización del AmbLeMario pendiente --

    def test_yearbook_pending_request_gets_current_sections(self):
        create_school_year()
        project, peca = self.enrolledProject()
        peca.school.sections = [Section(grade="2", name="B", students=[Student(firstName="Ana", lastName="Paz")])]
        peca.save()
        RequestContentApproval._get_collection().insert_one({
            "type": "7", "status": "1", "isDeleted": False, "createdAt": datetime.utcnow(),
            "project": {"id": str(project.id)}, "detail": {"pecaId": str(peca.id), "sections": [], "lapse1": {}}})

        update_yearbook_data_in_approval(PecaProject.objects(id=peca.id).first())
        request = RequestContentApproval.objects(type="7").first()
        self.assertEqual([s['name'] for s in request.detail['sections']], ["B"])
        self.assertEqual(request.detail['lapse1']['diagnosticSummary'][0]['grade'], "2")

    def test_yearbook_sync_without_pending_request(self):
        create_school_year()
        _, peca = self.enrolledProject()
        self.assertFalse(update_yearbook_data_in_approval(PecaProject.objects(id=peca.id).first()))


if __name__ == "__main__":
    unittest.main()
