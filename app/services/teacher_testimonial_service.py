# app/services/teacher_testimonial_service.py


from functools import reduce
import operator
import os.path
import copy

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q, fields

from app.models.teacher_testimonial_model import TeacherTestimonial
from app.models.school_user_model import SchoolUser
from app.models.user_model import User
from app.models.request_content_approval_model import RequestContentApproval
from app.models.teacher_model import Teacher
from app.schemas.teacher_testimonial_schema import TeacherTestimonialSchema, TestimonialSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound
from app.models.shared_embedded_documents import Approval
from resources.images import path_images
from app.helpers.handler_images import upload_image


class TeacherTestimonialService():

    filesFolder = 'testimonials'

    def get_all(self, schoolId):

        school = SchoolUser.objects(id=schoolId, isDeleted=False).first()

        if school:
            schema = TeacherTestimonialSchema()
            return schema.dump(school.teachersTestimonials), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId})

    def save(self, schoolId, userId, jsonData):

        school = SchoolUser.objects(id=str(schoolId), isDeleted=False).first()

        if school:
            try:
                user = User.objects(id=str(userId), isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})

                schema = TeacherTestimonialSchema()

                teachersTestimonials = school.teachersTestimonials
                newTeachersTestimonials = copy.copy(teachersTestimonials)
                if teachersTestimonials.isInApproval:
                    return {"status": "0", "msg": "Record has a pending approval request"}, 400

                if 'testimonials' in jsonData:
                    folder = "schools/{}/{}".format(
                        schoolId,
                        self.filesFolder
                    )
                    DIR = path_images + '/' + folder
                    folder = folder + \
                        '/{}'.format(len([name for name in os.listdir(DIR)]) + 1
                                     if os.path.exists(DIR) else 1)
                    for testimonial in jsonData['testimonials']:
                        teacher = school.teachers.filter(
                            id=testimonial['teacherId'], isDeleted=False).first()
                        if teacher:
                            testimonial['firstName'] = teacher.firstName
                            testimonial['lastName'] = teacher.lastName
                        else:
                            raise RegisterNotFound(message="Record not found",
                                                   status_code=404,
                                                   payload={"teacherId": testimonial['teacherId']})
                        if 'id' not in testimonial:
                            testimonial['id'] = str(fields.ObjectId())
                        if str(testimonial['image']).startswith('data'):
                            testimonial['image'] = upload_image(
                                testimonial['image'], folder, None)

                data = schema.load(jsonData)

                approvalRequired = False
                oldTestimonials = {}
                for testimonial in teachersTestimonials.testimonials:
                    oldTestimonials[testimonial.id] = testimonial

                for field in data.keys():
                    if teachersTestimonials[field] != data[field]:
                        if field == 'testimonials':
                            for testimonial in data[field]:
                                # testimonial was updated
                                if testimonial.id in oldTestimonials and testimonial != oldTestimonials[testimonial.id]:
                                    approvalRequired = True
                                # new testimonial
                                elif testimonial.id not in oldTestimonials:
                                    approvalRequired = True
                        newTeachersTestimonials[field] = data[field]
                try:
                    if approvalRequired:
                        jsonData['schoolId'] = schoolId

                        request = RequestContentApproval(
                            project=school.project,
                            user=user,
                            type="2",
                            detail=jsonData
                        ).save()

                        teachersTestimonials.isInApproval = True
                        teachersTestimonials.approvalHistory.append(
                            Approval(
                                id=str(request.id),
                                user=user.id,
                                detail=jsonData
                            )
                        )
                    else:
                        teachersTestimonials.testimonials = newTeachersTestimonials.testimonials
                    school.save()

                    return schema.dump(teachersTestimonials), 200
                except Exception as e:
                    print(e)
                    return {'status': 0, 'message': str(e)}, 400
            except Exception as e:
                print(e)
                return {'status': 0, 'message': str(e)}, 400
            
            #except ValidationError as err:
            #    return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId})
