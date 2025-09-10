# app/services/statistics_diagnostics_service.py


from datetime import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject

from app.helpers.error_helpers import RegisterNotFound


class StatisticsDiagnosticService():

    def get(self, schoolYearId, schoolId, diagnosticsFilter=None):

        schoolYear = SchoolYear.objects(
            id=schoolYearId).only('pecaSetting').first()
        peca = PecaProject.objects(
            schoolYear=schoolYearId,
            isDeleted=False,
            project__school__id=schoolId,
        ).first()

        if schoolYear and peca:

            goalSetting = schoolYear.pecaSetting.goalSetting
            diagnostics = {
                'math': 'multiplicationsPerMin',
                'logic': 'operationsPerMin',
                'reading': 'wordsPerMin'
            }

            # get diagnostic types parameters, if not, show all diagnostics
            diagnosticsSearch = []
            if diagnosticsFilter:
                for diag in diagnosticsFilter.split(','):
                    if diag in diagnostics:
                        diagnosticsSearch.append(diag)
            else:
                diagnosticsSearch = ['math', 'logic', 'reading']

            data = {}
            data['date'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
            data['school'] = peca.school.name
            data['schoolYear'] = peca.schoolYear.fetch().name
            data['coordinator'] = peca.project.coordinator.name
            data['sections'] = []
            data['yearSummaryAvailable'] = False
            data['yearSummary'] = {}
            data["totales"] = {
                'lapse1':{},
                'lapse2':{},
                'lapse3':{},
            }
            for diag in diagnosticsSearch:
                data["totales"]['lapse1'][diag] = {
                    'studentsMeta': 0
                }
                data["totales"]['lapse2'][diag] = {
                    'studentsMeta': 0
                }
                data["totales"]['lapse3'][diag] = {
                    'studentsMeta': 0
                }
            
            for section in peca.school.sections:
                if int(section.grade) > 0 and not section.isDeleted:

                    # initialize section data
                    sectionData = {}
                    sectionData['grade'] = section.grade
                    sectionData['name'] = section.name
                    sectionData['teacher'] = section.teacher.firstName + \
                        ' ' + section.teacher.lastName
                    sectionData['enrollment'] = len(section.students.filter(isDeleted=False))

                    for i in range(3):

                        # initialize lapse data
                        sectionData['lapse{}'.format(i+1)] = {
                            'available': False,
                            'students': [],
                        }

                        # initialize diagnostic data
                        for diag in diagnosticsSearch:
                            sectionData['lapse{}'.format(i+1)][diag] = {
                                'available': False,
                                'firstTestDate': '',
                                'lastTestDate': '',
                                'goal': goalSetting['grade{}'.format(section.grade)][diagnostics[diag]],
                                'participants': 0,
                                'resultAverage': 0,
                                'resultTotal': 0,
                                'overGoalStudents': 0,
                                'overGoalAverage': 0,
                                'indexTotal': 0,
                                'indexAverage': 0
                            }

                    # initialize diagnostic dates
                    diagnosticsDates = {}
                    for i in range(3):
                        diagnosticsDates['lapse{}'.format(i+1)] = {
                            'math': [],
                            'reading': [],
                            'logic': []
                        }

                    for student in section.students:
                        if not student.isDeleted:
                            for i in range(3):
                                hasResult = False
                                sectionLapse = sectionData['lapse{}'.format(
                                    i+1)]
                                studentLapse = student["lapse{}".format(i+1)]
                                studentData = {
                                    'firstName': student.firstName,
                                    'lastName': student.lastName,
                                    'cardId': student.cardId,
                                    'cardType': student.cardType
                                }
                                for diag in diagnosticsSearch:
                                    if studentLapse[diagnostics[diag]] != None:
                                        hasResult = True
                                        # set lapse and diagnostic available
                                        sectionLapse['available'] = True
                                        sectionLapse[diag]['available'] = True

                                        # set acumulators and counters
                                        goal = sectionLapse[diag]['goal']
                                        sectionLapse[diag]['participants'] += 1
                                        sectionLapse[diag]['resultTotal'] += studentLapse[diagnostics[diag]]
                                        sectionLapse[diag]['indexTotal'] += float(studentLapse['{}Index'.format(diagnostics[diag])]) if studentLapse['{}Index'.format(diagnostics[diag])]!=None else 0
                                        if diag == "reading":
                                            if studentLapse[diagnostics[diag]] >= goal:
                                                sectionLapse[diag]['overGoalStudents'] += 1
                                                data["totales"]["lapse{}".format(i+1)][diag]["studentsMeta"] += 1

                                        if diag in ["math", "logic"]:
                                            if studentLapse[diagnostics[diag]] == goal:
                                                sectionLapse[diag]['overGoalStudents'] += 1
                                                data["totales"]["lapse{}".format(i+1)][diag]["studentsMeta"] += 1

                                        # set dates of diagnostics
                                        diagnosticsDates['lapse{}'.format(i+1)][diag].append(
                                            studentLapse['{}Date'.format(diag)] if studentLapse['{}Date'.format(diag)] != None else datetime.today()
                                        )

                                        # add diagnostic data to student
                                        studentData[diagnostics[diag]
                                                    ] = studentLapse[diagnostics[diag]]
                                        studentData['{}Index'.format(
                                            diagnostics[diag])] = float(studentLapse['{}Index'.format(diagnostics[diag])]) if studentLapse['{}Index'.format(diagnostics[diag])] != None else 0
                                    else:
                                        studentData[diagnostics[diag]] = None
                                        studentData['{}Index'.format(
                                            diagnostics[diag])] = None
                                
                                # add student to lapse
                                #if hasResult:
                                sectionLapse['students'].append(
                                    studentData)
                                sectionData['lapse{}'.format(
                                    i+1)] = sectionLapse
                                
                                    

                    sectionSummaryAvailable = True
                    for i in range(3):
                        # process data and lapse statistics
                        lapse = sectionData['lapse{}'.format(i+1)]
                        diagnocticsDateLapse = diagnosticsDates['lapse{}'.format(
                            i+1)]
                        if lapse['available']:
                            for diag in diagnosticsSearch:
                                diagnostic = lapse[diag]
                                if diagnostic['available']:
                                    diagnostic['resultAverage'] = diagnostic['resultTotal'] / \
                                        diagnostic['participants']
                                    diagnostic['overGoalAverage'] = diagnostic['overGoalStudents'] * 100 / \
                                        diagnostic['participants']
                                    diagnostic['indexAverage'] = diagnostic['indexTotal'] / \
                                        diagnostic['participants']

                                    # set diagnostic date min and max
                                    minDate = min(diagnocticsDateLapse[diag])
                                    diagnostic['firstTestDate'] = minDate.strftime(
                                        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                                    maxDate = max(diagnocticsDateLapse[diag])
                                    diagnostic['lastTestDate'] = maxDate.strftime(
                                        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

                                    lapse[diag] = diagnostic
                            sectionData['lapse{}'.format(i+1)] = lapse
                        else:
                            sectionSummaryAvailable = False

                    if sectionSummaryAvailable:
                        sectionSummary = {}
                        for diag in diagnosticsSearch:
                            available = False
                            for i in range(3):
                                if sectionData['lapse{}'.format(i+1)][diag]['available']:
                                    available = True
                            if available:
                                sectionSummary[diag] = {}
                                data['yearSummaryAvailable'] = True
                                sectionData['sectionSummaryAvailable'] = True
                                for i in range(3):
                                    sectionSummary[diag]['lapse{}'.format(
                                        i+1)] = {}
                                    # resultAverage
                                    sectionSummary[diag]['lapse{}'.format(
                                        i+1)]['resultAverage'] = sectionData['lapse{}'.format(
                                            i+1)][diag]['resultAverage']
                                    # indexAverage
                                    sectionSummary[diag]['lapse{}'.format(
                                        i+1)]['indexAverage'] = sectionData['lapse{}'.format(
                                            i+1)][diag]['indexAverage']
                                    # overGoalStudents
                                    sectionSummary[diag]['lapse{}'.format(
                                        i+1)]['overGoalStudents'] = sectionData['lapse{}'.format(
                                            i+1)][diag]['overGoalStudents']
                                # improvement percentage
                                sectionSummary[diag]['improvementPercentage'] = ((sectionSummary[diag]['lapse3']['resultAverage'] -
                                                                                  sectionSummary[diag]['lapse1']['resultAverage'])
                                                                                 * 100/sectionSummary[diag]['lapse3']['resultAverage']) if sectionSummary[diag]['lapse3']['resultAverage'] > 0 else 0
                                sectionSummary[diag]['totalIndexAverage'] = (sectionSummary[diag]['lapse1']['indexAverage'] +
                                                                             sectionSummary[diag]['lapse2']['indexAverage'] +
                                                                             sectionSummary[diag]['lapse3']['indexAverage'])/3

                        sectionData['sectionSummary'] = sectionSummary

                    data['sections'].append(sectionData)

            if data['yearSummaryAvailable'] == True:
                yearSummary = {}
                for diag in diagnosticsSearch:
                    diagSummary = {
                        'sections': [],
                        'improvementPercentageAverage': 0
                    }
                    improvementPercentageAcum = 0
                    resultAverageAcum = 0

                    for section in data['sections']:
                        if 'sectionSummaryAvailable' in section and section['sectionSummaryAvailable'] and diag in section['sectionSummary']:
                            improvementPercentageAcum += section['sectionSummary'][diag]['improvementPercentage']
                            sectionSummary = {
                                'grade': section['grade'],
                                'name': section['name'],
                                'goal': goalSetting['grade{}'.format(section['grade'])][diagnostics[diag]],
                                'improvementPercentage': section['sectionSummary'][diag]['improvementPercentage'],
                                'lapse1': {},
                                'lapse2': {},
                                'lapse3': {}}
                            sectionResultAcum = 0
                            for i in range(1, 4):
                                sectionSummary['lapse{}'.format(
                                    i)]['resultAverage'] = section['sectionSummary'][diag]['lapse{}'.format(i)]['resultAverage']
                                sectionResultAcum += section['sectionSummary'][diag]['lapse{}'.format(
                                    i)]['resultAverage']
                                sectionSummary['lapse{}'.format(
                                    i)]['indexAverage'] = section['sectionSummary'][diag]['lapse{}'.format(i)]['indexAverage']
                                sectionSummary['lapse{}'.format(
                                    i)]['overGoalStudents'] = section['sectionSummary'][diag]['lapse{}'.format(i)]['overGoalStudents']
                            resultAverageAcum += sectionResultAcum/3
                            diagSummary['sections'].append(
                                sectionSummary)
                    if diagSummary['sections']:
                        diagSummary['improvementPercentageAverage'] = improvementPercentageAcum / \
                            len(diagSummary['sections'])
                        diagSummary['totalResultAverage'] = resultAverageAcum / \
                            len(diagSummary['sections'])
                        diagSummary['sections'] = sorted(
                            diagSummary['sections'], key=lambda x: (x['grade'], x['name']))
                        yearSummary[diag] = diagSummary
                data['sections'] = sorted(
                    data['sections'], key=lambda x: (x['grade'], x['name']))
                data['yearSummary'] = yearSummary
            return data, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolYearId": schoolYearId, "schoolId": schoolId})
