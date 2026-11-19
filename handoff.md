# handoff — amblema---backend

## Estado actual
Rama `fix/iaa-amblemario-sync` (commit `d251b65`), PR #126 abierto contra `master`. Batería: 290 pruebas OK.

## Hecho
- 2026-11-19 — IAA (diagnóstico de ambiente) en cero en el AmbLeMario (`/pdf-template/yearbook`):
  - Causa: el PDF usa la foto de la última aprobación del AmbLeMario; `submit_evaluation` no la sincronizaba,
    así que las evaluaciones enviadas después de aprobar quedaban fuera (`environmentalSummary` en `[0,0,0,0,0]`).
  - `services/environmental_diagnostic_service.py`: tras guardar la evaluación llama a
    `update_yearbook_data_in_approval` (vía `_sync_yearbook`; si falla, solo lo registra y la evaluación se guarda igual).
    Se añadió `# -*- coding: utf-8 -*-` (el archivo tenía tildes sin cabecera: SyntaxError en Python 2.7).
  - `scripts/refresh_environmental_summaries.py` (Python 2.7/3.6): resincroniza el IAA de los PECA con evaluaciones
    enviadas. `--dry-run` lista, `--all-years` incluye años anteriores. Ejecutado en la BD local: 26 PECA actualizados.
  - Pruebas: `maintenance_scripts_test.py` (envío actualiza la solicitud pendiente; fallo de sync no rompe el envío) y
    `unitary/environmental_diagnostic_test.py` (llama a la sync con el `pecaId` del evaluador).

## Pendiente
- Revisar y fusionar el PR #126.
- Producción: desplegar el cambio y luego correr el script (primero `--dry-run`).

## Decisiones y notas
- `update_yearbook_data_in_approval` actualiza la solicitud pendiente y solo la aprobación más reciente
  (también reescribe `sections` y `diagnosticSummary`, como ya hacían los otros diagnósticos).
- El script toma la raíz del backend desde su propia ruta (no `/home`): en producción vive en `~/amblema-back`.
- Devuelve `False` si no hay aprobación en `yearbook_approval` aunque haya actualizado la pendiente; el script lo
  cuenta como "omitido".
