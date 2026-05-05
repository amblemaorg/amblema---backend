import os
import sys
import unittest
import datetime
from mongoengine import connect, disconnect
from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.models.project_model import Project
from app.models.school_user_model import SchoolUser
from app.models.sponsor_user_model import SponsorUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.yearbook_approval_model import YearbookApproval
from app.models.peca_school_model import School
from app.models.shared_embedded_documents import Approval, Link, ProjectReference, SchoolReference, DocumentReference
from app.services.school_year_service import CronUpdateDataProjectsService, CronClearApprovalHistoryService
from app.models.role_model import Role

# Set environment variable for testing DB - MUST be done before importing app/config
os.environ["TESTING_DB_URL"] = "mongodb://amblema:garden86@mongo:27017/amblema_test_yearbook?authSource=amblema"

from app import create_app

class TestSchoolYearServiceRefactor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        disconnect()
        cls.app_context.pop()

    def setUp(self):


        
        # Create Dummy Role
        self.role = Role(
            name="Admin",
            devName="admin",
            permissions=[]
        )
        self.role.save()

        # Create SchoolYear
        self.schoolYear = SchoolYear(
            name="2024-2025",
            startDate=datetime.date(2024, 9, 1),
            endDate=datetime.date(2025, 7, 31),
            status="1",
            isDeleted=False
        )
        self.schoolYear.initFirstPecaSetting() # Initialize default settings
        self.schoolYear.save()

        # Create Users
        self.school_user = SchoolUser(
            name="Escuela Test",
            email="escuela@test.com",
            password="123",
            userType="4",
            role=self.role.id,
            code="123456",
            phone="1234567890"
        )
        self.school_user.save()

        self.sponsor_user = SponsorUser(
            name="Padrino Test",
            email="padrino@test.com",
            password="123",
            userType="3",
            role=self.role.id,
            companyRif="J-123456789",
            companyType="1",
            companyPhone="1234567890"
        )
        self.sponsor_user.save()

        self.coordinator_user = CoordinatorUser(
            name="Coordinador Test",
            email="coordinador@test.com",
            password="123",
            userType="2",
            role=self.role.id
        )
        self.coordinator_user.save()

        # Create Project
        self.project = Project(
            school=self.school_user,
            sponsor=self.sponsor_user,
            coordinator=self.coordinator_user,
            schoolYear=self.schoolYear.id
        )
        self.project.save()

        # Create PecaProject
        self.peca = PecaProject(
            schoolYear=self.schoolYear.id,
            project=self.project.getReference()
        )
        self.peca.school = School(
            name=self.school_user.name,
            code=self.school_user.code,
            phone=self.school_user.phone,
            addressState=self.school_user.addressState,
            addressMunicipality=self.school_user.addressMunicipality,
            address=self.school_user.address,
            addressCity=self.school_user.addressCity,
            principalFirstName=self.school_user.principalFirstName,
            principalLastName=self.school_user.principalLastName,
            principalEmail=self.school_user.principalEmail,
            principalPhone=self.school_user.principalPhone,
            subPrincipalFirstName=self.school_user.subPrincipalFirstName,
            subPrincipalLastName=self.school_user.subPrincipalLastName,
            subPrincipalEmail=self.school_user.subPrincipalEmail,
            subPrincipalPhone=self.school_user.subPrincipalPhone,
            nTeachers=self.school_user.nTeachers,
            nAdministrativeStaff=self.school_user.nAdministrativeStaff,
            nLaborStaff=self.school_user.nLaborStaff,
            nStudents=self.school_user.nStudents,
            nGrades=self.school_user.nGrades,
            facebook=self.school_user.facebook,
            instagram=self.school_user.instagram,
            twitter=self.school_user.twitter,
        )
        self.peca.save()

        # Create YearbookApproval
        self.approval1 = YearbookApproval(
            pecaId=str(self.peca.id),
            approval=Approval(
                id="1",
                createdAt=datetime.datetime.utcnow(),
                updatedAt=datetime.datetime.utcnow(),
                status="1",
                detail={
                    "school": {"name": "Old School Name"},
                    "sponsor": {"name": "Old Sponsor Name"},
                    "coordinator": {"name": "Old Coordinator Name"},
                    "lapse1": {"diagnosticSummary": []},
                    "lapse2": {"diagnosticSummary": []},
                    "lapse3": {"diagnosticSummary": []}
                }
            )
        )
        self.approval1.save()

    def test_cron_update_data_projects_service(self):
        # Update user names
        self.school_user.name = "New School Name"
        self.school_user.save()
        self.project.school = self.school_user
        self.project.save()
        
        # Update Peca Project Reference (simulating what happens in ProjectService usually)
        self.peca.project = self.project.getReference()
        self.peca.school.name = "New School Name"
        self.peca.save()

        # Run CronUpdateDataProjectsService
        service = CronUpdateDataProjectsService()
        service.run(limit=10, skip=0)

        # Verify YearbookApproval updated
        approval = YearbookApproval.objects(id=self.approval1.id).first()
        self.assertEqual(approval.approval.detail['school']['name'], "New School Name")
        self.assertEqual(approval.approval.detail['sponsor']['name'], "Padrino Test") # Should match current sponsor

    def test_cron_clear_approval_history_service(self):
        # Create some old approvals
        past_date = datetime.datetime(2023, 1, 1)
        
        approval_old = YearbookApproval(
            pecaId=str(self.peca.id),
            approval=Approval(
                id="old",
                createdAt=past_date,
                updatedAt=past_date,
                status="1", # Pending
                detail={}
            )
        )
        approval_old.save()
        
        # Run CronClearApprovalHistoryService (clearing history from before today)
        service = CronClearApprovalHistoryService()
        # desde=1 (January), hasta=12 (December)
        # logic filters approvals updated >= first day of 'desde' month?
        # Re-reading logic:
        # fecha_inicio = datetime.datetime(now.year, desde, 1)
        # keep if updatedAt >= fecha_inicio
        
        # If I want to verify deletion, I should set date range such that approval_old is excluded?
        # Actually logic is: Keep if updatedAt >= fecha_inicio AND status in [1,2,3].
        # So if I set fecha_inicio to NOW, the old one (2023) should be deleted.
        
        current_month = datetime.datetime.now().month
        service.run(desde=current_month, hasta=current_month)
        
        # Check if approval_old is deleted
        approval_check = YearbookApproval.objects(id=approval_old.id).first()
        self.assertIsNone(approval_check)
        
        # Check if approval1 (created now) is kept
        approval1_check = YearbookApproval.objects(id=self.approval1.id).first()
        self.assertIsNotNone(approval1_check)

if __name__ == '__main__':
    unittest.main()
