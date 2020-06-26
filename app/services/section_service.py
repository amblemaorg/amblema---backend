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


class SectionService():

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
                                   payload={"pecaId": pecaId, "sectionId": sectionId})

    def delete(self, pecaId, sectionId):
        """
        Delete (change isDeleted to True) a record
        """

        peca = PecaProject.objects.filter(
            id=pecaId,
            school__sections__id=sectionId,
            school__sections__isDeleted=False
        ).first()

        if peca:

            try:
                for oldSection in peca.school.sections:
                    if str(oldSection.id) == sectionId:
                        oldSection.isDeleted = True
                for i in range(1, 4):
                    if peca['lapse{}'.format(i)].ambleCoins:
                        for oldSection in peca['lapse{}'.format(i)].ambleCoins.sections:
                            if oldSection.id == sectionId:
                                peca['lapse{}'.format(i)].ambleCoins.sections.remove(
                                    oldSection)
                peca.save()
                return "Record deleted successfully", 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId, "sectionId": sectionId})

    def checkForDuplicated(self, peca, newSection):
        section = PecaProject.objects.filter(
            id=peca.id,
            school__sections__isDeleted=False,
            school__sections__grade=newSection.grade,
            school__sections__name=newSection.name
        ).only('id').first()
        if section:
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
