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
                            students_data = peca['lapse{}'.format(lapse)].readingOlympics.students
                            summary = school.olympicsReadingSummary
                        else:
                            students_data = peca['lapse{}'.format(lapse)].olympics.students
                            summary = school.olympicsSummary

                        summary.inscribed = len(students_data)
                        summary.participant = len([s for s in students_data if s.status in ["2", "3"]])
                        summary.classified = len([s for s in students_data if s.status == "3"])
                        
                        summary.participantRegional = len([s for s in students_data if s.statusRegional in ["1", "2"]])
                        summary.classifiedRegional = 0
                        
                        summary.medalsGold = len([s for s in students_data if s.result == "1" and s.statusRegional == "1"])
                        summary.medalsSilver = len([s for s in students_data if s.result == "2" and s.statusRegional == "1"])
                        summary.medalsBronze = len([s for s in students_data if s.result == "3" and s.statusRegional == "1"])
                        
                        summary.inscribedNational = len([s for s in students_data if s.result == "1"])
                        summary.classifiedNational = 0
                        summary.medalsGoldNational = len([s for s in students_data if s.resultNational == "1" and s.statusNational == "1"])
                        summary.medalsSilverNational = len([s for s in students_data if s.resultNational == "2" and s.statusNational == "1"])
                        summary.medalsBronzeNational = len([s for s in students_data if s.resultNational == "3" and s.statusNational == "1"])
                        
                        school.save()
                        
                        schoolYear = peca.schoolYear.fetch()
                        schoolYear.refreshOlympicsSummary()
                        schoolYear.save()

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
                        has_changed = True

                # Enforce dependent fields consistency
                if record.statusRegional != '1':
                    if record.result is not None or record.statusNational is not None or record.resultNational is not None:
                        record.result = None
                        record.statusNational = None
                        record.resultNational = None
                        has_changed = True
                elif record.result != '1':
                    if record.statusNational is not None or record.resultNational is not None:
                        record.statusNational = None
                        record.resultNational = None
                        has_changed = True
                elif record.statusNational != '1':
                    if record.resultNational is not None:
                        record.resultNational = None
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
                                school = SchoolUser.objects(
                                    id=peca.project.school.id, isDeleted=False).first()
                                
                                if olympicsType == 'reading':
                                    students_data = peca['lapse{}'.format(lapse)].readingOlympics.students
                                    summary = school.olympicsReadingSummary
                                else:
                                    students_data = peca['lapse{}'.format(lapse)].olympics.students
                                    summary = school.olympicsSummary

                                summary.inscribed = len(students_data)
                                summary.participant = len([s for s in students_data if s.status in ["2", "3"]])
                                summary.classified = len([s for s in students_data if s.status == "3"])
                                
                                summary.participantRegional = len([s for s in students_data if s.statusRegional in ["1", "2"]])
                                summary.classifiedRegional = 0
                                
                                summary.medalsGold = len([s for s in students_data if s.result == "1" and s.statusRegional == "1"])
                                summary.medalsSilver = len([s for s in students_data if s.result == "2" and s.statusRegional == "1"])
                                summary.medalsBronze = len([s for s in students_data if s.result == "3" and s.statusRegional == "1"])
                                
                                summary.inscribedNational = len([s for s in students_data if s.result == "1"])
                                summary.classifiedNational = 0
                                summary.medalsGoldNational = len([s for s in students_data if s.resultNational == "1" and s.statusNational == "1"])
                                summary.medalsSilverNational = len([s for s in students_data if s.resultNational == "2" and s.statusNational == "1"])
                                summary.medalsBronzeNational = len([s for s in students_data if s.resultNational == "3" and s.statusNational == "1"])

                                school.save()

                                schoolYear = peca.schoolYear.fetch()
                                schoolYear.refreshOlympicsSummary()
                                schoolYear.save()
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
                    school = SchoolUser.objects(
                        id=peca.project.school.id, isDeleted=False).first()
                    
                    if olympicsType == 'reading':
                        students_data = peca['lapse{}'.format(lapse)].readingOlympics.students
                        summary = school.olympicsReadingSummary
                    else:
                        students_data = peca['lapse{}'.format(lapse)].olympics.students
                        summary = school.olympicsSummary

                    summary.inscribed = len(students_data)
                    summary.participant = len([s for s in students_data if s.status in ["2", "3"]])
                    summary.classified = len([s for s in students_data if s.status == "3"])
                    
                    summary.participantRegional = len([s for s in students_data if s.statusRegional in ["1", "2"]])
                    summary.classifiedRegional = 0
                    
                    summary.medalsGold = len([s for s in students_data if s.result == "1" and s.statusRegional == "1"])
                    summary.medalsSilver = len([s for s in students_data if s.result == "2" and s.statusRegional == "1"])
                    summary.medalsBronze = len([s for s in students_data if s.result == "3" and s.statusRegional == "1"])
                    
                    summary.inscribedNational = len([s for s in students_data if s.result == "1"])
                    summary.classifiedNational = 0
                    summary.medalsGoldNational = len([s for s in students_data if s.resultNational == "1" and s.statusNational == "1"])
                    summary.medalsSilverNational = len([s for s in students_data if s.resultNational == "2" and s.statusNational == "1"])
                    summary.medalsBronzeNational = len([s for s in students_data if s.resultNational == "3" and s.statusNational == "1"])

                    school.save()

                    schoolYear = peca.schoolYear.fetch()
                    schoolYear.refreshOlympicsSummary()
                    schoolYear.save()
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
