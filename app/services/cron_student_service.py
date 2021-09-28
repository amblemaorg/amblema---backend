# app/services/cron_student_service.py

from datetime import datetime

from flask import current_app
from marshmallow import ValidationError
from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.peca_student_model import SectionClass
from app.models.peca_student_model import StudentClass

class CronStudentService():
    def run(self):
        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
        pecas = PecaProject.objects(
            isDeleted=False,
            schoolYear=schoolYear.id)
        for peca in pecas:
            school = SchoolUser.objects(code=peca.school.code, isDeleted=False).first()
            sections_peca = peca.school.sections.filter(isDeleted=False)
            students_save = []
            for section in sections_peca:
                section_save = SectionClass()
                section_save.id = section.id
                section_save.grade = section.grade
                section_save.name = section.name
                section_save.schoolYear = schoolYear.id
                students_peca = section.students.filter(isDeleted=False)
                for student in students_peca:
                    student_filter = next((stu for stu in students_save if stu.cardId == student.cardId), None)
                    if not student_filter:
                        student_save = StudentClass()
                        student_save.firstName = student.firstName
                        student_save.lastName = student.lastName
                        student_save.cardId = student.cardId
                        student_save.cardType = student.cardType
                        student_save.birthdate = student.birthdate
                        student_save.gender = student.gender
                        student_save.isDeleted = student.isDeleted
                        student_save.sections = [section_save]
                        students_save.append(student_save)
                school.students = students_save
                school.save()
                    
        return {"status":200, "msg": "Exito"},200