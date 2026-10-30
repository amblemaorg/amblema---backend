# app/tests/integration/requests_test.py


import unittest
import json
from datetime import datetime

from bson import ObjectId

from app import create_app
from app.tests.base import drop_testing_database
from app.tests.fixtures import (
    seed_base, create_location, create_coordinator, create_sponsor, create_school,
    create_school_year)
from app.models.coordinator_contact_model import CoordinatorContact
from app.models.peca_activities_model import ActivityPeca
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.request_content_approval_model import RequestContentApproval
from app.models.request_find_coordinator_model import RequestFindCoordinator
from app.models.request_project_approval_model import RequestProjectApproval
from app.models.school_contact_model import SchoolContact
from app.models.shared_embedded_documents import Approval
from app.models.yearbook_approval_model import YearbookApproval


class RequestsTest(unittest.TestCase):
    """Notificaciones pendientes, listados de solicitudes y cancelación de solicitudes de contenido."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client
        seed_base()
        self.state, self.municipality = create_location()
        self.schoolYear = create_school_year(start=datetime(2025, 9, 1), end=datetime(2026, 7, 31))
        self.coordinator = create_coordinator(self.state, self.municipality)

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    # -- helpers: inserciones directas para no disparar los hooks de cada tipo --

    def insert(self, model, **doc):
        doc.setdefault('isDeleted', False)
        doc.setdefault('status', "1")
        doc.setdefault('createdAt', datetime(2025, 10, 1))
        doc.setdefault('updatedAt', doc['createdAt'])
        return model._get_collection().insert_one(doc).inserted_id

    def contentRequest(self, code, type="3", status="1", createdAt=datetime(2025, 10, 1),
                       projectCode="0001", detail=None):
        return self.insert(
            RequestContentApproval, code=code, type=type, status=status, createdAt=createdAt,
            user=self.coordinator.id, project={"id": str(ObjectId()), "code": projectCode},
            detail=detail or {})

    def enrolledPeca(self):
        project = Project(coordinator=self.coordinator,
                          sponsor=create_sponsor(self.state, self.municipality),
                          school=create_school(self.state, self.municipality), phase="2")
        project.save()
        self.client().put('/enrollment/{}'.format(project.id))
        return PecaProject.objects(isDeleted=False).first()

    # -- Notificaciones pendientes --

    def test_pending_notifications(self):
        self.insert(CoordinatorContact, firstName="Ana", lastName="Ruiz", createdAt=datetime(2025, 10, 2))
        self.insert(SchoolContact, name="Escuela", createdAt=datetime(2025, 10, 3))
        self.insert(SchoolContact, name="Vieja", createdAt=datetime(2025, 8, 1))  # antes del año activo
        self.insert(SchoolContact, name="Atendida", status="2")
        self.insert(RequestFindCoordinator, user=self.coordinator.id, createdAt=datetime(2025, 10, 4))
        self.insert(RequestProjectApproval, createdAt=datetime(2025, 10, 5))
        self.contentRequest("1", createdAt=datetime(2025, 10, 6))

        res = self.client().get('/notifications/pending')
        self.assertEqual(res.status_code, 200)
        records = self.json(res)['records']
        self.assertEqual([r['notiType'] for r in records], [4, 3, 2, 1, 1])
        self.assertEqual(records[0]['user'], {"name": "Ana Pérez"})
        self.assertEqual(records[4]['name'], "Ana Ruiz")

    # -- Solicitudes de contenido: tabla paginada --

    def test_paginated_filters_and_numeric_sort(self):
        for code in ("9", "10", "2"):
            self.contentRequest(code, projectCode="00{}".format(code))
        self.contentRequest("11", status="2")
        self.contentRequest("12", type="7")
        self.contentRequest("13", createdAt=datetime(2025, 1, 1))  # año escolar anterior

        res = self.client().get('/requestscontentapproval?page=1&per_page=10&_sort=code&_order=ASC')
        body = self.json(res)
        self.assertEqual([r['code'] for r in body['records']], ["2", "9", "10", "11", "12"])
        self.assertEqual(body['pagination'], {"total_records": 5, "total_pages": 1, "page": 1})
        self.assertEqual(body['records'][0]['user'], {"id": str(self.coordinator.id), "name": "Ana Pérez"})
        self.assertEqual(body['records'][0]['typeUser'], "2")

        def codes(query):
            res = self.client().get('/requestscontentapproval?page=1&per_page=10&' + query)
            return sorted(r['code'] for r in self.json(res)['records'])

        self.assertEqual(codes('status=2'), ["11"])
        self.assertEqual(codes('type=7'), ["12"])
        self.assertEqual(codes('code=1'), ["10", "11", "12"])
        self.assertEqual(codes('project=009'), ["9"])
        self.assertEqual(codes('user=ana&typeUser=2'), ["10", "11", "12", "2", "9"])
        self.assertEqual(codes('user=nadie'), [])

    def test_paginated_pages_and_invalid_params(self):
        for code in range(1, 6):
            self.contentRequest(str(code))
        res = self.client().get('/requestscontentapproval?page=2&per_page=2')
        body = self.json(res)
        self.assertEqual(len(body['records']), 2)
        self.assertEqual(body['pagination']['total_pages'], 3)
        res = self.client().get('/requestscontentapproval?page=x&per_page=2')
        self.assertEqual(res.status_code, 400)

    def test_full_list_hides_students_of_sections(self):
        self.contentRequest("1", type="4", detail={"sections": [{"name": "A", "students": [{"id": "1"}]}]})
        res = self.client().get('/requestscontentapproval')
        record = self.json(res)['records'][0]
        self.assertEqual(record['detail']['sections'], [{"name": "A"}])
        self.assertEqual(record['typeUser'], "2")

    # -- Listados de contacto y de búsqueda de usuarios --

    def test_contact_and_find_lists(self):
        self.insert(CoordinatorContact, firstName="Ana", lastName="Ruiz", createdAt=datetime(2025, 10, 2))
        self.insert(SchoolContact, name="Escuela", createdAt=datetime(2025, 10, 3))
        res = self.client().get('/contactrequests')
        records = self.json(res)['records']
        self.assertEqual([(r['type'], r['name']) for r in records],
                         [("school", "Escuela"), ("coordinator", "Ana Ruiz")])
        res = self.client().get('/contactrequests?status=2')
        self.assertEqual(self.json(res)['records'], [])

    # -- Cancelar (borrar) solicitudes de contenido revierte el estado en aprobación --

    def test_cancel_activity_request_reopens_activity(self):
        peca = self.enrolledPeca()
        requestId = self.contentRequest("1")
        activity = ActivityPeca(id=str(ObjectId()), name="Huerto", devName="huerto", approvalType="3",
                                status="2", approvalHistory=[Approval(id=str(requestId), status="1")])
        peca.lapse1.activities.append(activity)
        peca.save()
        RequestContentApproval._get_collection().update_one(
            {'_id': requestId}, {'$set': {'detail': {'pecaId': str(peca.id), 'lapse': '1', 'id': activity.id}}})

        res = self.client().delete('/requestscontentapproval/{}'.format(requestId))
        self.assertEqual(res.status_code, 200)
        peca.reload()
        saved = peca.lapse1.activities[0]
        self.assertEqual(saved.status, "1")
        self.assertEqual(saved.approvalHistory[0].status, "4")

    def test_cancel_yearbook_request(self):
        peca = self.enrolledPeca()
        peca.yearbook.isInApproval = True
        peca.save()
        requestId = self.contentRequest("1", type="7", detail={"pecaId": str(peca.id)})
        YearbookApproval(pecaId=str(peca.id), approval=Approval(id=str(requestId), status="1")).save()

        res = self.client().delete('/requestscontentapproval/{}'.format(requestId))
        self.assertEqual(res.status_code, 200)
        peca.reload()
        self.assertFalse(peca.yearbook.isInApproval)
        self.assertEqual(YearbookApproval.objects(pecaId=str(peca.id)).first().approval.status, "4")


if __name__ == "__main__":
    unittest.main()
