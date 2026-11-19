# -*- coding: utf-8 -*-
"""
Actualiza el IAA (environmentalSummary) del AmbLeMario con los resultados reales de los
evaluadores del diagnostico de ambiente.

Corrige los PECA cuyo AmbLeMario aprobado/pendiente quedo con el IAA en cero porque los
evaluadores enviaron sus resultados despues de la ultima aprobacion.

Solo toca los PECA que tienen al menos un evaluador con evaluacion enviada. Por cada uno
llama a update_yearbook_data_in_approval (pendiente + ultimo aprobado), igual que el backend.

Compatible con Python 2.7 y 3.6. Uso (desde /home, con el venv activo):

    python scripts/refresh_environmental_summaries.py --dry-run      # solo lista
    python scripts/refresh_environmental_summaries.py                # ano escolar activo
    python scripts/refresh_environmental_summaries.py --all-years    # todos los anos

La instancia sale de la variable de entorno INSTANCE (por defecto 'development').
"""
import os
import sys

sys.path.append('/home')

from app import create_app

app = create_app(os.getenv('INSTANCE', 'development'))


def parse_args(argv):
    known = ('--dry-run', '--all-years')
    unknown = [arg for arg in argv if arg not in known]
    if unknown:
        print("Argumentos no reconocidos: {}. Validos: {}".format(', '.join(unknown), ', '.join(known)))
        sys.exit(1)
    return '--dry-run' in argv, '--all-years' in argv


def main(argv):
    dry_run, all_years = parse_args(argv)

    with app.app_context():
        from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
        from app.models.peca_project_model import PecaProject
        from app.models.school_year_model import SchoolYear
        from app.helpers.peca_yearbook_helper import update_yearbook_data_in_approval

        evaluated_peca_ids = EnvironmentalDiagnosticEvaluator.objects(
            hasEvaluated=True, isDeleted=False).distinct('pecaId')

        query = {'id__in': evaluated_peca_ids, 'isDeleted': False}
        if not all_years:
            school_year = SchoolYear.objects(isDeleted=False, status="1").first()
            if not school_year:
                print("No hay ano escolar activo; use --all-years para procesar todos.")
                return 1
            query['schoolYear'] = school_year
            print("Ano escolar activo: {}".format(school_year.name))

        peca_ids = [str(peca_id) for peca_id in PecaProject.objects(**query).scalar('id')]
        total = len(peca_ids)
        print("PECA con evaluaciones ambientales enviadas: {}{}".format(
            total, " (dry-run, no se modifica nada)" if dry_run else ""))

        updated = 0
        skipped = 0
        errors = 0
        for index, peca_id in enumerate(peca_ids, 1):
            evaluators = EnvironmentalDiagnosticEvaluator.objects(
                pecaId=peca_id, hasEvaluated=True, isDeleted=False).count()

            if dry_run:
                print("[{}/{}] PECA {}: {} evaluador(es) con evaluacion".format(index, total, peca_id, evaluators))
                continue

            try:
                peca = PecaProject.objects(id=peca_id).first()
                if peca and update_yearbook_data_in_approval(peca) is not False:
                    updated += 1
                    print("[{}/{}] PECA {}: actualizado ({} evaluador(es))".format(index, total, peca_id, evaluators))
                else:
                    skipped += 1
                    print("[{}/{}] PECA {}: sin aprobacion que actualizar".format(index, total, peca_id))
            except Exception as e:
                errors += 1
                print("[{}/{}] PECA {}: ERROR {}".format(index, total, peca_id, e))

        if not dry_run:
            print("Terminado. Actualizados: {}, omitidos: {}, con error: {}".format(updated, skipped, errors))
        return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
