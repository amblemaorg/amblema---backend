# app/services/section_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_section_model import Section
from app.models.peca_amblecoins_model import AmbleSection
from app.schemas.peca_school_schema import SectionSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser
from app.models.school_year_model import SchoolYear
from app.helpers.handler_messages import HandlerMessages
from app.models.peca_student_model import SectionClass, Student, Diagnostic, StudentClass
from app.schemas.peca_student_schema import StudentSchema
from datetime import datetime
import re
import unicodedata
import difflib


def normalize_student_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip().lower()


def is_same_student_record(s_fn, s_ln, s_bd, s_gen, s_card, t_fn, t_ln, t_bd, t_gen, t_card):
    # 1. Direct match by cardId if both are non-empty
    if s_card and t_card and str(s_card).strip() and str(t_card).strip():
        if str(s_card).strip() == str(t_card).strip():
            return True

    n_s_fn = normalize_student_text(s_fn)
    n_t_fn = normalize_student_text(t_fn)
    n_s_ln = normalize_student_text(s_ln)
    n_t_ln = normalize_student_text(t_ln)

    # 2. Exact match on normalized first and last names
    if n_s_fn and n_t_fn and n_s_fn == n_t_fn and n_s_ln == n_t_ln:
        return True

    # 3. Match ignoring spaces in names (e.g. JulietaAlejandra vs Julieta Alejandra)
    if n_s_fn and n_t_fn and n_s_fn.replace(" ", "") == n_t_fn.replace(" ", "") and n_s_ln.replace(" ", "") == n_t_ln.replace(" ", ""):
        return True

    # 4. Same birthdate (day, month, year) + same lastName + similar firstName
    same_bd = False
    if s_bd and t_bd:
        try:
            same_bd = ((s_bd.year, s_bd.month, s_bd.day) == (t_bd.year, t_bd.month, t_bd.day))
        except Exception:
            pass

    if same_bd and (n_s_ln == n_t_ln or n_s_ln.replace(" ", "") == n_t_ln.replace(" ", "")):
        if difflib.SequenceMatcher(None, n_s_fn, n_t_fn).ratio() >= 0.65:
            return True

    # 5. Same birthdate + high full name similarity
    if same_bd:
        if difflib.SequenceMatcher(None, f"{n_s_fn} {n_s_ln}", f"{n_t_fn} {n_t_ln}").ratio() >= 0.8:
            return True

    return False


