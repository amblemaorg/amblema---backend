---
name: script-produccion-backend
description: Use when hay que crear o arreglar un script de mantenimiento, migración o reparación de datos en amblema---backend/scripts para correrlo en el servidor de producción, o cuando un script falla en el servidor con "ImportError: No module named 'app'", "TypeError: argument of type 'NoneType' is not iterable" en flask_mongoengine o DB_URL vacía.
---

# Script de producción del backend AmbLeMa

Solo para `amblema---backend`. Un script que funciona en Docker local suele fallar en el servidor: la ruta, la versión
de Python y el origen de las variables son distintos. Este flujo lo deja listo para la primera corrida.

## El servidor (no Docker)

| Elemento | Producción | Docker local |
|---|---|---|
| Código | `/home/amblema/amblema-back` | `/home` |
| Python | `venv/bin/python` **3.5** (no 2.7, aunque CLAUDE.md lo diga) | 3.6 |
| Variables (`DB_URL`, `INSTANCE`…) | `environment=` de `/etc/supervisor/conf.d/gunicorn.conf` | entorno del contenedor y `.env` |
| Usuario | `amblema` (`sudo -iu amblema`) | root |

En el servidor la shell **no** tiene las variables y el `.env` no aplica.

## Estructura del script (`scripts/<nombre>.py`)

1. Primera línea `# -*- coding: utf-8 -*-`.
2. Raíz del backend desde `__file__`, nunca `/home`:
   `BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` y `sys.path.insert(0, BACKEND_ROOT)`.
3. Carga de variables **antes** de `from app import create_app`, sin pisar las ya definidas, con prioridad
   entorno > supervisor (`SUPERVISOR_CONF`, por defecto `/etc/supervisor/conf.d/gunicorn.conf`) > `.env`.
   Si `DB_URL` sigue vacía, terminar con un error claro. Nunca imprimir valores.
   Copiar `load_environment()` y sus funciones de `scripts/refresh_environmental_summaries.py` (implementación de referencia).
4. `app = create_app(os.getenv('INSTANCE', 'development'))` y todo dentro de `with app.app_context():`.
5. **Simula por defecto**; escribe solo con `--apply`. Argumentos con `argparse` o lista blanca: un argumento desconocido
   termina con error.
6. Reutilizar helpers del backend (p. ej. `update_yearbook_data_in_approval`) en vez de reescribir la lógica.
7. Si modifica datos que no se pueden recalcular, guardar antes un respaldo JSON de lo que cambia y ofrecer
   `--restore` (ver `scripts/fix_peca_activity_order.py`).
8. Salida legible: `[i/total] <id>: <acción>` y un resumen final (actualizados / omitidos / con error).
   Código de salida 1 si hubo errores.
9. Sintaxis Python 3.5: sin f-strings, sin anotaciones de variables, solo `.format()`.

## Verificación obligatoria antes de entregarlo

Desde `amblema---backend`:

```bash
# 1. Sintaxis Python 3.5, tildes sin cabecera y rutas fijas a /home
python3 .claude/skills/script-produccion-backend/check_script.py scripts/<nombre>.py

# 2. Como en el servidor: sin DB_URL/INSTANCE en el entorno, desde otra carpeta y
#    con las variables solo en un gunicorn.conf de prueba (armado dentro del contenedor, sin imprimir la clave)
docker exec amblema_development_back sh -c '
printf "[program:gunicorn]\nenvironment=INSTANCE=\"development\",\n    DB_URL=\"%s\"\n" "$DB_URL" > /tmp/fake_gunicorn.conf
cd /tmp && env -u DB_URL -u INSTANCE SUPERVISOR_CONF=/tmp/fake_gunicorn.conf python /home/scripts/<nombre>.py
rm -f /tmp/fake_gunicorn.conf'
```

La prueba 2 debe mostrar `Variables de supervisor (...): 2 cargadas` (o más) y simular contra la BD local. Como
supervisor tiene prioridad sobre `.env`, ese contador prueba que `DB_URL` salió de supervisor. No mover ni editar el
`.env` (archivo protegido).

3. Correr la simulación y, si el Ing. Fidel lo aprueba, `--apply` en la BD local. Revisar en Mongo el resultado de un caso real.
4. Si el script toca lógica del backend, correr la batería de pruebas (comando en `CLAUDE.md`).

## Guía de ejecución (`scripts/<nombre>.md`)

Mismo formato que `scripts/fix_peca_activity_order.md`: qué corrige y qué toca, `sudo -iu amblema`,
`cd /home/amblema/amblema-back`, simulación, `--apply`, verificación, cómo deshacer. Comandos con `venv/bin/python` e
`INSTANCE=production`. Si `amblema` no puede leer `gunicorn.conf`, la alternativa es exportar `DB_URL` con `sudo grep`.

## Entrega

- Rama propia desde `master`, commit (script + `.md` + `handoff.md`), push y PR. `master` está protegida: el Ing. Fidel fusiona.
- Antes de cada push extra a la rama: `gh pr view <n> --json state`. Si ya está `MERGED`, el commit nuevo va en un PR nuevo.
- La corrida en producción la hace el Ing. Fidel. No marcarla como hecha en `handoff.md` sin ver su salida.

## Errores típicos en el servidor

| Error | Causa | Arreglo |
|---|---|---|
| `ImportError: No module named 'app'` | `sys.path` con `/home` fijo | Raíz desde `__file__` (paso 2) |
| `TypeError: argument of type 'NoneType' is not iterable` en `flask_mongoengine` | `DB_URL` vacía | Leer supervisor (paso 3) |
| `No se pudo leer /etc/supervisor/conf.d/gunicorn.conf` | Sin permiso de lectura | `export DB_URL="$(sudo grep -o 'DB_URL="[^"]*"' /etc/supervisor/conf.d/gunicorn.conf \| cut -d'"' -f2)"` |
| `SyntaxError` con f-string o anotación | Sintaxis 3.6+ | `check_script.py` |
| `SyntaxError: Non-ASCII character` | Tildes sin cabecera de codificación | `# -*- coding: utf-8 -*-` |
