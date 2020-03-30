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
                    peca.school.append(section)
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

    def checkForDuplicated(self, peca, newSection):
        section = PecaProject.objects.filter(
            id=peca.id,
            school__sections__isDeleted=False,
            school__sections__grade=newSection.grade,
            school__sections__name=newSection.name
        ).fields(school__sections={'$elemMatch': {'name': newSection.name, 'grade': newSection.grade}})
        if section:
            return True
        return False

    def update(self, pecaId, sectionId, jsonData):

        peca = PecaProject.objects(
            isDeleted=False, id=pecaId).only('id').first()

        if peca:
            try:
                schema = SectionSchema()
                data = schema.load(jsonData)

                section = PecaProject.objects.filter(
                    id=peca.id,
                    school__sections__isDeleted=False,
                    school__sections__grade=newSection.grade,
                    school__sections__name=newSection.name
                ).fields(school__sections={'$elemMatch': {'name': newSection.name, 'grade': newSection.grade}})

                for section in peca.school.sections:
                    if str(section.id) == id:
                        for field in schema.dump(data).keys():
                            section[field] = data[field]
                        if self.checkForDuplicated(peca, section):
                            raise ValidationError(
                                {"name": [{"status": "5",
                                           "msg": "Duplicated record found: {}".format(section.name)}]}
                            )
                        try:
                            peca.school.append(section)
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

    def delete(self, lapse, id):
        """
        Delete (change isDeleted to False) a record
        """

        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").first()

        if schoolYear:
            if lapse == "1":
                activities = schoolYear.pecaSetting.lapse1.activities
            elif lapse == "2":
                activities = schoolYear.pecaSetting.lapse2.activities
            elif lapse == "3":
                activities = schoolYear.pecaSetting.lapse3.activities

            found = False
            for activity in activities:
                if str(activity.id) == str(id) and not activity.isDeleted:
                    found = True
                    try:
                        activity.isDeleted = True
                        if lapse == "1":
                            schoolYear.pecaSetting.lapse1.activities = activities
                        elif lapse == "2":
                            schoolYear.pecaSetting.lapse2.activities = activities
                        elif lapse == "3":
                            schoolYear.pecaSetting.lapse3.activities = activities
                        schoolYear.save()
                        return {"message": "Record deleted successfully"}, 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400

            if not found:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"recordId": id})
