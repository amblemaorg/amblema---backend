# app/services/promote_student_service.py

from datetime import datetime

from flask import current_app
from marshmallow import ValidationError
from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.peca_student_model import SectionClass, Student, Diagnostic
from app.models.peca_student_model import StudentClass

import unicodedata

from bson import ObjectId
from pymongo import UpdateOne


# PECA section fields without their students (the PECA documents carry every student)
SECTION_FIELDS = ('school.sections.id', 'school.sections.grade',
                  'school.sections.name', 'school.sections.isDeleted')


def _sortText(value):
    """
    Text for alphabetical ordering: lowercase, without accents and with
    the n with tilde between n and o, as in Spanish ('{' sorts after 'z').
    """
    if value is None:
        return u''
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'ignore')
    value = value.strip().lower().replace(u'\u00f1', u'n{')
    return u''.join(c for c in unicodedata.normalize('NFKD', value)
                    if not unicodedata.combining(c))


def _refId(ref):
    return getattr(ref, 'id', ref)


def _previousSchoolYear():
    return SchoolYear.objects(
        isDeleted=False, status="2").order_by('-createdAt').only('id').first()


def _schoolStudentsStatus(school_code, schoolYearId):
    """
    Reads the school's master students list raw (ids, isDeleted and the school
    year of each section). Going through the model would dereference SchoolYear
    for every section, loading a whole school year document each time.
    Returns (schoolId, active student ids, ids already enrolled in schoolYearId).
    """
    school = SchoolUser._get_collection().find_one(
        {'code': school_code, 'isDeleted': False, '_cls': SchoolUser._class_name},
        {'students.id': 1, 'students.isDeleted': 1, 'students.sections.schoolYear': 1})
    active, enrolled = set(), set()
    if not school:
        return None, active, enrolled
    for student in school.get('students') or []:
        if student.get('isDeleted'):
            continue
        studentId = str(student.get('id'))
        active.add(studentId)
        for section in student.get('sections') or []:
            if _refId(section.get('schoolYear')) == schoolYearId:
                enrolled.add(studentId)
                break
    return school['_id'], active, enrolled


def _previousPecaStudents(school_code, schoolYearPreviusId, studentIds):
    """Active students of the previous year PECA, raw, keyed by id (str)"""
    if not studentIds or not schoolYearPreviusId:
        return {}
    peca = PecaProject._get_collection().find_one(
        {'isDeleted': False, 'schoolYear': schoolYearPreviusId, 'school.code': school_code},
        {'school.sections.isDeleted': 1, 'school.sections.students': 1})
    students = {}
    for section in ((peca or {}).get('school') or {}).get('sections') or []:
        if section.get('isDeleted'):
            continue
        for student in section.get('students') or []:
            studentId = str(student.get('id'))
            if not student.get('isDeleted') and studentId in studentIds:
                students[studentId] = student
    return students


def _countPecaStudents(pecaId):
    """Active students in active sections of a PECA"""
    pipeline = [
        {"$match": {"_id": pecaId}},
        {"$unwind": "$school.sections"},
        {"$match": {"school.sections.isDeleted": {"$ne": True}}},
        {"$unwind": "$school.sections.students"},
        {"$match": {"school.sections.students.isDeleted": {"$ne": True}}},
        {"$group": {"_id": None, "total": {"$sum": 1}}}
    ]
    res = list(PecaProject._get_collection().aggregate(pipeline))
    return res[0]["total"] if res else 0


def updateSchoolYearStudents(schoolYear, fallback):
    # Suma los nStudents ya persistidos de cada PECA del año, sin cargar ni guardar cada documento
    if not schoolYear:
        return
    pipeline = [
        {"$match": {"schoolYear": schoolYear.id, "isDeleted": False}},
        {"$group": {"_id": None, "total": {"$sum": "$school.nStudents"}}}
    ]
    agg_res = list(PecaProject._get_collection().aggregate(pipeline))
    schoolYear.nStudents = agg_res[0]["total"] if agg_res else fallback
    schoolYear.save()


