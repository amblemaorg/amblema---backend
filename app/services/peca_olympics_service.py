# app/services/peca_amblecoins_service.py

import copy

from flask import current_app
from marshmallow import ValidationError

from app.models.peca_project_model import PecaProject
from app.models.peca_olympics_model import Olympics, Student
from app.schemas.peca_olympics_schema import OlympicsSchema, StudentSchema
from app.helpers.error_helpers import RegisterNotFound
from app.models.school_user_model import SchoolUser


class OlympicsService():

    def getOlympics(self, pecaId, lapse, olympicsType='math'):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            schema = OlympicsSchema()
            if olympicsType == 'reading':
                olympics = peca['lapse{}'.format(
                lapse)].readingOlympics
            else:
                olympics = peca['lapse{}'.format(
                    lapse)].olympics
            return schema.dump(olympics), 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def saveStudent(self, pecaId, lapse, jsonData, olympicsType='math'):

        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                paso = False
                schema = StudentSchema()

                if not peca['lapse{}'.format(lapse)].olympics:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"olympics lapse: ": lapse})
                if "section" in jsonData:
                    section = peca.school.sections.filter(
                        id=jsonData['section'], isDeleted=False).first()
                    if not section:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"section: ": jsonData["section"]})
                if "student" in jsonData and section:
                    paso = True
                    student = section.students.filter(
                        id=jsonData['student']).first()
                    if not student:
                        raise RegisterNotFound(message="Record not found",
                                               status_code=404,
                                               payload={"student: ": jsonData["student"]})
                    if olympicsType == 'reading':
                         olympics = peca['lapse{}'.format(
                            lapse)].readingOlympics
                    else:
                        olympics = peca['lapse{}'.format(
                            lapse)].olympics

                    for enrolledStudent in olympics.students:
                        if enrolledStudent.id == str(student.id):
                            return {
                                "student": [
                                    {
                                        "status": "5",
                                        "msg": "Duplicated record found"
                                    }]
                            }, 400

                    jsonData['id'] = str(student.id)
                    jsonData['name'] = student.firstName + \
                        ' ' + student.lastName
                    jsonData['section'] = {
                        "id": str(section.id),
                        "name": section.name,
                        "grade": section.grade}

                data = schema.load(jsonData)

                student = Student()
                for field in data.keys():
                    student[field] = data[field]
                if paso:
                    olympics['students'].append(student)
                    try:
                        if olympicsType == 'reading':
                            peca['lapse{}'.format(lapse)].readingOlympics = olympics
                        else:
                            peca['lapse{}'.format(lapse)].olympics = olympics
                        peca.save()
                        school = SchoolUser.objects(
                            id=peca.project.school.id, isDeleted=False).first()
                        if olympicsType == 'reading':
                            school.olympicsReadingSummary.inscribed += 1
                            if student.status == "2":
                                school.olympicsReadingSummary.classified += 1
                                if student.result:
                                    if student.result == "1":
                                        school.olympicsReadingSummary.medalsGold += 1
                                    elif student.result == "2":
                                        school.olympicsReadingSummary.medalsSilver += 1
                                    elif student.result == "3":
                                        school.olympicsReadingSummary.medalsBronze += 1
                            
                            school.olympicsReadingSummary.inscribedNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="1"))
                            
                            if student.statusNational == "2":
                                school.olympicsReadingSummary.classifiedNational += 1
                                if student.resultNational:
                                    if student.resultNational == "1":
                                        school.olympicsReadingSummary.medalsGoldNational += 1
                                    elif student.resultNational == "2":
                                        school.olympicsReadingSummary.medalsSilverNational += 1
                                    elif student.resultNational == "3":
                                        school.olympicsReadingSummary.medalsBronzeNational += 1
                        else:
                            school.olympicsSummary.inscribed += 1
                            if student.status == "2":
                                school.olympicsSummary.classified += 1
                                if student.result:
                                    if student.result == "1":
                                        school.olympicsSummary.medalsGold += 1
                                    elif student.result == "2":
                                        school.olympicsSummary.medalsSilver += 1
                                    elif student.result == "3":
                                        school.olympicsSummary.medalsBronze += 1
                            
                            school.olympicsSummary.inscribedNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1"))

                            if student.statusNational == "2":
                                school.olympicsSummary.classifiedNational += 1
                                if student.resultNational:
                                    if student.resultNational == "1":
                                        school.olympicsSummary.medalsGoldNational += 1
                                    elif student.resultNational == "2":
                                        school.olympicsSummary.medalsSilverNational += 1
                                    elif student.resultNational == "3":
                                        school.olympicsSummary.medalsBronzeNational += 1
                        
                        school.save()

                        return schema.dump(student), 200
                    except Exception as e:
                        return {'status': 0, 'message': str(e)}, 400
                else:
                    return schema.dump(student), 200
                    
            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def updateStudent(self, pecaId, lapse, studentId, jsonData, olympicsType='math'):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            try:
                schema = StudentSchema()
                if olympicsType == 'reading':
                     if not peca['lapse{}'.format(lapse)].readingOlympics:
                        raise RegisterNotFound(message="Record not found",
                                            status_code=404,
                                            payload={"readingOlympics lapse: ": lapse})
                else:
                    if not peca['lapse{}'.format(lapse)].olympics:
                        raise RegisterNotFound(message="Record not found",
                                            status_code=404,
                                            payload={"olympics lapse: ": lapse})

                data = schema.load(jsonData, partial=True)
                if olympicsType == 'reading':
                     record = peca['lapse{}'.format(
                        lapse)].readingOlympics.students.filter(id=studentId).first()
                else:
                    record = peca['lapse{}'.format(
                        lapse)].olympics.students.filter(id=studentId).first()
                oldRecord = copy.copy(record)
                if not record:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"student: ": studentId})
                has_changed = False
                for field in data.keys():
                    if data[field] != record[field]:
                        record[field] = data[field]
                        if field == 'result' and data[field]:
                            record['status'] = '2'
                        has_changed = True
                if has_changed:
                    if olympicsType == 'reading':
                         students_list = peca['lapse{}'.format(lapse)].readingOlympics.students
                    else:
                        students_list = peca['lapse{}'.format(lapse)].olympics.students

                    for student in students_list:
                        if student.id == studentId:
                            student = record
                            try:
                                peca.save()
                                if olympicsType == 'reading':
                                    classified = peca['lapse{}'.format(lapse)].readingOlympics.students.filter(status="2")
                                    classifiedNational = peca['lapse{}'.format(lapse)].readingOlympics.students.filter(statusNational="2")
                                else:
                                    classified = peca['lapse{}'.format(lapse)].olympics.students.filter(status="2")
                                    classifiedNational = peca['lapse{}'.format(lapse)].olympics.students.filter(statusNational="2")

                                school = SchoolUser.objects(
                                        id=peca.project.school.id, isDeleted=False).first()
                                
                                if olympicsType == 'reading':
                                    school.olympicsReadingSummary.classified = len(classified)
                                    school.olympicsReadingSummary.inscribed = len(peca['lapse{}'.format(lapse)].readingOlympics.students)
                                    school.olympicsReadingSummary.medalsGold = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="1", status="2"))
                                    school.olympicsReadingSummary.medalsSilver = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="2", status="2"))
                                    school.olympicsReadingSummary.medalsBronze = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="3", status="2"))
                                    
                                    school.olympicsReadingSummary.inscribedNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="1"))
                                    school.olympicsReadingSummary.classifiedNational = len(classifiedNational)
                                    school.olympicsReadingSummary.medalsGoldNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(resultNational="1", statusNational="2"))
                                    school.olympicsReadingSummary.medalsSilverNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(resultNational="2", statusNational="2"))
                                    school.olympicsReadingSummary.medalsBronzeNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(resultNational="3", statusNational="2"))
                                else:
                                    school.olympicsSummary.classified = len(classified)
                                    school.olympicsSummary.inscribed = len(peca['lapse{}'.format(lapse)].olympics.students)
                                    school.olympicsSummary.medalsGold = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1", status="2"))
                                    school.olympicsSummary.medalsSilver = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="2", status="2"))
                                    school.olympicsSummary.medalsBronze = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="3", status="2"))

                                    school.olympicsSummary.inscribedNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1"))
                                    school.olympicsSummary.classifiedNational = len(classifiedNational)
                                    school.olympicsSummary.medalsGoldNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(resultNational="1", statusNational="2"))
                                    school.olympicsSummary.medalsSilverNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(resultNational="2", statusNational="2"))
                                    school.olympicsSummary.medalsBronzeNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(resultNational="3", statusNational="2"))

                                school.save()
                                #if student.result != oldRecord.result:
                                    #if oldRecord.status == '2':
                                    #    school.olympicsSummary.classified -= 1
                                    #if oldRecord.result:
                                    #    if oldRecord.result == "1":
                                    #        school.olympicsSummary.medalsGold = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1"))
                                    #    elif oldRecord.result == "2":
                                    #        school.olympicsSummary.medalsSilver = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="2"))
                                    #    elif oldRecord.result == "3":
                                    #        school.olympicsSummary.medalsBronze = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="3"))
                                    #if student.result:
                                    #if student.result == "1":
                                    #    school.olympicsSummary.medalsGold = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1", status="2"))
                                    #elif student.result == "2":
                                    #    school.olympicsSummary.medalsSilver = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="2", status="2"))
                                    #elif student.result == "3":
                                    #    school.olympicsSummary.medalsBronze = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="3", status="2"))
                                    #if student.status == '2':
                                    #    school.olympicsSummary.classified += 1
                                #    school.save()
                                break
                            except Exception as e:
                                return {'status': 0, 'message': str(e)}, 400
                return schema.dump(record), 200

            except ValidationError as err:
                return err.normalized_messages(), 400
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})

    def deleteStudent(self, pecaId, lapse, studentId, olympicsType='math'):
        peca = PecaProject.objects(
            isDeleted=False,
            id=pecaId,
        ).first()

        if peca:
            if olympicsType == 'reading':
                 if not peca['lapse{}'.format(lapse)].readingOlympics:
                    raise RegisterNotFound(message="Record not found",
                                           status_code=404,
                                           payload={"readingOlympics lapse: ": lapse})
                 record = peca['lapse{}'.format(
                    lapse)].readingOlympics.students.filter(id=studentId).first()
            else:
                if not peca['lapse{}'.format(lapse)].olympics:
                    raise RegisterNotFound(message="Record not found",
                                        status_code=404,
                                        payload={"olympics lapse: ": lapse})

                record = peca['lapse{}'.format(
                    lapse)].olympics.students.filter(id=studentId).first()
            if not record:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"olympics lapse: ": lapse})
            found = False
            if olympicsType == 'reading':
                students_list = peca['lapse{}'.format(lapse)].readingOlympics.students
            else:
                students_list = peca['lapse{}'.format(lapse)].olympics.students

            for student in students_list:
                if student.id == studentId:
                    found = True
                    if olympicsType == 'reading':
                        peca['lapse{}'.format(
                        lapse)].readingOlympics.students.remove(student)
                    else:
                        peca['lapse{}'.format(
                            lapse)].olympics.students.remove(student)
                    break

            if found:
                try:
                    peca.save()
                    if olympicsType == 'reading':
                        classified = peca['lapse{}'.format(lapse)].readingOlympics.students.filter(status="2")   
                        classifiedNational = peca['lapse{}'.format(lapse)].readingOlympics.students.filter(statusNational="2")

                        school = SchoolUser.objects(
                            id=peca.project.school.id, isDeleted=False).first()
                        school.olympicsReadingSummary.classified = len(classified)
                        school.olympicsReadingSummary.inscribed = len(peca['lapse{}'.format(lapse)].readingOlympics.students)
                        school.olympicsReadingSummary.medalsGold = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="1", status="2"))
                        school.olympicsReadingSummary.medalsSilver = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="2", status="2"))
                        school.olympicsReadingSummary.medalsBronze = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="3", status="2"))
                        
                        school.olympicsReadingSummary.inscribedNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(result="1"))
                        school.olympicsReadingSummary.classifiedNational = len(classifiedNational)
                        school.olympicsReadingSummary.medalsGoldNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(resultNational="1", statusNational="2"))
                        school.olympicsReadingSummary.medalsSilverNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(resultNational="2", statusNational="2"))
                        school.olympicsReadingSummary.medalsBronzeNational = len(peca['lapse{}'.format(lapse)].readingOlympics.students.filter(resultNational="3", statusNational="2"))
                    else:
                        classified = peca['lapse{}'.format(lapse)].olympics.students.filter(status="2")   
                        classifiedNational = peca['lapse{}'.format(lapse)].olympics.students.filter(statusNational="2")

                        school = SchoolUser.objects(
                            id=peca.project.school.id, isDeleted=False).first()
                        school.olympicsSummary.classified = len(classified)
                        school.olympicsSummary.inscribed = len(peca['lapse{}'.format(lapse)].olympics.students)
                        school.olympicsSummary.medalsGold = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1", status="2"))
                        school.olympicsSummary.medalsSilver = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="2", status="2"))
                        school.olympicsSummary.medalsBronze = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="3", status="2"))
                        
                        school.olympicsSummary.inscribedNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(result="1"))
                        school.olympicsSummary.classifiedNational = len(classifiedNational)
                        school.olympicsSummary.medalsGoldNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(resultNational="1", statusNational="2"))
                        school.olympicsSummary.medalsSilverNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(resultNational="2", statusNational="2"))
                        school.olympicsSummary.medalsBronzeNational = len(peca['lapse{}'.format(lapse)].olympics.students.filter(resultNational="3", statusNational="2"))

                    school.save()
                    #if record.result:
                    #    #school.olympicsSummary.classified -= 1
                    #    if record.result == "1":
                    #        school.olympicsSummary.medalsGold -= 1
                    #    elif record.result == "2":
                    #        school.olympicsSummary.medalsSilver -= 1
                    #    elif record.result == "3":
                    #        school.olympicsSummary.medalsBronze -= 1
                    #school.save()
                    return {"message": "Record deleted successfully"}, 200
                except Exception as e:
                    return {'status': 0, 'message': str(e)}, 400
            else:
                raise RegisterNotFound(message="Record not found",
                                       status_code=404,
                                       payload={"olympics lapse: ": lapse})

        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"pecaId": pecaId})
