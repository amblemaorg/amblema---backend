# Premios Escuela HQS: criterio doble y columna AmbLeMario — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El premio HQS se otorga solo si el Índice Integral **y** el Índice Docente alcanzan cada uno el mínimo del nivel, y el reporte muestra al final si el AmbLeMario está habilitado para descarga.

**Architecture:** La regla vive en `app/helpers/hqs_award_helper.py` (fuente única). El servicio `hqs_award_service.py` la aplica, reordena por nivel de premio y añade `yearbookDownloadEnabled` a cada fila. El backoffice solo pinta: columna nueva con ícono, nota de reglas actualizada en pantalla, PDF y Excel.

**Tech Stack:** Python 2.7 (prod) / 3.6 (Docker), Flask-RESTful, MongoEngine 0.24.1, `unittest`. Angular 11.2.14, Nebular 7 (`nb-icon`), pdfmake 0.2, xlsx-js-style.

**Spec:** `docs/superpowers/specs/2026-11-14-premios-escuela-hqs-design.md` (reglas originales) + este plan (cambios pedidos por el Ing. Fidel el 2026-11-18).

## Global Constraints

- Rama: **mantener `feat/coevaluacion-docente`** en backend y backoffice. No crear ramas. No tocar `master`.
- Tareas **secuenciales**: no empezar una hasta que la anterior pase su verificación y su revisión.
- **Sin commits** hasta que el Ing. Fidel lo indique.
- Código compatible con Python 2.7: `from __future__ import division`, sin f-strings, sin anotaciones de tipo.
- No tocar archivos protegidos (`.env*`, `docker-compose*.yml`, `Dockerfile`, `*.bson`).
- Umbrales sin cambio: ORO 80, PLATA 60, BRONCE 40, comparación **inclusiva (≥)**.
- Nivel = el más alto cuyo `minPercentage` cumplen **ambos** índices (equivale a evaluar `min(integral, docente)`).
- Respuesta JSON: solo se **añade** `yearbookDownloadEnabled: bool` por escuela. No se quita ni renombra ningún campo (`finalIndex` se conserva como dato informativo, columna "Promedio").
- Backoffice: sin tests automatizados; validación manual.
- Batería del backend (dentro del contenedor):
  `docker exec amblema_development_back sh -c 'cd /home && python -m coverage run --source=app --omit="app/tests/*,app/scripts/*" -m unittest discover -s app/tests -p "*_test.py" -t . && python -m coverage report'`

## Decisiones (revisar antes de ejecutar)

- **D1 — "≥" y no ">":** el pedido dice "> 80", pero la tabla vigente y la nota del reporte usan "Oro ≥ 80". Se mantiene **≥**. Si debe ser estricto, cambiar solo `get_award` y los límites de su prueba.
- **D2 — Orden de la tabla:** con la regla nueva, una escuela PLATA puede tener mayor promedio que una ORO (p. ej. 100 y 79 → promedio 89,5, PLATA). Se ordena por **nivel** (ORO, PLATA, BRONCE, Sin premio, Incompletos), luego `finalIndex` descendente, luego nombre.
- **D3 — AmbLeMario en cualquier año:** la columna muestra el valor guardado de `yearbookDownloadEnabled` del PECA, también en años cerrados (donde ya no se puede cambiar).
- **D4 — Ícono solo en pantalla:** pantalla = `nb-icon icon="checkmark-outline"`, vacío si no. PDF y Excel = texto **"Sí"** o vacío (la fuente Roboto de pdfmake no trae el carácter ✓).

## Review Focus

1. Integral alto y docente justo bajo el corte (p. ej. 95 y 79,99) → PLATA, no ORO.
2. Ambos exactamente en el corte (80 y 80; 40 y 40) → ORO / BRONCE.
3. Uno ≥ 40 y el otro < 40 (p. ej. 90 y 39,99) → "Sin premio", aunque el promedio sea ≥ 60.
4. PECA sin campo `yearbookDownloadEnabled` en Mongo (documentos viejos) → `false`, sin error.
5. Escuela "Datos incompletos" → nunca premio; la columna AmbLeMario igual se muestra.

---

### Task 1: Regla de premio con criterio doble (backend)

**Modelo sugerido:** Sonnet 5.5 (lógica acotada, pruebas claras).

**Files:**
- Modify: `amblema---backend/app/helpers/hqs_award_helper.py` (docstring de reglas y `get_award`)
- Modify: `amblema---backend/app/services/hqs_award_service.py` (`build_school_row`, `sort_schools`)
- Test: `amblema---backend/app/tests/unitary/hqs_award_helper_test.py`
- Test: `amblema---backend/app/tests/unitary/hqs_award_service_test.py`
- Test: `amblema---backend/app/tests/integration/hqs_award_report_test.py`

