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
from app.schemas.teacher_testimonial_schema import TeacherTestimonialSchema
from app.helpers.handler_files import validate_files, upload_files
from app.helpers.document_metadata import getFileFields
from app.helpers.error_helpers import RegisterNotFound


class TeacherTestimonialService():

    def get_all(self, schoolId, access):

        school = SchoolUser.objects(id=schoolId, isDeleted=False).only("teachersTestimonials").first()
        
        if school:
            testimonials = []
            if access == "web":
                testimonials = school.teachersTestimonials.filter(approvalStatus="2", visibilityStatus="1", isDeleted=False)
            elif access == "peca":
                testimonials = school.teachersTestimonials.filter(isDeleted=False)
            
            if testimonials:
                schema = TeacherTestimonialSchema()
                return {"records": schema.dump(testimonials, many=True)}, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId})
    
    def get(self, schoolId, testimonialId):

        school = SchoolUser.objects(id=schoolId, isDeleted=False).only("teachersTestimonials").first()

        if school:
            testimonial = school.teachersTestimonials.filter(id=testimonialId, isDeleted=False).first()
            if testimonial:
                schema = TeacherTestimonialSchema()
                return schema.dump(testimonial), 200
            else:
                raise RegisterNotFound(message="Record not found",
                                    status_code=404,
                                    payload={"testimonialId": testimonialId})
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

                user = User.objects(id=str(userId), isDeleted=False).first()
                if not user:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"userId":  userId})
                
                cont = school.teachersTestimonials.filter(isDeleted=False).count()
                
                if cont < 4:
                    testimonial = TeacherTestimonial()
                    for field in schema.dump(data).keys():
                        testimonial[field] = data[field]
                    try:
                        teacher = school.teachers.filter(id=testimonial.teacherId, isDeleted=False).first()
                        if teacher:
                            testimonial.firstName = teacher.firstName
                            testimonial.lastName = teacher.lastName
                        else:
                            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"teacherId": testimonial.teacherId})
                        
                        school.teachersTestimonials.append(testimonial)
                        school.save()
                        RequestContentApproval(
                            project=school.project,
                            user=user,
                            type="2",
                            detail=schema.dump(testimonial)
                        ).save()
                        return schema.dump(testimonial), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400
                else:
                    return {'status': 0, 'message': 'Supero la cantidad maxima de testimonios'}, 400

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId})
    
    def update(self, schoolId, testimonialId, jsonData):

        school = SchoolUser.objects(id=schoolId, isDeleted=False).first()
        
        if school:
            try:
                schema = TeacherTestimonialSchema()
                data = schema.load(jsonData)
                hasChanged = False

                testimonial = school.teachersTestimonials.filter(id=testimonialId, isDeleted=False).first()
                if testimonial:
                    for field in schema.dump(data).keys():
                        if testimonial[field] != data[field]:
                            hasChanged = True
                            testimonial[field] = data[field]
                    
                    if hasChanged:
                        try:
                            teacher = school.teachers.filter(id=testimonial.teacherId, isDeleted=False).first()
                            if teacher:
                                testimonial.firstName = teacher.firstName
                                testimonial.lastName = teacher.lastName
                            else:
                                raise RegisterNotFound(message="Record not found",
                                    status_code=404,
                                    payload={"teacherId": testimonial.teacherId})
                            school.save()
                            return schema.dump(testimonial), 200
                        except Exception as e:
                            return {'status': 0, 'message': str(e)}, 400
                else:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404, payload={"testimonialId": testimonialId})
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolId": schoolId, "testimonialId": testimonialId})
    
    def delete(self, schoolId, testimonialId):
        """
        Delete (change isDeleted to True) a record
        """
        
        school = SchoolUser.objects(id=schoolId, isDeleted=False, teachersTestimonials__id= testimonialId, teachersTestimonials__isDeleted=False).only("teachersTestimonials").first()

        if school:
            try:
                SchoolUser.objects(id=schoolId, isDeleted=False, teachersTestimonials__id= testimonialId, teachersTestimonials__isDeleted=False).update(set__teachersTestimonials__S__isDeleted=True)
                return {"message": "Record deleted successfully"}, 200
            except Exception as e:
                return {'status': 0, 'message': str(e)}, 400
        else:
            raise RegisterNotFound(message="Record not found",
            status_code=404,
            payload={"schoolId": schoolId, "testimonialId": testimonialId})