class SectionService():

    handlerMessages = HandlerMessages()

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                school = SchoolUser.objects(
                    id=peca.project.school.id, isDeleted=False).first()
                schema = SectionSchema()
                if "teacher" in jsonData:

                    teacher = school.teachers.filter(
                        id=jsonData['teacher'], isDeleted=False).first()
                    if not teacher:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"teacher": jsonData['teacher']})
                    else:
                        jsonData['teacher'] = {
                            'id': str(teacher.id),
                            'firstName': teacher.firstName,
                            'lastName': teacher.lastName
                        }
                data = schema.load(jsonData)

                section = Section()
                for field in schema.dump(data).keys():
                    section[field] = data[field]
                if self.checkForDuplicated(peca, section):
                    raise ValidationError(
                        {"name": [{"status": "5",
                                   "msg": "Duplicated record found: {}".format(section.name)}]}
                    )
                try:
                    schoolYear = peca.schoolYear.fetch()
                    if section.grade != "0":
                        section.goals = schoolYear.pecaSetting.goalSetting['grade{}'.format(
                            section.grade)]
                    peca.school.sections.append(section)

                    for i in range(1, 4):
                        if peca['lapse{}'.format(i)].ambleCoins:
                            peca['lapse{}'.format(i)].ambleCoins.sections.append(
                                AmbleSection(
                                    id=str(section.id),
                                    name=section.name,
                                    grade=section.grade
                                )
                            )
                    peca.school.nSections += 1
                    grades = []
                    for section in peca.school.sections:
                        if section.grade not in grades:
                            grades.append(section.grade)
                    peca.school.nGrades = len(grades)
                    school.nSections = peca.school.nSections
                    school.nGrades = peca.school.nGrades
                    school.save()

                    peca.save()
                    return schema.dump(section), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def update(self, pecaId, sectionId, jsonData):

        peca = PecaProject.objects.filter(
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False
        ).first()

        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if sectionId:
                try:
                    schema = SectionSchema()
                    school = SchoolUser.objects(
                        id=peca.project.school.id, isDeleted=False).first()
                    if "teacher" in jsonData:
                        teacher = school.teachers.filter(
                            id=jsonData['teacher'], isDeleted=False).first()
                        if not teacher:
                            raise RegisterNotFound(message="Record not found",
                                                   status_code=404,
                                                   payload={"teacher": jsonData['teacher']})
                        else:
                            jsonData['teacher'] = {
                                'id': str(teacher.id),
                                'firstName': teacher.firstName,
                                'lastName': teacher.lastName
                            }
                    data = schema.load(jsonData)

                    section = peca.school.sections.filter(
                        id=sectionId, isDeleted=False).first()

                    for field in schema.dump(data).keys():
                        if section[field] != data[field]:
                            section[field] = data[field]
                            if field == 'grade':
                                section.goals = peca.schoolYear.fetch(
                                ).pecaSetting.goalSetting['grade{}'.format(section.grade)]
                    if self.checkForDuplicated(peca, section):
                        raise ValidationError(
                            {"name": [{"status": "5",
                                       "msg": "Duplicated record found: {}".format(section.name)}]}
                        )
                    try:
                        for oldSection in peca.school.sections:
                            if str(oldSection.id) == sectionId:
                                oldSection = section
                        for i in range(1, 4):
                            if peca['lapse{}'.format(i)].ambleCoins:
                                for oldSection in peca['lapse{}'.format(i)].ambleCoins.sections:
                                    if oldSection.id == sectionId:
                                        oldSection.name = section.name
                                        oldSection.grade = section.grade
                        peca.save()
                        return schema.dump(section), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

                except ValidationError as err:
                    return err.normalized_messages(), 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"sectionId": sectionId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def delete(self, pecaId, sectionId):
        """
        Delete (change isDeleted to True) a record
        """

        peca = PecaProject.objects.filter(
            id=pecaId,
            isDeleted=False
        ).first()

        if peca:
            section = peca.school.sections.filter(
                isDeleted=False, id=sectionId).first()
            if section:
                school = SchoolUser.objects(
                    id=peca.project.school.id, isDeleted=False).first()

                students = section.students.filter(isDeleted=False)
                if students:
                    return {
                        'status': '0',
                        'entity': 'Student',
                        'msg': self.handlerMessages.getDeleteEntityMsg('Student')
                    }, 419

                try:
                    section.isDeleted = True

                    for i in range(1, 4):
                        if peca['lapse{}'.format(i)].ambleCoins:
                            for oldSection in peca['lapse{}'.format(i)].ambleCoins.sections:
                                if oldSection.id == sectionId:
                                    peca['lapse{}'.format(i)].ambleCoins.sections.remove(
                                        oldSection)
                    peca.school.nSections -= 1
                    grades = []
                    for section in peca.school.sections:
                        if section.grade not in grades:
                            grades.append(section.grade)
                    peca.school.nGrades = len(grades)
                    peca.save()
                    school.nSections = peca.school.nSections
                    school.nGrades = peca.school.nGrades
                    school.save()
                    return "Record deleted successfully", 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"sectionId": sectionId})
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def checkForDuplicated(self, peca, newSection):

        for section in peca.school.sections.filter(isDeleted=False):
            if section.id != newSection.id and section.grade == newSection.grade and section.name == newSection.name:
                return True
        return False

        """
        section = PecaProject.objects.filter(
            id=peca.id,
            school__sections__isDeleted=False,
            school__sections__grade=newSection.grade,
            school__sections__name=newSection.name
        ).fields(id=1, school__sections={'$elemMatch': {'name': newSection.name, 'grade': newSection.grade}}).first()
        if section:
            return True
        return False
        """