class PromoteStudentService():
    def getList(self, school_code, id_section):
        try:
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").only('id').first()
            schoolYearPrevius = _previousSchoolYear()
            schoolId, active, enrolled = _schoolStudentsStatus(school_code, schoolYear.id)
            if not schoolId:
                return {'status': 0, 'message': 'School not found'}, 400
            peca = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYearPrevius.id, school__code=school_code).only('school.sections').first()
            if peca:
                section_peca = peca.school.sections.filter(isDeleted=False, id=id_section).first()
                students_list = []
                if section_peca:
                    for student in section_peca.students.filter(isDeleted=False):
                        studentId = str(student.id)
                        # Only students still active in the school and not enrolled in the current year
                        if studentId in active and studentId not in enrolled:
                            students_list.append({"id":studentId, "firstName": student.firstName, "lastName": student.lastName, "cardId": student.cardId, "cardType": student.cardType, "birthdate": str(student.birthdate), "gender": student.gender})
                # By last name, then first name
                students_list.sort(key=lambda st: (_sortText(st["lastName"]), _sortText(st["firstName"])))
                return {"status":200, "msg": "Exito", "students": students_list},200
            else:
                return {"status":400, "msg": "No tiene data de periodos anteriores"},200
                
        except Exception as e:   
            return {'status': 0, 'message': str(e)}, 400
    
    def promoteStudents(self, school_code, data):
        """
        Promotes only the students selected in the front (data["students"]),
        skipping the ones already enrolled in the current year or no longer
        active. Student data is taken from the previous year PECA (what the
        list showed), not from the request body.
        """
        try:
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            peca_actual = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYear.id, school__code=school_code).only(*SECTION_FIELDS).first()
            section = peca_actual.school.sections.filter(
                    isDeleted=False, id=data["id_section_current"]).first()
            if section:
                schoolId, active, enrolled = _schoolStudentsStatus(school_code, schoolYear.id)
                requested = []
                for student in data.get("students") or []:
                    studentId = str(student.get("id"))
                    if studentId in active and studentId not in enrolled and studentId not in requested:
                        requested.append(studentId)

                schoolYearPrevius = _previousSchoolYear()
                previousStudents = _previousPecaStudents(
                    school_code, schoolYearPrevius.id if schoolYearPrevius else None, set(requested))

                newStudents = []
                for studentId in requested:
                    previous = previousStudents.get(studentId)
                    if not previous:
                        continue
                    student_save = Student(
                        id=previous.get("id"),
                        firstName=previous.get("firstName"),
                        lastName=previous.get("lastName"),
                        cardId=previous.get("cardId"),
                        cardType=previous.get("cardType"),
                        birthdate=previous.get("birthdate"),
                        gender=previous.get("gender"),
                        isDeleted=False,
                        lapse1=Diagnostic(),
                        lapse2=Diagnostic(),
                        lapse3=Diagnostic())
                    student_save.validate()
                    newStudents.append(student_save)

                if newStudents:
                    # One write for all the students in the PECA section
                    PecaProject._get_collection().update_one(
                        {'_id': peca_actual.id, 'school.sections.id': section.id},
                        {'$push': {'school.sections.$.students': {
                            '$each': [s.to_mongo() for s in newStudents]}}})

                    section_save = SectionClass()
                    section_save.name = section.name
                    section_save.grade = section.grade
                    section_save.isDeleted = False
                    section_save.schoolYear = schoolYear.id
                    section_save.id = section.id
                    sectionDoc = section_save.to_mongo()
                    # Current year section in each student's master record
                    SchoolUser._get_collection().bulk_write([
                        UpdateOne(
                            {'_id': schoolId, 'students.id': s.id},
                            {'$push': {'students.$.sections': sectionDoc}})
                        for s in newStudents])

                nStudents = _countPecaStudents(peca_actual.id)
                now = datetime.utcnow()
                PecaProject._get_collection().update_one(
                    {'_id': peca_actual.id},
                    {'$set': {'school.nStudents': nStudents, 'updatedAt': now}})
                SchoolUser._get_collection().update_one(
                    {'_id': schoolId},
                    {'$set': {'nStudents': nStudents, 'updatedAt': now}})
                updateSchoolYearStudents(schoolYear, nStudents)

                return {"status":201, "msg": "Estudiantes promovidos con exito"},201
            else:
                return {"status":400, "msg": "La sección no existe"},201
        except Exception as e:
            
            return {'status': 0, 'message': str(e)}, 400

class SectionsPromoteStudentService():
    def getSections(self, school_code):
        try:
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").only('id').first()
            schoolYearPrevius = _previousSchoolYear()
            peca_actual = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYear.id, school__code=school_code).only(*SECTION_FIELDS).first()
            peca_previus = PecaProject.objects(
                isDeleted=False,
                schoolYear=schoolYearPrevius.id, school__code=school_code).only(*SECTION_FIELDS).first()
            if peca_previus:
                if peca_actual:
                    sections_peca_actual = peca_actual.school.sections.filter(isDeleted=False)
                    sections_list_actual = []
                    for section in sections_peca_actual:
                        sections_list_actual.append({"id":str(section.id), "grade": section.grade, "name": section.name})

                    sections_peca_previus = peca_previus.school.sections.filter(isDeleted=False)
                    sections_list_previus = []
                    for section in sections_peca_previus:
                        sections_list_previus.append({"id":str(section.id), "grade": section.grade, "name": section.name})
                    
                    return {"status": 200, "section_previus": sections_list_previus, "section_current": sections_list_actual},200
                else:
                    return {"status": 400, "msg": "La escuela no tiene proyecto actual"},200
            else:
                return {"status": 400, "msg": "La escuela no tiene proyecto anterior"},200
                
        except Exception as e:
            
            return {'status': 0, 'message': str(e)}, 400        

