"""Verifica que un script del backend pueda correr en el servidor de produccion.

- Sintaxis compatible con Python 3.5 (f-strings y anotaciones de variables no).
- Cabecera utf-8 si hay caracteres no ASCII.
- Sin rutas fijas a /home (en el servidor el codigo esta en /home/amblema/amblema-back).

Uso: python3 check_script.py scripts/mi_script.py [otros.py ...]
Sale con 1 si encuentra problemas. Necesita Python >= 3.8 para correr.
"""
import ast
import sys


def check(path):
    with open(path, encoding='utf-8') as source_file:
        source = source_file.read()
    problems = []
    try:
        tree = ast.parse(source, filename=path, feature_version=(3, 5))
    except SyntaxError as e:
        return ['{}:{}: {}'.format(path, e.lineno, e.msg)]
    for node in ast.walk(tree):
        # feature_version no detecta f-strings (3.6+): se buscan en el AST
        if isinstance(node, ast.JoinedStr):
            problems.append('{}:{}: f-string (requiere Python 3.6+)'.format(path, node.lineno))
        # Ruta del contenedor local: en el servidor no existe (usar la raiz desde __file__)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and (
                node.value == '/home' or node.value.startswith('/home/')):
            problems.append('{}:{}: ruta fija "{}" (resolver la raiz desde __file__)'.format(
                path, node.lineno, node.value))
    if not source.startswith('# -*- coding: utf-8 -*-') and any(ord(c) > 127 for c in source):
        problems.append('{}:1: hay caracteres no ASCII sin "# -*- coding: utf-8 -*-" en la primera linea'.format(path))
    return problems


if __name__ == '__main__':
    found = [problem for path in sys.argv[1:] for problem in check(path)]
    print('\n'.join(found) if found else 'OK: compatible con Python 3.5')
    sys.exit(1 if found else 0)
