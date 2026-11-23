# handoff — amblema---backend

## Estado actual
Rama `master` al día con `origin/master` (`521b0e1`). Arreglo del IAA del AmbLeMario fusionado (PR #126, #127 y #128).
Falta confirmar la corrida del script en producción. Batería: 290 pruebas OK.

## Hecho
- 2026-11-19 — IAA (diagnóstico de ambiente) en cero en el AmbLeMario (`/pdf-template/yearbook`):
  - Causa: el PDF usa la foto de la última aprobación del AmbLeMario; `submit_evaluation` no la sincronizaba,
    así que las evaluaciones enviadas después de aprobar quedaban fuera (`environmentalSummary` en `[0,0,0,0,0]`).
  - `services/environmental_diagnostic_service.py`: tras guardar la evaluación llama a
    `update_yearbook_data_in_approval` (vía `_sync_yearbook`; si falla, solo lo registra y la evaluación se guarda igual).
    Se añadió `# -*- coding: utf-8 -*-` (el archivo tenía tildes sin cabecera).
  - `scripts/refresh_environmental_summaries.py`: resincroniza el IAA de los PECA con evaluaciones enviadas.
    `--dry-run` lista, `--all-years` incluye años anteriores. Ejecutado en local (26 PECA).
  - Pruebas: `maintenance_scripts_test.py` (envío actualiza la solicitud pendiente; fallo de sync no rompe el envío) y
    `unitary/environmental_diagnostic_test.py` (llama a la sync con el `pecaId` del evaluador).

## Pendiente
- Confirmar que el script se corrió en producción (sin `--dry-run`) y verificar el PDF del AmbLeMario de U.E.E.R. La Esperanza 2026-2027 (IAA del lapso 1 con datos).
- Opcional: índice compuesto `(pecaId, lapse)` en `environmental_diagnostic_evaluators`.

## Decisiones y notas
- `update_yearbook_data_in_approval` actualiza la solicitud pendiente y solo la aprobación más reciente
  (también reescribe `sections` y `diagnosticSummary`, como ya hacían los otros diagnósticos).
  Devuelve `False` si no hay aprobación en `yearbook_approval` aunque haya actualizado la pendiente.
- Servidor de producción: backend en `/home/amblema/amblema-back`, venv con **Python 3.5** (no 2.7), variables en
  `environment=` de `/etc/supervisor/conf.d/gunicorn.conf` (no en la shell ni en `.env`).
- Los scripts para producción deben: resolver la raíz del backend desde su propia ruta (no `/home`) y leer las variables
  de supervisor. Prioridad en `refresh_environmental_summaries.py`: entorno > supervisor (`SUPERVISOR_CONF`) > `.env`.
- `master` está protegida (requiere revisión): los PR los fusiona el Ing. Fidel.
- Skill `.claude/skills/script-produccion-backend/` (2026-11-19): flujo para scripts que se corren en el servidor, con
  `check_script.py` (sintaxis 3.5, cabecera utf-8, rutas fijas a `/home`) y prueba con un `gunicorn.conf` falso.
