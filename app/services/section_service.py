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
from app.models.peca_olympics_model import Section as OlympicsSection
from app.schemas.peca_student_schema import StudentSchema
from collections import OrderedDict
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


def count_diacritics(text):
    if not text:
        return 0
    return sum(1 for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) == "Mn")


# Partículas que se mantienen en minúscula cuando no son la primera palabra
# (ej. "María de los Ángeles", "Juan del Valle").
NAME_PARTICLES = {"de", "del", "la", "las", "los", "y", "e", "da", "di", "van", "von"}


def format_person_name(text):
    """
    Normaliza un nombre propio: colapsa espacios, pone en mayúscula la inicial de
    cada palabra (también tras guion o apóstrofo) y el resto en minúscula.
    Ej: "josé  GREGORIO de la cruz" -> "José Gregorio de la Cruz".
    """
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    words = []
    for idx, word in enumerate(text.split(" ")):
        lower = word.lower()
        if idx > 0 and lower in NAME_PARTICLES:
            words.append(lower)
            continue
        words.append(re.sub(
            r"(^|[-'’])(\w)",
            lambda m: m.group(1) + m.group(2).upper(),
            lower,
            flags=re.UNICODE
        ))
    return " ".join(words)


def sync_accented_names(target, first_name, last_name):
    """
    Actualiza firstName/lastName de un estudiante existente con el valor importado cuando:
      a) es el mismo nombre (comparación sin acentos/mayúsculas/espacios) pero difiere en
         acentos o capitalización. Ej: 'jose perez' -> 'José Pérez'.
      b) el importado completa al almacenado agregando nombres/apellidos al final.
         Ej: 'José' -> 'José Gregorio', 'Pérez' -> 'Pérez Rodríguez'.
    Nunca quita acentos ya guardados y no sobrescribe nombres distintos para no
    corromper registros emparejados por cédula o por fecha de nacimiento + similitud.
    """
    if target is None:
        return False
    changed = False
    for field, incoming in (("firstName", first_name), ("lastName", last_name)):
        incoming = re.sub(r"\s+", " ", incoming or "").strip()
        current = getattr(target, field, None) or ""
        if not incoming or incoming == current:
            continue
        inc_tokens = normalize_student_text(incoming).split(" ")
        cur_norm = normalize_student_text(current)
        cur_tokens = cur_norm.split(" ") if cur_norm else []
        same_name = inc_tokens == cur_tokens
        extends_name = len(inc_tokens) > len(cur_tokens) and inc_tokens[:len(cur_tokens)] == cur_tokens
        if (same_name or extends_name) and count_diacritics(incoming) >= count_diacritics(current):
            setattr(target, field, incoming)
            changed = True
    return changed


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
        full_s = "{0} {1}".format(n_s_fn, n_s_ln)
        full_t = "{0} {1}".format(n_t_fn, n_t_ln)
        if difflib.SequenceMatcher(None, full_s, full_t).ratio() >= 0.8:
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
            isDeleted=False, id=pecaId).only(
            'id', 'school', 'schoolYear', 'lapse1', 'lapse2', 'lapse3').first()

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
                                    section_list["students"].sort(
                                        key=lambda s: (
                                            normalize_student_text(s.get("lastName", "")),
                                            normalize_student_text(s.get("firstName", ""))
                                        )
                                    )
                                    sections_export.append(section_list)
                            return {"status_code":201, "message": "Exito", "sections": sections_export},201
                        else:
                            return {"status_code":404, "message": "Debe enviar secciones a exportar"},201

                    if jsonData["action"] == "import":
                        if ("section" in jsonData) and ("students" in jsonData):    
                            section_peca = peca.school.sections.filter(isDeleted=False, id=jsonData["section"]).first()
                            if section_peca:
                                if len(jsonData["students"]) > 0:
                                    placed = dict(
                                        (student_id, str(section_peca.id)) for student_id in
                                        self._importStudentsIntoSection(peca, school, section_peca, jsonData["students"]))
                                    moved = self._finishImport(peca, school, placed)

                                    return {"status_code": 201, "message": "Estudiantes importados con éxito", "moved": moved}, 201                
                                else:
                                    return {"status_code":400, "message": "No se ha recibido data para importar"},201
                            else:
                                return {"status_code":404, "message": "Debe enviar una sección válida a importar"},201

                        else:
                            return {"status_code":404, "message": "Debe enviar una sección a importar"},201

                    if jsonData["action"] == "import_multiple":
                        # Cada estudiante trae el id de su sección; se agrupan por sección y se
                        # persiste una sola vez para que la carga sea todo o nada.
                        students = jsonData.get("students") or []
                        if not isinstance(students, list) or len(students) == 0:
                            return {"status_code": 400, "message": "No se ha recibido data para importar"}, 400

                        active_sections = dict(
                            (str(s.id), s) for s in peca.school.sections.filter(isDeleted=False))
                        grouped = OrderedDict()
                        errors = []
                        for idx, student in enumerate(students):
                            section_id = str(student.get("section") or "") if isinstance(student, dict) else ""
                            if section_id not in active_sections:
                                row = student.get("fila") if isinstance(student, dict) else None
                                errors.append("Fila {}: el grado y la sección no están registrados en el año escolar".format(
                                    row if row else idx + 1))
                                continue
                            grouped.setdefault(section_id, []).append(student)

                        if errors:
                            return {"status_code": 400, "message": "Hay estudiantes con grado o sección no registrados", "errors": errors}, 400

                        placed = {}
                        for section_id, section_students in grouped.items():
                            for student_id in self._importStudentsIntoSection(
                                    peca, school, active_sections[section_id], section_students):
                                placed[student_id] = section_id
                        moved = self._finishImport(peca, school, placed)

                        return {"status_code": 201, "message": "Estudiantes importados con éxito",
                                "sections": len(grouped), "students": len(students), "moved": moved}, 201

                else:
                    raise RegisterNotFound(message="Debe escoger una acción a realizar",
                                   status_code=404)
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"recordId": pecaId})

    def _importStudentsIntoSection(self, peca, school, section_peca, students):
        """Empareja/agrega en memoria los estudiantes del Excel a una sección; no persiste."""
        # Emparejamiento estricto (sin similitud difusa de nombres: confundía
        # hermanos/gemelos con mismo apellido y fecha de nacimiento):
        #   1. Misma cédula -> mismo estudiante; nombre, fecha y género se toman
        #      del Excel salvo que el nombre pertenezca a otro estudiante.
        #   2. Mismo nombre + apellido + fecha de nacimiento + género -> mismo
        #      estudiante aunque la cédula difiera (corrección de cédula).
        #   3. Mismo nombre + apellido sin cédulas contradictorias -> mismo
        #      estudiante (corrección de fecha de nacimiento/género).
        #   Cualquier otro caso -> estudiante nuevo.
        # Un estudiante ya emparejado por una fila previa del mismo Excel solo
        # puede volver a emparejarse con una fila de igual nombre (fila repetida);
        # así una cédula repetida por error entre gemelos no sobrescribe al primero.
        claimed_ids = set()

        def claim(s):
            if s is not None and s.id:
                claimed_ids.add(str(s.id))

        def is_blocked(s, key):
            return bool(s.id) and str(s.id) in claimed_ids and name_key(s.firstName, s.lastName) != key

        def name_key(first_name, last_name):
            fn = normalize_student_text(first_name).replace(" ", "")
            ln = normalize_student_text(last_name).replace(" ", "")
            return (fn, ln) if fn and ln else None

        def bd_key(birthdate):
            return (birthdate.year, birthdate.month, birthdate.day) if birthdate else None

        def register_in_index(s, by_card, by_name, overwrite_card=True):
            c = str(s.cardId or "").strip()
            if c and (overwrite_card or c not in by_card):
                by_card[c] = s
            k = name_key(s.firstName, s.lastName)
            if k:
                by_name.setdefault(k, []).append(s)

        def reindex_card(s, old_card, new_card, by_card):
            if old_card and by_card.get(old_card) is s:
                del by_card[old_card]
            if new_card:
                by_card[new_card] = s

        def reindex_name(s, old_key, new_key, by_name):
            if old_key in by_name:
                by_name[old_key] = [c for c in by_name[old_key] if c is not s]
            if new_key:
                by_name.setdefault(new_key, []).append(s)

        def find_in_index(card_id, key, bd_tuple, gender, by_card, by_name):
            if card_id and card_id in by_card and not is_blocked(by_card[card_id], key):
                return by_card[card_id]
            candidates = [c for c in (by_name.get(key, []) if key else []) if not is_blocked(c, key)]
            for cand in candidates:
                if bd_key(cand.birthdate) == bd_tuple and cand.gender == gender:
                    return cand
            for cand in candidates:
                cand_card = str(cand.cardId or "").strip()
                if not (card_id and cand_card and cand_card != card_id):
                    return cand
            return None

        def name_taken_by_other(key, student_id, card_id):
            # El nombre pertenece a otro estudiante si está activo en esta sección
            # o, en la escuela, tiene otra cédula. Registros de escuela sin cédula
            # (duplicados de años previos) no bloquean.
            for c in sec_by_name.get(key, []):
                if str(c.id) != str(student_id) and not getattr(c, "isDeleted", False):
                    return True
            for c in school_by_name.get(key, []):
                other_card = str(c.cardId or "").strip()
                if (str(c.id) != str(student_id) and not getattr(c, "isDeleted", False)
                        and other_card and other_card != card_id):
                    return True
            return False

        def can_rename(target, key, card_id):
            # Con la misma cédula, el nombre del Excel prevalece salvo que pertenezca
            # a otro estudiante (gemelos o cédula repetida por error).
            if target is None or not key or name_key(target.firstName, target.lastName) == key:
                return False
            return not name_taken_by_other(key, target.id, card_id)

        def apply_corrections(target, key, first_name, last_name, rename,
                              card_id, card_type, birthdate, gender, by_card, by_name):
            # Cédula: se actualiza siempre que venga en el Excel.
            # Nombre: solo si can_rename() lo autorizó.
            # Fecha/género: solo si el nombre coincide, para no pisar datos de otro
            # estudiante cuando una cédula mal tipeada choca con la de un hermano.
            if target is None:
                return
            old_card = str(target.cardId or "").strip()
            if card_id and card_id != old_card:
                target.cardId = card_id
                target.cardType = card_type
                reindex_card(target, old_card, card_id, by_card)
            elif card_id:
                target.cardType = card_type
            if rename:
                old_key = name_key(target.firstName, target.lastName)
                target.firstName = first_name
                target.lastName = last_name
                reindex_name(target, old_key, key, by_name)
            if name_key(target.firstName, target.lastName) == key:
                if birthdate:
                    target.birthdate = birthdate
                if gender:
                    target.gender = gender

        # 1. Pre-index section students
        sec_by_card = {}
        sec_by_name = {}
        for s in section_peca.students:
            register_in_index(s, sec_by_card, sec_by_name)

        # 2. Pre-index school students
        school_by_id = {}
        school_by_card = {}
        school_by_name = {}
        for s in school.students:
            school_by_id[str(s.id)] = s
            if getattr(s, "isDeleted", False):
                continue
            register_in_index(s, school_by_card, school_by_name, overwrite_card=False)

        schema = StudentSchema()

        for student in students:
            if not (student.get("nombre") and student.get("apellido") and student.get("fecha_de_nacimiento") and student.get("genero")):
                continue

            student["nombre"] = format_person_name(student["nombre"])
            student["apellido"] = format_person_name(student["apellido"])

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

            key = name_key(student["nombre"], student["apellido"])
            bd_tuple = bd_key(parsed_date)

            # Check section
            student_in_section = find_in_index(
                clean_doc, key, bd_tuple, student["genero"],
                sec_by_card, sec_by_name
            )

            # Check school
            student_find = None
            if student_in_section:
                student_find = school_by_id.get(str(student_in_section.id))
            if not student_find:
                student_find = find_in_index(
                    clean_doc, key, bd_tuple, student["genero"],
                    school_by_card, school_by_name
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
                sync_accented_names(student_in_section, student["nombre"], student["apellido"])
                sync_accented_names(student_find, student["nombre"], student["apellido"])
                rename = can_rename(student_in_section, key, clean_doc)
                apply_corrections(student_in_section, key, student["nombre"], student["apellido"], rename,
                                  clean_doc, student_format["cardType"],
                                  data["birthdate"], student["genero"], sec_by_card, sec_by_name)
                apply_corrections(student_find, key, student["nombre"], student["apellido"], rename,
                                  clean_doc, student_format["cardType"],
                                  data["birthdate"], student["genero"], school_by_card, school_by_name)
                claim(student_in_section)
            elif student_find:
                # Existing student in school, add to section
                sync_accented_names(student_find, student["nombre"], student["apellido"])
                rename = can_rename(student_find, key, clean_doc)
                apply_corrections(student_find, key, student["nombre"], student["apellido"], rename,
                                  clean_doc, student_format["cardType"],
                                  data["birthdate"], student["genero"], school_by_card, school_by_name)
                # La copia en la sección refleja el registro de escuela ya corregido.
                student_save.id = student_find.id
                for field in ("firstName", "lastName", "cardId", "cardType", "birthdate", "gender"):
                    student_save[field] = getattr(student_find, field)

                section_peca.students.append(student_save)
                register_in_index(student_save, sec_by_card, sec_by_name)
                claim(student_save)

                has_sec = False
                for sect in student_find.sections:
                    sect_sy = getattr(sect, 'schoolYear', None)
                    sect_sy_id = getattr(sect_sy, 'id', sect_sy) if sect_sy else None
                    peca_sy_id = getattr(peca.schoolYear, 'id', peca.schoolYear) if getattr(peca, 'schoolYear', None) else None
                    if str(sect.id) == str(section_peca.id) and sect_sy_id and str(sect_sy_id) == str(peca_sy_id):
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
                register_in_index(student_save, sec_by_card, sec_by_name)

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
                register_in_index(student_class, school_by_card, school_by_name)
                claim(student_save)

        # Ids de los estudiantes que quedaron en la sección por este Excel
        return claimed_ids

    def _moveFromOtherSections(self, peca, school, placed):
        """
        Deja a cada estudiante solo en la sección indicada por el Excel: lo da de baja en las
        demás secciones del PECA, conserva sus diagnósticos (recalculando índices con las metas
        del grado destino) y actualiza la sección en olimpíadas e historial de la escuela.
        placed: {studentId: sectionId destino}. Retorna (movidos, hubo diagnósticos movidos).
        """
        sections = dict((str(s.id), s) for s in peca.school.sections.filter(isDeleted=False))
        goalSetting = None
        if peca.schoolYear:
            schoolYear = peca.schoolYear.fetch()
            goalSetting = schoolYear.pecaSetting.goalSetting if schoolYear.pecaSetting else None

        # Diagnóstico -> fecha en que se registró
        diagnosticDates = [('multiplicationsPerMin', 'mathDate'),
                           ('operationsPerMin', 'logicDate'),
                           ('wordsPerMin', 'readingDate')]

        def mergeDiagnostics(student, targetStudent, setting):
            """
            Trae a la copia destino cada diagnóstico (por lapso y materia) de la copia anterior.
            El destino solo conserva el suyo si es más reciente: puede ser una copia revivida
            de una sección donde el estudiante estuvo antes, con datos viejos. El 0 es un
            diagnóstico válido. La copia anterior queda sin diagnósticos, igual que al eliminar.
            Retorna si hubo cambios.
            """
            changed = False
            for i in [1, 2, 3]:
                lapse = 'lapse{}'.format(i)
                source = student[lapse]
                if source is None:
                    continue
                target = targetStudent[lapse]
                if target is None:
                    target = targetStudent[lapse] = Diagnostic()
                for diag, dateField in diagnosticDates:
                    if source[diag] is None:
                        continue
                    targetDate = target[dateField]
                    targetIsNewer = target[diag] is not None and targetDate is not None and (
                        source[dateField] is None or targetDate > source[dateField])
                    if not targetIsNewer:
                        target[diag] = source[diag]
                        target[dateField] = source[dateField]
                    source[diag] = None
                    source['{}Index'.format(diag)] = None
                    source[dateField] = None
                    changed = True
                if changed and setting:
                    target.calculateIndex(setting)
            return changed

        moved = {}  # studentId -> (sección anterior, sección destino)
        movedDiagnostics = False
        for sectionId, section in sections.items():
            for student in section.students:
                targetId = placed.get(str(student.id))
                if student.isDeleted or not targetId or targetId == sectionId or targetId not in sections:
                    continue
                target = sections[targetId]
                targetStudent = target.students.filter(isDeleted=False, id=student.id).first()
                if targetStudent:
                    setting = goalSetting['grade{}'.format(target.grade)] if goalSetting else None
                    if mergeDiagnostics(student, targetStudent, setting):
                        movedDiagnostics = True
                student.isDeleted = True
                moved[str(student.id)] = (section, target)

        if not moved:
            return 0, False

        # Olimpíadas: la inscripción sigue al estudiante a su nueva sección
        for i in [1, 2, 3]:
            lapse = peca['lapse{}'.format(i)]
            if lapse is None:
                continue
            for olympics in [lapse.olympics, lapse.readingOlympics]:
                if olympics is None:
                    continue
                for enrolled in olympics.students:
                    if str(enrolled.id) in moved:
                        target = moved[str(enrolled.id)][1]
                        enrolled.section = OlympicsSection(
                            id=str(target.id), name=target.name, grade=target.grade)

        # Historial en la escuela: se quita la sección anterior (igual que al eliminar)
        for studentId, (previous, _) in moved.items():
            schoolStudent = school.students.filter(id=studentId).first()
            if schoolStudent:
                schoolStudent.sections = [
                    s for s in schoolStudent.sections if str(s.id) != str(previous.id)]

        if movedDiagnostics:
            for section in sections.values():
                section.refreshDiagnosticsSummary()
            peca.school.refreshDiagnosticsSummary()

        return len(moved), movedDiagnostics

    def _finishImport(self, peca, school, placed):
        """Mueve a los estudiantes a la sección del Excel, persiste y refresca el año escolar."""
        moved, movedDiagnostics = self._moveFromOtherSections(peca, school, placed)
        self._persistImport(peca, school)
        if movedDiagnostics:
            schoolYear = peca.schoolYear.fetch()
            schoolYear.refreshDiagnosticsSummary()
            schoolYear.save()
        return moved

    def _persistImport(self, peca, school):
        """Recalcula nStudents y guarda peca, escuela y año escolar en un solo paso."""
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
