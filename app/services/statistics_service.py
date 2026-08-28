# app/services/statistics_service.py


from app.models.user_model import User
from app.models.school_user_model import SchoolUser
from app.models.coordinator_user_model import CoordinatorUser
from app.models.sponsor_user_model import SponsorUser
from app.models.peca_project_model import PecaProject
from flask import current_app
from mongoengine.connection import get_db
from app.models.school_year_model import SchoolYear


class StatisticsService():

    def get_count_users(self):
        return {
            'coordinators': self.get_count_coordinator(),
            'sponsors': self.get_count_sponsor(),
            'schools': self.get_count_school(),
            'teachers': self.get_count_teacher()
        }

    def get_count_school(self):
        return SchoolUser.objects(isDeleted=False).count()

    def get_count_coordinator(self):
        return CoordinatorUser.objects(isDeleted=False).count()

    def get_count_sponsor(self):
        return SponsorUser.objects(isDeleted=False).count()

    def get_count_teacher(self):
        count = 0
        schools = SchoolUser.objects(
            isDeleted=False, status="1").only('teachers')
        for school in schools:
            count += len(school.teachers.filter(isDeleted=False))

        return count

    def get_count_students(self):
        
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only('nStudents').first()
        if schoolYear and schoolYear.nStudents:
            return schoolYear.nStudents
        else:
            return 0
    
    def get_count_home_page(self):
        nSchools = 0
        nStudents = 0
        nTeachers = 0
        nSponsors = 0
        nCoordinators = 0
        schoolYear = SchoolYear.objects(
            isDeleted=False, status="1").only('nStudents', 'nSchools', 'nTeachers', 'nSponsors', 'nCoordinators').first()
        if schoolYear:
            nSchools = schoolYear.nSchools
            nStudents = schoolYear.nStudents
            nTeachers = schoolYear.nTeachers
            nSponsors = schoolYear.nSponsors
            nCoordinators = schoolYear.nCoordinators
        return {
            'nSchools': nSchools,
            'nStudents': nStudents,
            'nTeachers': nTeachers,
            'nSponsors': nSponsors,
            'nCoordinators': nCoordinators
        }

    def get_diagnostics_last_five_years(self):
        periods = SchoolYear.objects(isDeleted=False).order_by('-createdAt')[:5]

        data = {
            'environmentIndex': [],
            'wordsPerMinIndex': [],
            'multiplicationsPerMinIndex': [],
            'operationsPerMinIndex': [],
            'mathOlympics': [],
            'readingOlympics': []
        }

        from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
        from app.models.peca_project_model import PecaProject

        def get_ind_val(item):
            if not item: return 0.0
            if isinstance(item, dict):
                if 'average' in item and item['average'] is not None:
                    try: return float(item['average'])
                    except (ValueError, TypeError): pass
                if 'value' in item and item['value'] is not None:
                    try: return float(item['value'])
                    except (ValueError, TypeError): pass
            elif isinstance(item, (int, float, str)):
                try: return float(item)
                except (ValueError, TypeError): pass
            return 0.0

        for period in periods:
            # Environmental Diagnostic aggregation for Home Page (optimized with field projections)
            pecas = PecaProject.objects(schoolYear=str(period.id), isDeleted=False).only('id')
            peca_ids = [str(p.id) for p in pecas]
            if peca_ids:
                evaluators = EnvironmentalDiagnosticEvaluator.objects(
                    pecaId__in=peca_ids,
                    hasEvaluated=True,
                    isDeleted=False
                ).only('lapse', 'index', 'results')

                if evaluators:
                    for lapse in [1, 2, 3]:
                        lapse_evals = [e for e in evaluators if str(e.lapse) == str(lapse) and e.index is not None]
                        if lapse_evals:
                            avg_index = round(sum(e.index for e in lapse_evals) / len(lapse_evals), 2)
                            indicators = {
                                'cleanlinessAndCareOfSpaces': round(sum(get_ind_val(e.results.get('cleanlinessAndCareOfSpaces')) for e in lapse_evals) / len(lapse_evals), 2),
                                'wasteManagement': round(sum(get_ind_val(e.results.get('wasteManagement')) for e in lapse_evals) / len(lapse_evals), 2),
                                'biodiversityConservation': round(sum(get_ind_val(e.results.get('biodiversityConservation')) for e in lapse_evals) / len(lapse_evals), 2),
                                'waterUse': round(sum(get_ind_val(e.results.get('waterUse')) for e in lapse_evals) / len(lapse_evals), 2),
                                'communityRelations': round(sum(get_ind_val(e.results.get('communityRelations')) for e in lapse_evals) / len(lapse_evals), 2)
                            }
                            data['environmentIndex'].append({
                                'createdAt': period.createdAt,
                                'label': period.name,
                                'serie': f'Lapso {lapse}',
                                'value': avg_index,
                                'indicators': indicators
                            })

            for diag in ['wordsPerMinIndex', 'multiplicationsPerMinIndex', 'operationsPerMinIndex']:
                hasInfo = False
                for lapse in [1, 2, 3]:
                    if period.diagnostics['lapse{}'.format(
                                lapse)][diag]:
                        hasInfo = True
                if hasInfo:
                    for lapse in [1, 2, 3]:
                        data[diag].append(
                            {
                                'createdAt': period.createdAt,
                                'label': period.name,
                                'serie': 'Lapso {}'.format(lapse),
                                'value': period.diagnostics['lapse{}'.format(
                                    lapse)][diag]
                            }
                        )
            
            # Olympics
            summary = period.olympicsSummary
            for olympicsType in ['math', 'reading']:
                diagKey = 'mathOlympics' if olympicsType == 'math' else 'readingOlympics'
                prefix = 'math' if olympicsType == 'math' else 'reading'
                
                enrolled = getattr(summary, '{}EnrolledCount'.format(prefix))
                if enrolled > 0:
                    gold = getattr(summary, '{}MedalsGold'.format(prefix)) + getattr(summary, '{}MedalsGoldNational'.format(prefix))
                    silver = getattr(summary, '{}MedalsSilver'.format(prefix)) + getattr(summary, '{}MedalsSilverNational'.format(prefix))
                    bronze = getattr(summary, '{}MedalsBronze'.format(prefix)) + getattr(summary, '{}MedalsBronzeNational'.format(prefix))
                    
                    medals_sum = gold + silver + bronze
                    if medals_sum > 0:
                        series_map_totals = {
                            'Oro': gold,
                            'Plata': silver,
                            'Bronce': bronze
                        }
                        for label, value in series_map_totals.items():
                            data[diagKey].append({
                                'createdAt': period.createdAt,
                                'label': period.name,
                                'serie': label,
                                'value': value
                            })

        for diag in data.keys():
            data[diag] = sorted(
                data[diag], reverse=True, key=lambda x: (x['createdAt']))
        return data
