# app/services/activity_service.py


from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_project_model import Section
from app.schemas.peca_project_schema import SectionSchema
from app.helpers.error_helpers import RegisterNotFound


class SectionService():

    def save(self, pecaId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).first()

        if peca:
            try:
                schema = SectionSchema()
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
                    peca.school.sections.append(section)
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
        ).only('school__sections').first()

        if peca:
            try:
                schema = SectionSchema()
                data = schema.load(jsonData)

                section = peca.school.sections.filter(
                    id=sectionId, isDeleted=False).first()

                for field in schema.dump(data).keys():
                    section[field] = data[field]
                if self.checkForDuplicated(peca, section):
                    raise ValidationError(
                        {"name": [{"status": "5",
                                   "msg": "Duplicated record found: {}".format(section.name)}]}
                    )
                try:
                    PecaProject.objects(
                        id=pecaId,
                        school__sections__id=sectionId
                    ).update(set__school__sections__S=section)
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
        ).only('school__sections').first()

        if peca:
            try:

                section = peca.school.sections.filter(id=sectionId).first()
                section.isDeleted = True
                try:
                    PecaProject.objects(
                        id=pecaId,
                        school__sections__id=sectionId
                    ).update(set__school__sections__S=section)
                    return "Record deleted successfully", 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
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
