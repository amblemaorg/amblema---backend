# -*- coding: utf-8 -*-
"""
Actualiza el IAA (environmentalSummary) del AmbLeMario con los resultados reales de los
evaluadores del diagnostico de ambiente.

Corrige los PECA cuyo AmbLeMario aprobado/pendiente quedo con el IAA en cero porque los
evaluadores enviaron sus resultados despues de la ultima aprobacion.

Solo toca los PECA que tienen al menos un evaluador con evaluacion enviada. Por cada uno
llama a update_yearbook_data_in_approval (pendiente + ultimo aprobado), igual que el backend.

Compatible con Python 2.7 y 3.5+. Uso (desde la raiz del backend, con el venv activo):

    python scripts/refresh_environmental_summaries.py --dry-run      # solo lista
    python scripts/refresh_environmental_summaries.py                # ano escolar activo
    python scripts/refresh_environmental_summaries.py --all-years    # todos los anos

Variables (DB_URL, INSTANCE, ...), por prioridad:
  1. Las ya definidas en el entorno (p. ej. INSTANCE=production en la linea de comando).
  2. environment= del programa de supervisor (/etc/supervisor/conf.d/gunicorn.conf, o la ruta en
     SUPERVISOR_CONF): las mismas que usa gunicorn en el servidor.
  3. El .env de la raiz del backend (entorno local).
No se imprime ningun valor.
"""
import io
import os
import re
import sys

# Raiz del backend (carpeta padre de scripts/), sirva en Docker (/home) o en el servidor (~/amblema-back)
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_ROOT)

SUPERVISOR_CONF = os.getenv('SUPERVISOR_CONF', '/etc/supervisor/conf.d/gunicorn.conf')

# KEY="valor" | KEY='valor' | KEY=valor (formato de environment= en supervisor)
SUPERVISOR_PAIR = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)=("(?:[^"\\]|\\.)*"|\'[^\']*\'|[^,\s]*)')


def set_missing(variables):
    """Define solo las variables que aun no existen; devuelve cuantas se cargaron."""
    loaded = 0
    for key, value in variables:
        if key and not os.getenv(key):
            os.environ[key] = value
            loaded += 1
    return loaded


def read_supervisor_environment(path):
    """Pares (clave, valor) de environment= en la config de supervisor (admite lineas de continuacion)."""
    with io.open(path, encoding='utf-8') as conf_file:
        lines = conf_file.read().splitlines()

    value_lines = []
    collecting = False
    for line in lines:
        if collecting:
            # En supervisor, una linea indentada continua el valor anterior
            if line[:1] in (' ', '\t') and line.strip() and not line.strip().startswith(('#', ';')):
                value_lines.append(line.strip())
                continue
            collecting = False
        match = re.match(r'\s*environment\s*=\s*(.*)$', line)
        if match:
            value_lines.append(match.group(1))
            collecting = True

    pairs = []
    for key, value in SUPERVISOR_PAIR.findall(' '.join(value_lines)):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        pairs.append((key, value))
    return pairs


def read_env_file(path):
    pairs = []
    with io.open(path, encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            if line.startswith('export '):
                line = line[len('export '):]
            key, value = line.split('=', 1)
            pairs.append((key.strip(), value.strip().strip('"').strip("'")))
    return pairs


def load_environment():
    if os.path.exists(SUPERVISOR_CONF):
        try:
            loaded = set_missing(read_supervisor_environment(SUPERVISOR_CONF))
            print("Variables de supervisor ({}): {} cargadas".format(SUPERVISOR_CONF, loaded))
        except (IOError, OSError) as e:
            print("No se pudo leer {} ({}). Ejecute con un usuario que pueda leerlo "
                  "o exporte DB_URL antes de correr el script.".format(SUPERVISOR_CONF, e.strerror or e))

    env_path = os.path.join(BACKEND_ROOT, '.env')
    if os.path.exists(env_path):
        loaded = set_missing(read_env_file(env_path))
        print("Variables de {}: {} cargadas".format(env_path, loaded))

    if not os.getenv('DB_URL'):
        print("ERROR: DB_URL no esta definida (ni en el entorno, ni en {}, ni en .env).".format(SUPERVISOR_CONF))
        sys.exit(1)


load_environment()

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
