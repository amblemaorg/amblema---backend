# -*- coding: utf-8 -*-
"""
Sincroniza el `order` de las actividades de los PECAs del año escolar activo con el
configurado en pecaSetting (los PECAs creados antes del fix quedaban con order=100).

Solo toca campos `order`. Compatible con Python 2.7 (producción) y 3.6 (Docker local).

Uso:
  python scripts/fix_peca_activity_order.py                      # simulación, no escribe
  python scripts/fix_peca_activity_order.py --peca <id> --peca <id>
  python scripts/fix_peca_activity_order.py --apply              # escribe + respaldo JSON
  python scripts/fix_peca_activity_order.py --restore <respaldo.json>

Conexión: variable de entorno DB_URL, --db-url, o DB_URL en el .env del repositorio.
"""
from __future__ import print_function, unicode_literals

import argparse
import io
import json
import os
import sys
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient

PY2 = sys.version_info[0] < 3

# pecaSetting key -> key in the PECA lapse
FIXED_ACTIVITIES = [
    ('initialWorkshop', 'initialWorkshop'),
    ('ambleCoins', 'ambleCoins'),
    ('lapsePlanning', 'lapsePlanning'),
    ('mathOlympic', 'olympics'),
    ('readingOlympics', 'readingOlympics'),
    ('annualPreparation', 'annualPreparation'),
    ('annualConvention', 'annualConvention'),
    ('specialLapseActivity', 'specialActivity'),
]
LAPSES = ('lapse1', 'lapse2', 'lapse3')


def out(msg=''):
    # py2 + stdout redirected (supervisor/log file) defaults to ascii; force utf-8
    if PY2:
        sys.stdout.write((msg + '\n').encode('utf-8'))
    else:
        print(msg)
    sys.stdout.flush()