**Interfaces:**
- Produces: `get_award(integral, teacherIndex) -> dict | None` (antes `get_award(finalIndex)`). Devuelve `None` si alguno es `None`.
- Produces: `sort_schools(schools) -> list` ordena por rango `gold, silver, bronze, none, incomplete`; empate → `finalIndex` desc (None al final) → nombre sin mayúsculas.
- `final_index` no cambia (sigue siendo el promedio, solo informativo).

- [ ] **Step 1: Reescribir `test_award_boundaries` en `hqs_award_helper_test.py`**

```python
def test_award_requires_both_indexes(self):
    self.assertEqual(get_award(100, 100)["code"], "gold")
    self.assertEqual(get_award(80.0, 80.0)["code"], "gold")
    self.assertEqual(get_award(95.0, 79.99)["code"], "silver")
    self.assertEqual(get_award(79.99, 95.0)["code"], "silver")
    self.assertEqual(get_award(60.0, 100)["code"], "silver")
    self.assertEqual(get_award(100, 59.99)["code"], "bronze")
    self.assertEqual(get_award(40.0, 40.0)["code"], "bronze")
    self.assertIsNone(get_award(90.0, 39.99))   # promedio 64,99, pero docente < 40
    self.assertIsNone(get_award(None, 90))
    self.assertIsNone(get_award(90, None))
```

- [ ] **Step 2: Ajustar `hqs_award_service_test.py::test_sort_schools`** — añadir una fila `{"name": "f", "finalIndex": 89.5, "award": "silver", "status": "awarded"}` y esperar `["A", "b", "f", "e", "d", "a2", "C"]` (la PLATA con 89,5 queda **después** de las ORO con 91,25 y antes de la PLATA con 65). Añadir `test_sort_gold_before_higher_average_silver`: ORO con `finalIndex` 80 y PLATA con 89,5 → ORO primero. Actualizar `test_count_schools` si cambia el conteo por la fila nueva (`silver: 2`).

- [ ] **Step 3: Pruebas de integración en `hqs_award_report_test.py`**
  - Nueva `test_high_integral_low_teacher_is_silver`: lapso 3 con los 3 índices en 100, evaluador 35 (IAA 100) → integral 100; una coevaluación con puntaje 3 → docente 60 %. Esperar `integralIndex 100.0`, `teacherIndex 60.0`, `finalIndex 80.0`, `award "silver"`. (Antes habría sido ORO por promedio 80.)
  - Nueva `test_one_index_below_40_has_no_award`: integral 100 (como arriba), coevaluación puntaje 1 (20 %) → `finalIndex 60.0`, `status "none"`, `award None`.
  - `test_iaa_uses_only_valid_lapse3_evaluators` sigue en BRONCE (47,5 y 40): no cambia. `test_report_caps_and_awards_gold` (92,5 y 90): no cambia.

- [ ] **Step 4: Correr las pruebas tocadas y ver que fallan**

Run: `docker exec amblema_development_back sh -c 'cd /home && python -m unittest app.tests.unitary.hqs_award_helper_test app.tests.unitary.hqs_award_service_test app.tests.integration.hqs_award_report_test'`
Expected: FAIL (`get_award` recibe 1 argumento; orden distinto; las nuevas de integración dan ORO/BRONCE).

- [ ] **Step 5: Implementar**
  - `get_award(integral, teacherIndex)`: recorre `AWARD_LEVELS` y devuelve el primero que cumplan **ambos** (`>= minPercentage`).
  - `build_school_row`: `award = get_award(integral, teacherIndex)`; `finalIdx` se sigue calculando con `final_index`.
  - `sort_schools`: clave `(rango_del_nivel, finalIndex is None, -(finalIndex or 0), nombre.lower())` con rango `{"gold":0,"silver":1,"bronze":2}` y, sin premio, `3` si `status == "none"` y `4` si `"incomplete"`.
  - Docstring del helper: reemplazar las líneas "Índice final…" y "Premio…" por: "Índice final: promedio informativo. Premio: primer nivel cuyo minPercentage cumplen a la vez el índice integral y el índice docente; si alguno es < 40 no hay premio."

- [ ] **Step 6: Correr las mismas pruebas**
Expected: OK.

- [ ] **Step 7: Batería completa** (comando de Global Constraints). Expected: sin fallos nuevos; si fallan las 6 conocidas por permisos de `resources/files/*` (ver HANDOFF), anotarlo y no tocarlas.

---

### Task 2: `yearbookDownloadEnabled` en cada fila del reporte (backend)

**Modelo sugerido:** Haiku 5.5 (cambio mecánico de 3 líneas + prueba).

**Files:**
- Modify: `amblema---backend/app/services/hqs_award_service.py` (`report`: `.only(...)`; `build_school_row`: parámetro nuevo)
- Test: `amblema---backend/app/tests/integration/hqs_award_report_test.py`

**Interfaces:**
- Consumes: `build_school_row` de Task 1.
- Produces: cada elemento de `schools` lleva `"yearbookDownloadEnabled": bool`. `build_school_row(..., yearbookDownloadEnabled=False)` como último parámetro con valor por defecto.