class ChangeSectionStudentsService():
    def changeSection(self, data, pecaID):
        try:
            peca = PecaProject.objects(
                isDeleted=False,
                id=pecaID).first()
            if peca:
                school_code = peca.school.code
                school = SchoolUser.objects(code=school_code, isDeleted=False).first()
                section = peca.school.sections.filter(id=data["section_previus"]).first()
                if section:
                    section_new = peca.school.sections.filter(id=data["section_new"]).first()
                    if section_new:
                        school_students = {str(s.id): s for s in school.students}
                        for student in data["students"]:
                            st = section.students.filter(
                        isDeleted=False, id=student["id"]).first()
                            if not st:
                                continue
                            st.isDeleted = True
                            student_save = Student()
                            student_save.id = student["id"]
                            student_save.firstName = student["firstName"]
                            student_save.lastName = student["lastName"]
                            student_save.cardId = student["cardId"]
                            student_save.cardType = student["cardType"]
                            student_save.birthdate = student["birthdate"]
                            student_save.gender = student["gender"]
                            student_save.isDeleted = False
                            student_save.lapse1 = Diagnostic()
                            student_save.lapse2 = Diagnostic()
                            student_save.lapse3 = Diagnostic()

                            section_new.students.append(student_save)

                            student_school = school_students.get(str(student["id"]))
                            if student_school:
                                sections_currents = []
                                for sect in student_school.sections:
                                    if sect.id !=  section.id:
                                        sections_currents.append(sect)
                                
                                student_school.sections = sections_currents
                        
                                section_save = SectionClass()
                                section_save.name = section_new.name
                                section_save.grade = section_new.grade
                                section_save.isDeleted = False
                                section_save.schoolYear = peca.schoolYear
                                section_save.id = section_new.id

                                student_school.sections.append(section_save)
                        
                        nStudents = 0
                        for section in peca.school.sections.filter(isDeleted=False):
                            nStudents += len(section.students.filter(isDeleted=False))
                        peca.school.nStudents = nStudents
                        peca.save()
                        school.nStudents = nStudents
                        school.save()

                        schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
                        updateSchoolYearStudents(schoolYear, nStudents)

                        return {"status": 201, "msg": "Estudiantes cambiados con éxito"},201
                    else:
                        return {"status": 400, "msg": "No se encontro la sección nueva"},200
                
                else:
                    return {"status": 400, "msg": "No se encontro la sección anterior"},200
                    
            else:
                return {"status": 400, "msg": "No se encontro el proyecto"},200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

    def deleteStudentForSection(self, data, pecaId):
        try:
            peca = PecaProject.objects(
                isDeleted=False,
                id=pecaId).first()
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            
            if peca:
                school_code = peca.school.code
                school = SchoolUser.objects(code=school_code, isDeleted=False).first()
                section = peca.school.sections.filter(id=data["section"]).first()
                if section:
                    school_students = {str(s.id): s for s in school.students}
                    for student in data["students"]:
                        st = section.students.filter(
                    isDeleted=False, id=student["id"]).first()
                        if not st:
                            continue
                        st.isDeleted = True

                        student_school = school_students.get(str(student["id"]))
                        if student_school:
                            sections_currents = []
                            for sect in student_school.sections:
                                # _data evita desreferenciar SchoolYear (1 query por sección)
                                sect_year = sect._data.get('schoolYear')
                                sect_year_id = getattr(sect_year, 'id', sect_year)
                                if sect.id !=  section.id and sect_year_id != schoolYear.id:
                                    sections_currents.append(sect)
                                
                            student_school.sections = sections_currents
                    nStudents = 0
                    for section in peca.school.sections.filter(isDeleted=False):
                        nStudents += len(section.students.filter(isDeleted=False))
                    peca.school.nStudents = nStudents
                    
                    school.nStudents = nStudents
                            
                    peca.save()
                    school.save()

                    updateSchoolYearStudents(schoolYear, nStudents)

                    return {"status": 201, "msg": "Estudiantes eliminados con éxito"},201    
                else:
                    return {"status": 400, "msg": "No se encontro la sección"},200
            else:
                return {"status": 400, "msg": "No se encontro el proyecto"},200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400