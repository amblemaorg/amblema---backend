# app/tests/integration/school_years_projects_test.py


import unittest
import json
from datetime import datetime, timedelta

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.request_content_approval_model import RequestContentApproval
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.models.shared_embedded_documents import Approval
from app.models.step_model import Step
from app.models.yearbook_approval_model import YearbookApproval


class SchoolYearsProjectsTest(unittest.TestCase):
    """Años escolares (alta y cambio de año), inscripción, crons y proyectos."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        seed_base()
        self.state, self.municipality = create_location()

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    def createProject(self, phase="2", code="0002", email="escuela@test.com", school=True):
        coordinator = create_coordinator(self.state, self.municipality, email="c{}@test.com".format(code),
                                         cardId="2{}".format(code))
        sponsor = create_sponsor(self.state, self.municipality, email="s{}@test.com".format(code))
        schoolUser = create_school(self.state, self.municipality, email=email, code=code) if school else None
        project = Project(coordinator=coordinator, sponsor=sponsor, school=schoolUser, phase=phase)
        project.save()
        return project

    # -- Años escolares --

    def test_first_school_year(self):
        res = self.client().post('/schoolyears', data=json.dumps({"name": "x"}),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 201)
        schoolYear = SchoolYear.objects(id=self.json(res)['id']).first()
        now = datetime.now()
        self.assertEqual(schoolYear.name, "{} - {}".format(now.year, now.year + 1))
        self.assertEqual(schoolYear.status, "1")
        self.assertIsNotNone(schoolYear.pecaSetting.lapse1.readingOlympics)

    def test_rollover_blocked_while_year_is_running(self):
        create_school_year(start=datetime.now() - timedelta(days=30),
                           end=datetime.now() + timedelta(days=30))
        res = self.client().post('/schoolyears', data=json.dumps({"name": "x"}),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(self.json(res)['msg'], "Current school year has not finished yet")

    def test_rollover_closes_old_year_and_copies_setting(self):
        old = create_school_year(start=datetime(2024, 9, 1), end=datetime(2025, 7, 31))
        old.pecaSetting.lapse1.activities = []
        old.pecaSetting.lapse1.mathOlympic.status = "1"
        old.save()
        oldSteps = Step.objects(isDeleted=False).count()
        for step in Step.objects(isDeleted=False):
            step.schoolYear = old.id
            step.save()

        res = self.client().post('/schoolyears', data=json.dumps({"name": "x"}),
                                 content_type='application/json')
        self.assertEqual(res.status_code, 201)

        old.reload()
        new = SchoolYear.objects(id=self.json(res)['id']).first()
        self.assertEqual(old.status, "2")
        self.assertEqual(new.status, "1")
        self.assertEqual(new.pecaSetting.lapse1.mathOlympic.status, "1")
        self.assertEqual(new.pecaSetting.lapse1.activities, [])
        self.assertIsNone(new.pecaSetting.yearbookOrder)
        self.assertIsNotNone(new.pecaSetting.environmentalProject)
        self.assertEqual(Step.objects(schoolYear=new.id, isDeleted=False).count(), oldSteps)
        self.assertEqual(Step.objects(schoolYear=old.id, isDeleted=False).count(), oldSteps)

    def test_school_year_list_update_delete(self):
        schoolYear = create_school_year()
        res = self.client().get('/schoolyears')
        self.assertEqual([r['name'] for r in self.json(res)['dates']], ["2025 - 2026"])

        res = self.client().put('/schoolyears/{}'.format(schoolYear.id), data=json.dumps({"name": "Año 25"}),
                                content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.json(res)['name'], "Año 25")

        res = self.client().delete('/schoolyears/{}'.format(schoolYear.id))
        self.assertEqual(res.status_code, 200)
        res = self.client().get('/schoolyears/{}'.format(schoolYear.id))
        self.assertEqual(res.status_code, 404)

    # -- Inscripción en el año activo --

    def test_enroll_and_unenroll_update_counters(self):
        schoolYear = create_school_year()
        project = self.createProject()

        res = self.client().get('/enrollment')
        self.assertEqual([s['projectId'] for s in self.json(res)['availableSchools']], [str(project.id)])

        res = self.client().put('/enrollment/{}'.format(project.id))
        self.assertEqual(res.status_code, 200)
        schoolYear.reload()
        self.assertEqual((schoolYear.nSchools, schoolYear.nSponsors, schoolYear.nCoordinators,
                          schoolYear.nTeachers), (1, 1, 1, 20))

        res = self.client().put('/enrollment/{}'.format(project.id))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(self.json(res)['msg'], "School already enrolled in active school year")

        res = self.client().get('/enrollment')
        self.assertEqual(len(self.json(res)['enrolledSchools']), 1)
        self.assertEqual(self.json(res)['availableSchools'], [])

        res = self.client().put('/enrollment/{}?action=delete'.format(project.id))
        self.assertEqual(res.status_code, 200)
        schoolYear.reload()
        project.reload()
        self.assertEqual((schoolYear.nSchools, schoolYear.nSponsors, schoolYear.nCoordinators), (0, 0, 0))
        self.assertEqual(project.schoolYears, [])
        self.assertEqual(PecaProject.objects(isDeleted=False).count(), 0)

        res = self.client().put('/enrollment/{}?action=delete'.format(project.id))
        self.assertEqual(res.status_code, 400)

    def test_unenroll_blocked_by_pending_request(self):
        create_school_year()
        project = self.createProject()
        self.client().put('/enrollment/{}'.format(project.id))
        peca = PecaProject.objects(isDeleted=False).first()
        # Inserción directa: el pre_save de la solicitud exige datos del tipo que aquí no importan
        RequestContentApproval._get_collection().insert_one(
            {"type": "5", "status": "1", "isDeleted": False, "detail": {"pecaId": str(peca.id)}})

        res = self.client().put('/enrollment/{}?action=delete'.format(project.id))
        self.assertEqual(res.status_code, 419)
        self.assertEqual(self.json(res)['entity'], 'RequestContentApproval')

    def test_enroll_requires_approved_project_and_active_year(self):
        res = self.client().put('/enrollment/5f0000000000000000000000')
        self.assertEqual(res.status_code, 404)
        create_school_year()
        project = self.createProject(phase="1")
        res = self.client().put('/enrollment/{}'.format(project.id))
        self.assertEqual(res.status_code, 404)

    # -- Crons de estadísticas --

    def test_cron_update_statistics(self):
        schoolYear = create_school_year()
        project = self.createProject()
        self.client().put('/enrollment/{}'.format(project.id))

        res = self.client().get('/cron/statistics/schoolYear')
        self.assertEqual(res.status_code, 200)
        schoolYear.reload()
        self.assertEqual((schoolYear.nTeachers, schoolYear.nStudents), (0, 0))
        school = SchoolUser.objects(id=project.school.id).first()
        self.assertEqual(school.nStudents, 0)

    def test_cron_empty_schools(self):
        create_school_year()
        project = self.createProject()
        self.client().put('/enrollment/{}'.format(project.id))
        school = SchoolUser.objects(id=project.school.id).first()
        school.nStudents = 50
        school.olympicsSummary.medalsGold = 3
        school.save()

        res = self.client().get('/cron/schools/empty')
        self.assertEqual(res.status_code, 200)
        school.reload()
        self.assertEqual((school.nStudents, school.olympicsSummary.medalsGold), (0, 0))

    # -- Crons de historial de aprobaciones del AmbLeMario --

    def addApprovals(self, peca, statuses, updatedAt=None):
        approvals = []
        for idx, status in enumerate(statuses):
            when = (updatedAt or datetime.utcnow()) + timedelta(minutes=idx)
            approval = YearbookApproval(
                pecaId=str(peca.id), approval=Approval(status=status), createdAt=when, updatedAt=when)
            approval.save()
            approvals.append(approval)
        return approvals

    def test_clear_approval_history_past_years_keeps_last_approved(self):
        create_school_year()
        project = self.createProject()
        self.client().put('/enrollment/{}'.format(project.id))
        peca = PecaProject.objects(isDeleted=False).first()
        SchoolYear.objects(id=peca.schoolYear.id).update(status="2")
        approvals = self.addApprovals(peca, ["2", "3", "2", "1"])

        res = self.client().get('/clear/approvalHistoryPast')
        self.assertEqual(res.status_code, 200)
        remaining = [str(a.id) for a in YearbookApproval.objects(pecaId=str(peca.id))]
        self.assertEqual(remaining, [str(approvals[2].id)])

    def test_clear_approval_history_active_year(self):
        create_school_year()
        project = self.createProject()
        self.client().put('/enrollment/{}'.format(project.id))
        peca = PecaProject.objects(isDeleted=False).first()
        old = self.addApprovals(peca, ["2"], updatedAt=datetime(datetime.now().year - 1, 1, 1))
        approvals = self.addApprovals(peca, ["2", "3", "1", "2", "3", "1"])

        month = datetime.now().month
        res = self.client().get('/cron/approvalHistory/clear/1/{}'.format(month))
        self.assertEqual(res.status_code, 200)
        remaining = [str(a.id) for a in YearbookApproval.objects(pecaId=str(peca.id)).order_by('createdAt')]
        # Pendientes del período + último aprobado + último rechazado; lo anterior al período se borra
        expected = [approvals[2], approvals[3], approvals[4], approvals[5]]
        self.assertEqual(remaining, [str(a.id) for a in expected])
        self.assertNotIn(str(old[0].id), remaining)

    # -- Proyectos --

    def test_projects_list_and_paginated_search(self):
        create_school_year()
        project = self.createProject()
        res = self.client().get('/projects')
        self.assertEqual([p['id'] for p in self.json(res)['records']], [str(project.id)])
        self.assertNotIn('stepsProgress', self.json(res)['records'][0])

        res = self.client().get('/projects?page=1&per_page=10&coordinator=ana')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self.json(res)['records']), 1)
        res = self.client().get('/projects?page=1&per_page=10&school=inexistente')
        self.assertEqual(self.json(res)['records'], [])

    def test_approved_project_requires_school(self):
        create_school_year()
        from marshmallow import ValidationError
        with self.assertRaises(ValidationError):
            self.createProject(school=False)

    def test_create_peca_is_idempotent(self):
        create_school_year()
        project = self.createProject()
        res = self.client().get('/projectpeca/{}'.format(project.id))
        self.assertEqual(res.status_code, 200)
        pecaId = self.json(res)['pecaId']
        res = self.client().get('/projectpeca/{}'.format(project.id))
        self.assertEqual(self.json(res)['pecaId'], pecaId)
        self.assertEqual(PecaProject.objects(isDeleted=False).count(), 1)

    def test_update_step_unknown_project(self):
        res = self.client().post('/projectsteps/5f0000000000000000000000', data={"id": "x", "status": "2"})
        self.assertEqual(res.status_code, 400)

    def test_delete_project_detaches_users(self):
        create_school_year()
        project = self.createProject(phase="1")
        res = self.client().delete('/projects/{}'.format(project.id))
        self.assertEqual(res.status_code, 200)
        project.reload()
        self.assertTrue(project.isDeleted)
        project.sponsor.reload()
        project.coordinator.reload()
        project.school.reload()
        self.assertEqual(project.sponsor.projects, [])
        self.assertEqual(project.coordinator.projects, [])
        self.assertIsNone(project.school.project)

    def test_delete_project_with_peca_is_blocked(self):
        create_school_year()
        project = self.createProject()
        self.client().put('/enrollment/{}'.format(project.id))
        res = self.client().delete('/projects/{}'.format(project.id))
        self.assertEqual(res.status_code, 419)
        self.assertEqual(self.json(res)['entity'], 'PecaProject')


if __name__ == "__main__":
    unittest.main()
