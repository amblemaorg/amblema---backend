# app/services/teacher_testimonial_service.py


from functools import reduce
import operator

from flask import current_app
from marshmallow import ValidationError
from mongoengine import Q

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


class TeacherTestimonialService():

    def get_all(self, schoolId, access):

        school = SchoolUser.objects(id=schoolId, isDeleted=False).first()
        
        if school:
            testimonial = TeacherTestimonial()
            if school.teachersTestimonials:
                if access == "web" and school.teachersTestimonials.approvalStatus == "2":
                    testimonial = school.teachersTestimonials
                elif access == "peca":
                    testimonial = school.teachersTestimonials
            
            if testimonial.testimonials:
                schema = TeacherTestimonialSchema()
                #return {"testimonials": schema.dump(testimonial, many=True)}, 200
                return schema.dump(testimonial), 200
            else:
                return {'status': 0, 'message': 'There are no testimonials'}, 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId})
    
    def save(self, schoolId, userId, jsonData):

        school = SchoolUser.objects(id=str(schoolId), isDeleted=False).first()

        if school:
            try:
                schema = TeacherTestimonialSchema()
                data = schema.load(jsonData)
                schema.validate(jsonData)

                user = User.objects(id=str(userId), isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})
                
                teachersTestimonials = school.teachersTestimonials
                if teachersTestimonials:
                    if teachersTestimonials.isInApproval:
                        return {"status": "0", "msg": "Record has a pending approval request"}, 400
                else:
                    teachersTestimonials = TeacherTestimonial()
                
                i = 0
                for field in schema.dump(data).keys():
                    del teachersTestimonials[field][:]
                    for testimonial in data[field]:
                        teacher = school.teachers.filter(id=testimonial.teacherId, isDeleted=False).first()
                        if teacher:
                            testimonial.firstName = teacher.firstName
                            testimonial.lastName = teacher.lastName
                        else:
                            raise RegisterNotFound(message="Record not found",
                                    status_code=404,
                                    payload={"teacherId": testimonial.teacherId})
                        teachersTestimonials[field].append(testimonial)
                        jsonData[field][i]['image'] = teachersTestimonials[field][i].image
                        i+=1

                try:
                    request = RequestContentApproval(
                        project=school.project,
                        user=user,
                        type="2",
                        detail=jsonData
                    ).save()

                    teachersTestimonials.approvalStatus = "1"
                    teachersTestimonials.isInApproval = True
                    teachersTestimonials.approvalHistory.append(
                        Approval(
                            id=str(request.id),
                            user=user.id,
                            detail=jsonData
                        )
                    )

                    school.teachersTestimonials = teachersTestimonials
                    school.save()

                    #return {"testimonials": TestimonialSchema().dump(teachersTestimonials.testimonials, many=True)}, 200
                    return schema.dump(teachersTestimonials), 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId})