def read_db_url(cli_value):
    if cli_value:
        return cli_value
    if os.getenv('DB_URL'):
        return os.getenv('DB_URL')
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(env_path):
        with io.open(env_path, encoding='utf-8') as env_file:
            for line in env_file:
                line = line.strip()
                if line.startswith('DB_URL='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    return None


def get_database(client):
    try:
        return client.get_default_database()
    except Exception:
        out('Error: DB_URL debe incluir el nombre de la base (ej. .../amblema?authSource=admin)')
        sys.exit(1)


def compute_changes(peca, setting):
    """Returns [(filter_extra, path, old, new)] for every order out of sync."""
    changes = []
    for lapse in LAPSES:
        settingLapse = setting.get(lapse) or {}
        pecaLapse = peca.get(lapse) or {}

        for settingKey, pecaKey in FIXED_ACTIVITIES:
            current = pecaLapse.get(pecaKey)
            expected = (settingLapse.get(settingKey) or {}).get('order')
            if isinstance(current, dict) and expected is not None and current.get('order') != expected:
                path = '{}.{}.order'.format(lapse, pecaKey)
                changes.append(({}, path, current.get('order'), expected))

        expectedById = {}
        for activity in settingLapse.get('activities') or []:
            if not activity.get('isDeleted') and activity.get('order') is not None:
                expectedById[str(activity.get('id'))] = activity.get('order')

        for i, activity in enumerate(pecaLapse.get('activities') or []):
            expected = expectedById.get(str(activity.get('id')))
            if expected is not None and activity.get('order') != expected:
                # Guard the positional path with the id, in case the array changed meanwhile
                guard = {'{}.activities.{}.id'.format(lapse, i): activity.get('id')}
                path = '{}.activities.{}.order'.format(lapse, i)
                changes.append((guard, path, activity.get('order'), expected))
    return changes


def activity_label(peca, path):
    parts = path.split('.')
    if parts[1] == 'activities':
        activity = peca[parts[0]]['activities'][int(parts[2])]
        return '{} / {}'.format(parts[0], activity.get('name') or activity.get('id'))
    return '{} / {}'.format(parts[0], parts[1])


def restore(db, backup_path):
    with io.open(backup_path, encoding='utf-8') as backup_file:
        entries = json.load(backup_file)
    restored = 0
    for entry in entries:
        query = {'_id': ObjectId(entry['pecaId'])}
        query.update(entry['guard'])
        result = db.peca_project.update_one(query, {'$set': {entry['path']: entry['old']}})
        restored += result.modified_count
    out('Restaurados {} de {} valores desde {}'.format(restored, len(entries), backup_path))


def main():
    parser = argparse.ArgumentParser(description='Sincroniza el order de actividades de los PECAs con pecaSetting')
    parser.add_argument('--apply', action='store_true', help='escribe los cambios (por defecto solo simula)')
    parser.add_argument('--peca', action='append', default=[], help='limita a este id de PECA (repetible)')
    parser.add_argument('--db-url', help='URL de Mongo (por defecto DB_URL)')
    parser.add_argument('--restore', help='restaura los valores de un respaldo generado con --apply')
    args = parser.parse_args()

    db_url = read_db_url(args.db_url)
    if not db_url:
        out('Error: no se encontró DB_URL (variable de entorno, --db-url o .env)')
        sys.exit(1)
    client = MongoClient(db_url)
    db = get_database(client)

    if args.restore:
        restore(db, args.restore)
        return

    schoolYear = db.school_years.find_one({'isDeleted': False, 'status': '1'}, {'name': 1, 'pecaSetting': 1})
    if not schoolYear or not schoolYear.get('pecaSetting'):
        out('Error: no hay año escolar activo con pecaSetting')
        sys.exit(1)
    setting = schoolYear['pecaSetting']

    query = {'schoolYear': schoolYear['_id'], 'isDeleted': False}
    if args.peca:
        query['_id'] = {'$in': [ObjectId(pecaId) for pecaId in args.peca]}
    projection = {'school.name': 1, 'lapse1': 1, 'lapse2': 1, 'lapse3': 1}
    pecas = list(db.peca_project.find(query, projection))

    out('Año escolar activo: {}'.format(schoolYear.get('name')))
    out('Modo: {}'.format('APLICAR' if args.apply else 'SIMULACIÓN (no escribe)'))
    out('PECAs revisados: {}'.format(len(pecas)))
    out()

    backup = []
    pecasWithChanges = 0
    for peca in pecas:
        changes = compute_changes(peca, setting)
        if not changes:
            continue
        pecasWithChanges += 1
        out('{} ({})'.format((peca.get('school') or {}).get('name', '').strip(), peca['_id']))
        for guard, path, old, new in changes:
            out('   {}: {} -> {}'.format(activity_label(peca, path), old, new))
            backup.append({'pecaId': str(peca['_id']), 'guard': guard, 'path': path, 'old': old, 'new': new})

    out()
    out('PECAs con desorden: {} | valores a corregir: {}'.format(pecasWithChanges, len(backup)))

    if not args.apply or not backup:
        if not args.apply and backup:
            out('Nada escrito. Ejecuta con --apply para corregir.')
        return

    backup_path = os.path.abspath('peca_order_backup_{}.json'.format(datetime.now().strftime('%Y%m%d_%H%M%S')))
    content = json.dumps(backup, ensure_ascii=False, indent=2)
    if PY2 and isinstance(content, bytes):  # py2 returns str when everything is ascii
        content = content.decode('utf-8')
    with io.open(backup_path, 'w', encoding='utf-8') as backup_file:
        backup_file.write(content)
    out('Respaldo: {}'.format(backup_path))

    updated = 0
    for entry in backup:
        query = {'_id': ObjectId(entry['pecaId'])}
        query.update(entry['guard'])
        result = db.peca_project.update_one(query, {'$set': {entry['path']: entry['new']}})
        updated += result.modified_count
    out('Valores actualizados: {} de {}'.format(updated, len(backup)))
    if updated != len(backup):
        out('Aviso: algunos valores no se actualizaron (el PECA cambió durante la ejecución). Vuelve a simular.')


if __name__ == '__main__':
    main()
