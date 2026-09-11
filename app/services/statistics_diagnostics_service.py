# app/services/statistics_diagnostics_service.py


from datetime import datetime

from flask import current_app
from marshmallow import ValidationError

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator

from app.helpers.error_helpers import RegisterNotFound


class StatisticsDiagnosticService():

    def get(self, schoolYearId, schoolId, diagnosticsFilter=None, lapso=None):

        targetLapse = None
        if lapso:
            try:
                targetLapse = int(lapso)
            except ValueError:
                pass

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
            hasEnvironmental = False
            if diagnosticsFilter:
                for diag in diagnosticsFilter.split(','):
                    diag_clean = diag.strip()
                    if diag_clean in diagnostics:
                        diagnosticsSearch.append(diag_clean)
                    if diag_clean in ['environmental', 'environment']:
                        hasEnvironmental = True
            else:
                diagnosticsSearch = ['math', 'logic', 'reading']
                hasEnvironmental = True

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
            
            sections_list = peca.school.sections if diagnosticsSearch else []
            for section in sections_list:
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
                                if targetLapse and (i+1) > targetLapse:
                                    continue
                                hasResult = False
                                sectionLapse = sectionData['lapse{}'.format(
                                    i+1)]
                                studentLapse = student["lapse{}".format(i+1)]
                                studentData = {
                                    'id': str(student.id),
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
                                        if diag in ["reading", "math", "logic"]:
                                            if studentLapse[diagnostics[diag]] >= goal:
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
                        if targetLapse and (i+1) > targetLapse:
                            continue
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

            # Environmental diagnostic data
            environmentalData = {
                'hasData': False,
                'lapses': {
                    '1': {'lapseName': '1er Lapso', 'evaluators': [], 'summary': None},
                    '2': {'lapseName': '2do Lapso', 'evaluators': [], 'summary': None},
                    '3': {'lapseName': '3er Lapso', 'evaluators': [], 'summary': None},
                }
            }

            if hasEnvironmental:
                indicator_definitions = [
                    {
                        'key': 'cleanlinessAndCareOfSpaces',
                        'title': 'Limpieza y cuidado de los espacios',
                        'subcriteria': ['1.1', '1.2', '1.3']
                    },
                    {
                        'key': 'wasteManagement',
                        'title': 'Gestión y aprovechamiento de los residuos',
                        'subcriteria': ['2.1', '2.2', '2.3']
                    },
                    {
                        'key': 'biodiversityConservation',
                        'title': 'Conservación de la biodiversidad',
                        'subcriteria': ['3.1', '3.2', '3.3']
                    },
                    {
                        'key': 'waterUse',
                        'title': 'Aprovechamiento del agua',
                        'subcriteria': ['4.1', '4.2', '4.3']
                    },
                    {
                        'key': 'communityRelations',
                        'title': 'Relación con la comunidad',
                        'subcriteria': ['5.1', '5.2']
                    }
                ]

                eval_query = EnvironmentalDiagnosticEvaluator.objects(
                    pecaId=str(peca.id),
                    isDeleted=False,
                    hasEvaluated=True
                )
                if targetLapse:
                    eval_query = eval_query.filter(lapse=str(targetLapse))

                all_evals = list(eval_query)

                for lapse_key in ['1', '2', '3']:
                    lapse_evals = [e for e in all_evals if e.lapse == lapse_key]
                    evaluators_list = []

                    for e in lapse_evals:
                        eval_res = e.results or {}
                        ind_data = {}
                        eval_ind_avgs = []

                        for ind_def in indicator_definitions:
                            ikey = ind_def['key']
                            isub = ind_def['subcriteria']
                            ind_dict = eval_res.get(ikey, {})

                            sub_vals = {}
                            sub_dict = ind_dict.get('subcriteria', {}) if isinstance(ind_dict, dict) else {}

                            applied_vals = []
                            for sc in isub:
                                sc_val = None
                                if isinstance(sub_dict, dict) and sc in sub_dict:
                                    sc_item = sub_dict[sc]
                                    if isinstance(sc_item, dict):
                                        val = sc_item.get('value')
                                        applies = sc_item.get('applies', True)
                                        if applies and val is not None and val != '':
                                            try:
                                                sc_val = float(val)
                                                applied_vals.append(sc_val)
                                            except (ValueError, TypeError):
                                                sc_val = 0.0
                                                applied_vals.append(0.0)
                                        else:
                                            sc_val = 0.0
                                    else:
                                        try:
                                            sc_val = float(sc_item)
                                            applied_vals.append(sc_val)
                                        except (ValueError, TypeError):
                                            sc_val = 0.0
                                sub_vals[sc] = sc_val

                            ind_avg = 0.0
                            if isinstance(ind_dict, dict) and 'average' in ind_dict and ind_dict['average'] is not None:
                                try:
                                    ind_avg = float(ind_dict['average'])
                                except (ValueError, TypeError):
                                    ind_avg = 0.0
                            elif isinstance(ind_dict, dict) and 'value' in ind_dict and ind_dict['value'] is not None:
                                try:
                                    ind_avg = float(ind_dict['value'])
                                except (ValueError, TypeError):
                                    ind_avg = 0.0
                            elif applied_vals:
                                ind_avg = sum(applied_vals) / len(applied_vals)

                            ind_data[ikey] = {
                                **sub_vals,
                                'average': round(ind_avg, 2)
                            }
                            eval_ind_avgs.append(ind_avg)

                        total_score = e.index if e.index is not None else sum(eval_ind_avgs)

                        evaluators_list.append({
                            'id': str(e.id),
                            'name': e.name,
                            'cleanlinessAndCareOfSpaces': ind_data['cleanlinessAndCareOfSpaces'],
                            'wasteManagement': ind_data['wasteManagement'],
                            'biodiversityConservation': ind_data['biodiversityConservation'],
                            'waterUse': ind_data['waterUse'],
                            'communityRelations': ind_data['communityRelations'],
                            'totalIndex': round(total_score, 2)
                        })

                    if evaluators_list:
                        environmentalData['hasData'] = True
                        lapse_summary = {}

                        for ind_def in indicator_definitions:
                            ikey = ind_def['key']
                            isub = ind_def['subcriteria']
                            lapse_summary[ikey] = {}

                            for sc in isub:
                                valid_vals = [ev[ikey][sc] for ev in evaluators_list if ev[ikey].get(sc) is not None]
                                avg_sc = sum(valid_vals) / len(valid_vals) if valid_vals else 0.0
                                lapse_summary[ikey][sc] = round(avg_sc, 2)

                            avg_ind = sum(ev[ikey]['average'] for ev in evaluators_list) / len(evaluators_list)
                            lapse_summary[ikey]['average'] = round(avg_ind, 2)

                        sum_total_index = sum(ev['totalIndex'] for ev in evaluators_list) / len(evaluators_list)
                        lapse_summary['totalIndex'] = round(sum_total_index, 2)

                        environmentalData['lapses'][lapse_key]['evaluators'] = evaluators_list
                        environmentalData['lapses'][lapse_key]['summary'] = lapse_summary

            data['environmental'] = environmentalData
            return data, 200
        else:
            raise RegisterNotFound(message="Record not found",
                                   status_code=404,
                                   payload={"schoolYearId": schoolYearId, "schoolId": schoolId})

    def get_pins_report(self, schoolYearId):
        schoolYear = SchoolYear.objects(id=schoolYearId).first()
        if not schoolYear:
            raise RegisterNotFound(message="School year not found",
                                   status_code=404,
                                   payload={"schoolYearId": schoolYearId})

        pecas = PecaProject.objects(
            schoolYear=schoolYearId,
            isDeleted=False
        )

        data = {
            'schoolYear': schoolYear.name,
            'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ'),
            'schools': []
        }

        for peca in pecas:
            enrollment = 0
            for section in peca.school.sections:
                if not section.isDeleted:
                    for student in section.students:
                        if not student.isDeleted:
                            enrollment += 1

            school_data = {
                'schoolName': peca.school.name,
                'state': peca.school.addressState.name if peca.school.addressState else "",
                'enrollment': enrollment,
                'readingOverGoal': 0,
                'mathOverGoal': 0,
                'logicOverGoal': 0
            }

            for section in peca.school.sections:
                if section.grade.isdigit() and int(section.grade) > 0 and not section.isDeleted:
                    for student in section.students:
                        if not student.isDeleted:
                            studentLapse = student.lapse3
                            if studentLapse:
                                if studentLapse.wordsPerMinIndex is not None and float(studentLapse.wordsPerMinIndex) >= 100:
                                    school_data['readingOverGoal'] += 1
                                if studentLapse.multiplicationsPerMinIndex is not None and float(studentLapse.multiplicationsPerMinIndex) >= 100:
                                    school_data['mathOverGoal'] += 1
                                if studentLapse.operationsPerMinIndex is not None and float(studentLapse.operationsPerMinIndex) >= 100:
                                    school_data['logicOverGoal'] += 1

            data['schools'].append(school_data)

        # Sort schools by state and schoolName case-insensitively
        data['schools'] = sorted(data['schools'], key=lambda x: (x['state'].lower(), x['schoolName'].lower()))

        return data, 200