- [ ] **Step 1: Prueba de integración** — `newPeca` acepta `yearbookDownloadEnabled=False` y lo pasa al `PecaProject`. Nueva `test_row_reports_yearbook_download_flag`: un PECA con `True` → `schools[0]["yearbookDownloadEnabled"] is True`. En otra prueba ya existente (p. ej. `test_low_score_has_no_award`) añadir `assertIs(s["yearbookDownloadEnabled"], False)`.
- [ ] **Step 2: Correr `app.tests.integration.hqs_award_report_test`** → FAIL (`KeyError`).
- [ ] **Step 3: Implementar** — añadir `'yearbookDownloadEnabled'` al `.only(...)` de `PecaProject`; pasar `yearbookDownloadEnabled=bool(peca.yearbookDownloadEnabled)`; incluir la clave en el dict de la fila.
- [ ] **Step 4: Correr la prueba** → OK. Batería completa → sin fallos nuevos.

---

### Task 3: Backoffice — columna AmbLeMario y nota de reglas

**Modelo sugerido:** Sonnet 5.5 (UI + exportaciones, sin lógica nueva).

**Files:**
- Modify: `amblema-backoffice/src/app/_models/report/hqs-award-report.model.ts` (`HqsAwardSchool.yearbookDownloadEnabled: boolean`)
- Modify: `amblema-backoffice/src/app/pages/report/hqs-award-report/hqs-award-report.component.html` (columna y nota)
- Modify: `amblema-backoffice/src/app/pages/report/hqs-award-report/hqs-award-report.component.scss` (centrar la celda del ícono, color verde `#81b03e`)
- Modify: `amblema-backoffice/src/app/pages/report/hqs-award-report/hqs-award-report-export.service.ts` (`NOTE`, PDF y Excel)

**Interfaces:**
- Consumes: `yearbookDownloadEnabled: boolean` de Task 2.

- [ ] **Step 1: Modelo** — añadir `yearbookDownloadEnabled: boolean;` al final de `HqsAwardSchool`.
- [ ] **Step 2: Pantalla** — última columna `<th class="center">AmbLeMario</th>`; celda `<td class="center"><nb-icon *ngIf="school.yearbookDownloadEnabled" icon="checkmark-outline" status="success" title="Descarga habilitada"></nb-icon></td>`. Sin ícono → celda vacía.
- [ ] **Step 3: Texto de la nota** (pantalla y constante `NOTE`, idéntico en ambos):
  `Índice Integral = promedio de IAA, PPM, M2M y 60LM del lapso 3 (máximo 100 cada uno; IAA convertido de 35 puntos a %). Premio: Oro si Índice Integral ≥ 80 e Índice Docentes HQS ≥ 80; Plata si ambos ≥ 60; Bronce si ambos ≥ 40. Promedio: solo informativo.`
- [ ] **Step 4: PDF** — añadir `'AmbLeMario'` al final de los encabezados, un `'auto'` más en `widths` y la celda `{ text: s.yearbookDownloadEnabled ? 'Sí' : '', alignment: 'center' }`.
- [ ] **Step 5: Excel** — columna `'AmbLeMario'` al final (después de `'Falta'`), valor `s.yearbookDownloadEnabled ? 'Sí' : ''`. Revisar `appendSheet`: hoy la **última** columna recibe ancho 36 (pensado para "Falta"); ajustar para que "Falta" conserve 36 y "AmbLeMario" quede en 14.
- [ ] **Step 6: Compilar** — `cd amblema-backoffice && npx tsc --noEmit -p tsconfig.app.json` → sin errores. `ng build` dentro del contenedor del backoffice si está disponible; si no, dejarlo como pendiente en el HANDOFF.

---

### Task 4: Revisión final, verificación manual y HANDOFF

**Modelo sugerido:** Opus 5.5 (revisión de la rama completa).

- [ ] **Step 1:** Revisar el diff de backend y backoffice contra Global Constraints, Decisiones y Review Focus.
- [ ] **Step 2:** Verificación manual (Ing. Fidel):
  - `GET /statistics/hqsawardsreport/<schoolYearId>` (token admin): cada escuela trae `yearbookDownloadEnabled`; una con integral alto y docente < 80 sale PLATA o menor.
  - Backoffice `localhost:2004` → Reportes → Premios Escuela HQS → año 2026-2027 → Consultar: columna "AmbLeMario" al final con ✓ donde se habilitó en Proyectos → "Descarga AmbLeMario"; orden ORO → PLATA → BRONCE → Sin premio → Incompletos.
  - Cambiar el interruptor en Proyectos, volver a consultar: aparece / desaparece el ✓.
  - Exportar PDF y Excel: columna "AmbLeMario" con "Sí" o vacío; nota nueva.
- [ ] **Step 3:** Actualizar `HANDOFF.md` (entrada 2026-11-18: archivos, decisiones D1–D4, totales de la batería).
- [ ] **Step 4:** Commit **solo** cuando el Ing. Fidel lo indique.