class SectionsImportExport():
    handlerMessages = HandlerMessages()
    def loadSections(self, pecaId, jsonData):
        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).only('id', 'school', 'schoolYear').first()

        if peca:
            try:
                school_code = peca.school.code
                school = SchoolUser.objects(code=school_code, isDeleted=False).first()
                
                if "action" in jsonData:
                    if  jsonData["action"] == "export":
                        if "sections" in jsonData:
                            sections_export = []
                            for section in jsonData["sections"]:
                                section_peca = peca.school.sections.filter(isDeleted=False, id=section).first()
                                if section_peca:
                                    section_list = {"name": section_peca.name, "grade": section_peca.grade, "id": str(section_peca.id), "students": []}
                                    for student in section_peca.students.filter(isDeleted=False):
                                        section_list["students"].append({"id":str(student.id), "firstName": student.firstName, "lastName": student.lastName, "cardId": student.cardId, "cardType": student.cardType, "birthdate": str(student.birthdate), "gender": student.gender})
                                    sections_export.append(section_list)
                            return {"status_code":201, "message": "Exito", "sections": sections_export},201
                        else:
                            return {"status_code":404, "message": "Debe enviar secciones a exportar"},201

                    if jsonData["action"] == "import":
                        if ("section" in jsonData) and ("students" in jsonData):    
                            section_peca = peca.school.sections.filter(isDeleted=False, id=jsonData["section"]).first()
                            if section_peca:
                                if len(jsonData["students"]) > 0:
                                    # 1. Pre-index section students
                                    sec_by_card = {}
                                    sec_by_norm = {}
                                    sec_by_clean = {}
                                    sec_by_bd_ln = {}

                                    for s in section_peca.students:
                                        c = str(s.cardId or "").strip()
                                        if c:
                                            sec_by_card[c] = s
                                        fn = normalize_student_text(s.firstName)
                                        ln = normalize_student_text(s.lastName)
                                        if fn and ln:
                                            sec_by_norm[(fn, ln)] = s
                                            sec_by_clean[(fn.replace(" ", ""), ln.replace(" ", ""))] = s
                                        if s.birthdate and ln:
                                            bd = (s.birthdate.year, s.birthdate.month, s.birthdate.day)
                                            sec_by_bd_ln.setdefault((bd, ln), []).append((fn, s))

                                    # 2. Pre-index school students
                                    school_by_id = {}
                                    school_by_card = {}
                                    school_by_norm = {}
                                    school_by_clean = {}
                                    school_by_bd_ln = {}

                                    for s in school.students:
                                        school_by_id[str(s.id)] = s
                                        if getattr(s, "isDeleted", False):
                                            continue
                                        c = str(s.cardId or "").strip()
                                        if c and c not in school_by_card:
                                            school_by_card[c] = s
                                        fn = normalize_student_text(s.firstName)
                                        ln = normalize_student_text(s.lastName)
                                        if fn and ln:
                                            if (fn, ln) not in school_by_norm:
                                                school_by_norm[(fn, ln)] = s
                                            clean_key = (fn.replace(" ", ""), ln.replace(" ", ""))
                                            if clean_key not in school_by_clean:
                                                school_by_clean[clean_key] = s
                                        if s.birthdate and ln:
                                            bd = (s.birthdate.year, s.birthdate.month, s.birthdate.day)
                                            school_by_bd_ln.setdefault((bd, ln), []).append((fn, s))

                                    def find_in_index(card_id, norm_fn, norm_ln, bd_tuple, by_card, by_norm, by_clean, by_bd_ln):
                                        if card_id and card_id in by_card:
                                            return by_card[card_id]
                                        if norm_fn and norm_ln:
                                            if (norm_fn, norm_ln) in by_norm:
                                                return by_norm[(norm_fn, norm_ln)]
                                            clean_k = (norm_fn.replace(" ", ""), norm_ln.replace(" ", ""))
                                            if clean_k in by_clean:
                                                return by_clean[clean_k]
                                        if bd_tuple and norm_ln and (bd_tuple, norm_ln) in by_bd_ln:
                                            candidates = by_bd_ln[(bd_tuple, norm_ln)]
                                            for cand_fn, cand_s in candidates:
                                                if difflib.SequenceMatcher(None, norm_fn, cand_fn).ratio() >= 0.65:
                                                    return cand_s
                                        return None

                                    def register_in_index(s, by_card, by_norm, by_clean, by_bd_ln):
                                        c = str(s.cardId or "").strip()
                                        if c:
                                            by_card[c] = s
                                        fn = normalize_student_text(s.firstName)
                                        ln = normalize_student_text(s.lastName)
                                        if fn and ln:
                                            by_norm[(fn, ln)] = s
                                            by_clean[(fn.replace(" ", ""), ln.replace(" ", ""))] = s
                                        if s.birthdate and ln:
                                            bd = (s.birthdate.year, s.birthdate.month, s.birthdate.day)
                                            by_bd_ln.setdefault((bd, ln), []).append((fn, s))

                                    schema = StudentSchema()

                                    for student in jsonData["students"]:
                                        if not (student.get("nombre") and student.get("apellido") and student.get("fecha_de_nacimiento") and student.get("genero")):
                                            continue

                                        gen = str(student["genero"]).strip().upper()
                                        student["genero"] = "1" if gen in ["F", "1", "FEMENINO"] else "2"

                                        tipo = str(student.get("tipo_de_documento", "")).strip().upper()
                                        raw_doc = str(student.get("documento_de_identidad", "")).strip()
                                        doc_match = re.match(r'^([VEve])[-–—\s]?(.*)$', raw_doc)
                                        if doc_match:
                                            if not tipo:
                                                tipo = doc_match.group(1).upper()
                                            raw_doc = doc_match.group(2)
                                        clean_doc = re.sub(r'\D', '', raw_doc)
                                        student["tipo_de_documento"] = "2" if tipo in ["2", "E", "EXTRANJERO"] else "1"
                                        student["documento_de_identidad"] = clean_doc

                                        birthdate_str = str(student["fecha_de_nacimiento"]).strip()
                                        parsed_date = None
                                        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
                                            try:
                                                parsed_date = datetime.strptime(birthdate_str, fmt)
                                                break
                                            except ValueError:
                                                pass
                                        if parsed_date:
                                            student["fecha_de_nacimiento"] = parsed_date.strftime("%Y-%m-%d") + "T00:00:00.000Z"

                                        norm_fn = normalize_student_text(student["nombre"])
                                        norm_ln = normalize_student_text(student["apellido"])
                                        bd_tuple = (parsed_date.year, parsed_date.month, parsed_date.day) if parsed_date else None

                                        # Check section
                                        student_in_section = find_in_index(
                                            clean_doc, norm_fn, norm_ln, bd_tuple,
                                            sec_by_card, sec_by_norm, sec_by_clean, sec_by_bd_ln
                                        )

                                        # Check school
                                        student_find = None
                                        if student_in_section:
                                            student_find = school_by_id.get(str(student_in_section.id))
                                        if not student_find:
                                            student_find = find_in_index(
                                                clean_doc, norm_fn, norm_ln, bd_tuple,
                                                school_by_card, school_by_norm, school_by_clean, school_by_bd_ln
                                            )

                                        student_format = {
                                            "firstName": student["nombre"],
                                            "lastName": student["apellido"],
                                            "cardId": clean_doc,
                                            "cardType": student["tipo_de_documento"],
                                            "birthdate": student.get("fecha_de_nacimiento", ""),
                                            "gender": student["genero"]
                                        }

                                        data = schema.load(student_format)
                                        student_save = Student()
                                        for field in schema.dump(data).keys():
                                            student_save[field] = data[field]
                                        for i in range(3):
                                            student_save['lapse{}'.format(i+1)] = Diagnostic()

                                        if student_in_section:
                                            # Existing student in section
                                            if getattr(student_in_section, "isDeleted", False):
                                                student_in_section.isDeleted = False
                                            if clean_doc:
                                                student_in_section.cardId = clean_doc
                                                student_in_section.cardType = student_format["cardType"]
                                                if student_find:
                                                    student_find.cardId = clean_doc
                                                    student_find.cardType = student_format["cardType"]
                                        elif student_find:
                                            # Existing student in school, add to section
                                            student_save.id = student_find.id
                                            if clean_doc:
                                                student_find.cardId = clean_doc
                                                student_find.cardType = student_format["cardType"]
                                                student_save.cardId = clean_doc
                                                student_save.cardType = student_format["cardType"]

                                            section_peca.students.append(student_save)
                                            register_in_index(student_save, sec_by_card, sec_by_norm, sec_by_clean, sec_by_bd_ln)

                                            has_sec = False
                                            for sect in student_find.sections:
                                                if str(sect.id) == str(section_peca.id) and getattr(sect, 'schoolYear', None) and str(sect.schoolYear.id) == str(peca.schoolYear.id):
                                                    has_sec = True
                                                    break
                                            if not has_sec:
                                                section_save = SectionClass(
                                                    id=section_peca.id,
                                                    name=section_peca.name,
                                                    grade=section_peca.grade,
                                                    isDeleted=False,
                                                    schoolYear=peca.schoolYear.id
                                                )
                                                student_find.sections.append(section_save)
                                        else:
                                            # Brand new student
                                            section_save = SectionClass(
                                                id=section_peca.id,
                                                name=section_peca.name,
                                                grade=section_peca.grade,
                                                isDeleted=False,
                                                schoolYear=peca.schoolYear.id
                                            )
                                            section_peca.students.append(student_save)
                                            register_in_index(student_save, sec_by_card, sec_by_norm, sec_by_clean, sec_by_bd_ln)

                                            student_class = StudentClass(
                                                id=student_save.id,
                                                firstName=student_save.firstName,
                                                lastName=student_save.lastName,
                                                cardId=student_save.cardId,
                                                cardType=student_save.cardType,
                                                birthdate=student_save.birthdate,
                                                gender=student_save.gender,
                                                isDeleted=False,
                                                sections=[section_save]
                                            )
                                            school.students.append(student_class)
                                            school_by_id[str(student_class.id)] = student_class
                                            register_in_index(student_class, school_by_card, school_by_norm, school_by_clean, school_by_bd_ln)

                                    # Single batch persistence for peca and school
                                    nStudents = sum(len(s.students.filter(isDeleted=False)) for s in peca.school.sections.filter(isDeleted=False))
                                    peca.school.nStudents = nStudents
                                    peca._mark_as_changed('school')
                                    peca.save()

                                    school.nStudents = nStudents
                                    school._mark_as_changed('students')
                                    school.save()

                                    # Fast MongoDB aggregation for schoolYear.nStudents
                                    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
                                    if schoolYear:
                                        pipeline = [
                                            {"$match": {"schoolYear": schoolYear.id, "isDeleted": False}},
                                            {"$group": {"_id": None, "total": {"$sum": "$school.nStudents"}}}
                                        ]
                                        agg_res = [doc for doc in PecaProject._get_collection().aggregate(pipeline)]
                                        schoolYear.nStudents = agg_res[0]["total"] if agg_res else nStudents
                                        schoolYear.save()

                                    return {"status_code": 201, "message": "Estudiantes importados con éxito"}, 201                
                                else:
                                    return {"status_code":400, "message": "No se ha recibido data para importar"},201
                            else:
                                return {"status_code":404, "message": "Debe enviar una sección válida a importar"},201

                        else:
                            return {"status_code":404, "message": "Debe enviar una sección a importar"},201

                else:
                    raise RegisterNotFound(message="Debe escoger una acción a realizar",
                                   status_code=404)
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def checkForDuplicated(self, section, newStudent):
        for s in section.students.filter(isDeleted=False):
            if s.id and newStudent.id and s.id == newStudent.id:
                return True
            if is_same_student_record(
                s.firstName, s.lastName, s.birthdate, s.gender, s.cardId,
                newStudent.firstName, newStudent.lastName, newStudent.birthdate, newStudent.gender, newStudent.cardId
            ):
                return True
        return False
