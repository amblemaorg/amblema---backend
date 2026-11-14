# Premios a la Escuela HQS — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reporte del backoffice "Premios Escuela HQS" que calcula, por año escolar, el Índice Integral AmbLeMa, el Índice de Docentes HQS, su promedio y el premio (Oro/Plata/Bronce) de cada escuela, con exportación a PDF y Excel.

**Architecture:** Backend: helper puro `hqs_award_helper.py` (escalas, tope, promedios, nivel) + servicio `HqsAwardService.report()` que reúne diagnósticos del lapso 3, IAA del lapso 3 y coevaluaciones completas por PECA, expuesto en `GET /statistics/hqsawardsreport/<schoolYearId>` (solo admin). Backoffice: pantalla nueva en Reportes que copia la estructura del reporte de coevaluación (filtros, tabla, exportación).

**Tech Stack:** Python 2.7 (prod) / 3.6 (Docker), Flask-RESTful, MongoEngine 0.24.1, unittest. Angular 11.2.14, Nebular 7, ng-select, pdfmake 0.2.6, xlsx-js-style.

**Spec:** `amblema---backend/docs/superpowers/specs/2026-11-14-premios-escuela-hqs-design.md` (leerlo antes de empezar; las decisiones D1–D6 están allí).

**Estado de aprobación (2026-11-14):** D1–D6 confirmadas por el Ing. Fidel. Pruebas de backend **autorizadas** (escribirlas y ejecutarlas). Ejecución: **subagent-driven-development**.

## Ejecución y modelos

Ejecutar con `superpowers:subagent-driven-development`: un subagente implementador por tarea, un revisor después de cada tarea y una revisión final de toda la rama. El coordinador pasa a cada subagente el parámetro `model` de esta tabla. **El Ing. Fidel puede editar la columna "Modelo"** antes de lanzar; valores válidos del parámetro: `haiku`, `sonnet`, `opus`, `fable`. Si una celda queda vacía, el subagente usa el modelo de la sesión.

| Paso | Rol | Modelo | Esfuerzo | Por qué |
|---|---|---|---|---|
| Task 1 · Helper de cálculo | Implementador | `sonnet` | lower | Funciones puras con las pruebas ya escritas en el plan. |
| Task 1 | Revisor | `sonnet` | — | Revisión acotada a un archivo y sus pruebas. |
| Task 2 · Endpoint del reporte | Implementador | `opus` | — | Consultas MongoEngine, compatibilidad Python 2.7 y contrato JSON del que depende el backoffice. |
| Task 2 | Revisor | `opus` | — | Un error aquí se arrastra a las Tasks 3–4. |
| Task 3 · Pantalla del backoffice | Implementador | `sonnet` | — | Copia la estructura del reporte de coevaluación. |
| Task 3 | Revisor | `sonnet` | — | Rutas en los dos archivos, tipos contra el contrato. |
| Task 4 · Exportación PDF/Excel | Implementador | `sonnet` | — | Mismo patrón que la exportación de coevaluación. |
| Task 4 | Revisor | `sonnet` | — | Estilos de Excel y cabeceras del PDF. |
| Task 5 · Cierre (HANDOFF) | Implementador | `haiku` | lower | Solo documentación. |
| Revisión final de la rama | Revisor | `opus` | higher | Coherencia backend ↔ backoffice y reglas del spec. |

Reglas para el coordinador:
- Pasar en el prompt de cada subagente: la ruta de este plan, la del spec, el texto completo de su Task, la sección **Global Constraints** y el bloque **Interfaces** de las tasks de las que depende.
- Orden estricto: Task 1 → 2 → 3 → 4 → 5. No empezar la Task 3 hasta que la Task 2 esté aprobada por su revisor (la pantalla depende del contrato JSON).
- Las pruebas de backend las corre el Ing. Fidel en el host (ver Global Constraints): el coordinador le pide el comando exacto y espera la salida antes de dar la task por aprobada.

## Global Constraints

- Idioma: comentarios, mensajes y textos de UI en español. Dirigirse al usuario como "Ing. Fidel".
- Ramas: crear `feat/premios-escuela-hqs` **desde `feat/coevaluacion-docente`** en `amblema---backend` y `amblema-backoffice` (depende de la coevaluación). Nunca trabajar en `master`.
- Commits: solo si el Ing. Fidel lo autorizó al lanzar la ejecución; si no, dejar los cambios sin commit y avisar.
- Backend compatible con **Python 2.7**: `from __future__ import division` en todo archivo nuevo que divida, `# -*- coding: utf-8 -*-`, literales `u"..."` con tildes, sin f-strings.
- No tocar archivos protegidos (`.env*`, `docker-compose*.yml`, `Dockerfile*`, `*.bson`…). No cambiar el contrato JSON de endpoints existentes.
- Backend: solo `unittest` + `coverage` (sin dependencias nuevas). Pruebas de integración con `create_app("testing")` y `drop_testing_database(self.db)` en `tearDown`. Nada de envíos reales de correo.
- Comando de la batería (dentro del contenedor). En este entorno `docker exec` está prohibido (403): pedir al Ing. Fidel que lo ejecute en el host y pegue la salida:
  `docker exec amblema_development_back sh -c 'cd /home && python -m coverage run --source=app --omit="app/tests/*,app/scripts/*" -m unittest discover -s app/tests -p "*_test.py" -t . && python -m coverage report'`
  Para un solo módulo: `docker exec amblema_development_back sh -c 'cd /home && python -m unittest app.tests.unitary.hqs_award_helper_test -v'`
- Backoffice: sin tests automatizados. Verificar con `node_modules/.bin/tsc --noEmit -p tsconfig.app.json` (desde `amblema-backoffice`, debe terminar sin salida) y pasos manuales.
- Antes de usar APIs de pdfmake o xlsx-js-style, consultar context7 (`resolve-library-id` + `query-docs`) para la versión instalada (pdfmake 0.2.6).
- Excel: **no** usar `font.name: 'Arial'` con negrita (sale invisible en LibreOffice); colores ARGB de 8 dígitos y `patternType: 'solid'` (ver `appendSheet` del reporte de coevaluación).
- Etiquetas exactas: `"Escuela HQS – Nivel ORO"`, `"Escuela HQS – Nivel PLATA"`, `"Escuela HQS – Nivel BRONCE"`, `"Sin premio"`, `"Datos incompletos"`. Siglas de componentes: `IAA`, `PPM`, `M2M`, `60LM`; falta de coevaluación: `Coevaluación`.
- Al terminar: actualizar `/home/fidel/public_html/amblema/HANDOFF.md` (sección nueva con fecha 2026-11-14, estado, archivos, decisiones D1–D6 y pasos de verificación).

## Review Focus

- Escuela con diagnósticos solo en lapsos 1–2 (lapso 3 vacío): el componente es `null` y la escuela queda en "Datos incompletos", nunca con 0 % ni con premio. → `test_missing_lapse3_is_incomplete` (Task 2).
- Índices por encima de 100 (p. ej. PPM 130 %): cuentan como 100 en el componente y en el promedio. → `test_cap_index` (Task 1) y `test_report_caps_and_awards_gold` (Task 2).
- Evaluadores IAA borrados, sin evaluar, con `index` nulo o de otros lapsos: se ignoran; varios válidos se promedian. → `test_iaa_uses_only_valid_lapse3_evaluators` (Task 2).
- Bordes de los rangos: 80.00 → Oro, 79.99 → Plata, 40.00 → Bronce, 39.99 → Sin premio. → `test_award_boundaries` (Task 1).
- Escuela con coevaluaciones iniciadas pero ninguna completa: Índice de Docentes `null` → "Datos incompletos" con falta `teacherIndex`. → `test_no_completed_coevaluation_is_incomplete` (Task 2).

---

### Task 1: Helper de cálculo (backend)

**Files:**
- Create: `amblema---backend/app/helpers/hqs_award_helper.py`
- Test: `amblema---backend/app/tests/unitary/hqs_award_helper_test.py`

**Interfaces:**
- Produces (constantes):
  - `IAA_MAX = 35`
  - `COMPONENTS = ["iaa", "wordsPerMin", "multiplicationsPerMin", "operationsPerMin"]`
  - `COMPONENT_LABELS = {"iaa": u"IAA", "wordsPerMin": u"PPM", "multiplicationsPerMin": u"M2M", "operationsPerMin": u"60LM", "teacherIndex": u"Coevaluación"}`
  - `AWARD_LEVELS = [{"code": "gold", "label": u"Escuela HQS – Nivel ORO", "minPercentage": 80}, {"code": "silver", "label": u"Escuela HQS – Nivel PLATA", "minPercentage": 60}, {"code": "bronze", "label": u"Escuela HQS – Nivel BRONCE", "minPercentage": 40}]`
  - `NO_AWARD_LABEL = u"Sin premio"`, `INCOMPLETE_LABEL = u"Datos incompletos"`
- Produces (funciones, todas devuelven `None` si la entrada es `None`):
  - `cap_index(value) -> float|None`: `round(min(100.0, max(0.0, float(value))), 2)`.
  - `iaa_percentage(rawAverage) -> float|None`: `cap_index(rawAverage * 100 / IAA_MAX)`.
  - `integral_index(components: dict) -> (float|None, list)`: recibe `{clave: valor ya topado o None}` para las 4 claves de `COMPONENTS`; devuelve `(round(promedio, 2), [])` si están las 4, o `(None, [claves que faltan en el orden de COMPONENTS])`.
  - `final_index(integral, teacherIndex) -> float|None`: `None` si falta alguno; si no `round((integral + teacherIndex) / 2, 2)`.
  - `get_award(finalIndex) -> dict|None`: primer nivel de `AWARD_LEVELS` con `finalIndex >= minPercentage`; `None` si `finalIndex` es `None` o `< 40`.

- [ ] **Step 1: Escribir las pruebas que fallan** en `hqs_award_helper_test.py` (clase `HqsAwardHelperTest(unittest.TestCase)`):

```python
def test_cap_index(self):
    self.assertIsNone(cap_index(None))
    self.assertEqual(cap_index(130), 100.0)
    self.assertEqual(cap_index(83.333), 83.33)
    self.assertEqual(cap_index(-5), 0.0)

def test_iaa_percentage(self):
    self.assertIsNone(iaa_percentage(None))
    self.assertEqual(iaa_percentage(35), 100.0)
    self.assertEqual(iaa_percentage(28), 80.0)
    self.assertEqual(iaa_percentage(14), 40.0)  # 14 * 100 / 35 en Python 2.7 no debe truncar

def test_integral_index_complete(self):
    value, missing = integral_index({"iaa": 80.0, "wordsPerMin": 100.0,
                                     "multiplicationsPerMin": 70.0, "operationsPerMin": 50.0})
    self.assertEqual(value, 75.0)
    self.assertEqual(missing, [])

def test_integral_index_missing(self):
    value, missing = integral_index({"iaa": None, "wordsPerMin": 100.0,
                                     "multiplicationsPerMin": None, "operationsPerMin": 50.0})
    self.assertIsNone(value)
    self.assertEqual(missing, ["iaa", "multiplicationsPerMin"])

def test_final_index(self):
    self.assertIsNone(final_index(None, 80))
    self.assertIsNone(final_index(80, None))
    self.assertEqual(final_index(75.0, 84.0), 79.5)

def test_award_boundaries(self):
    self.assertEqual(get_award(100)["code"], "gold")
    self.assertEqual(get_award(80.0)["code"], "gold")
    self.assertEqual(get_award(79.99)["code"], "silver")
    self.assertEqual(get_award(60.0)["code"], "silver")
    self.assertEqual(get_award(59.99)["code"], "bronze")
    self.assertEqual(get_award(40.0)["code"], "bronze")
    self.assertIsNone(get_award(39.99))
    self.assertIsNone(get_award(None))
```

- [ ] **Step 2: Ejecutar y comprobar que falla**
Run: `docker exec amblema_development_back sh -c 'cd /home && python -m unittest app.tests.unitary.hqs_award_helper_test -v'` (vía el Ing. Fidel en el host).
Expected: `ImportError` / `ModuleNotFoundError: app.helpers.hqs_award_helper`.

- [ ] **Step 3: Implementar `app/helpers/hqs_award_helper.py`** con las constantes y funciones de Interfaces. Encabezado obligatorio: `# -*- coding: utf-8 -*-` y `from __future__ import division`. Docstring del módulo con las reglas del spec (fuente única del cálculo).

- [ ] **Step 4: Ejecutar y comprobar que pasa** (mismo comando). Expected: `Ran 6 tests ... OK`.

- [ ] **Step 5: Commit** (si está autorizado)
```bash
git add app/helpers/hqs_award_helper.py app/tests/unitary/hqs_award_helper_test.py
git commit -m "feat(premios-hqs): helper de cálculo del premio Escuela HQS"
```

---

### Task 2: Servicio, controlador y ruta del reporte (backend)

**Files:**
- Create: `amblema---backend/app/services/hqs_award_service.py`
- Create: `amblema---backend/app/controllers/hqs_award_controller.py`
- Modify: `amblema---backend/app/__init__.py` (import junto a los de `teacher_coevaluation_controller`, ~línea 159; ruta junto a `/statistics/coevaluationsreport`, ~línea 441)
- Test: `amblema---backend/app/tests/integration/hqs_award_report_test.py`

**Interfaces:**
- Consumes: todo lo de Task 1; `school_index(percentages)` de `app.helpers.coevaluation_helper`; modelos `SchoolYear`, `PecaProject`, `EnvironmentalDiagnosticEvaluator` (`app.models.environmental_diagnostic_model`), `TeacherCoevaluation`.
- Produces:
  - `class HqsAwardService` con `report(self, schoolYearId, schoolId=None) -> (dict, int)`.
  - `class HqsAwardReportController(Resource)` con `@admin_required def get(self, schoolYearId)` que llama `report(schoolYearId, schoolId=request.args.get('schoolId') or None)`.
  - Ruta: `GET /statistics/hqsawardsreport/<string:schoolYearId>`.
  - Respuesta 200 (contrato que consume Task 3):
    ```json
    {
      "schoolYear": {"id": "...", "name": "2026 - 2027", "status": "1"},
      "levels": [ AWARD_LEVELS tal cual ],
      "counts": {"gold": 0, "silver": 0, "bronze": 0, "none": 0, "incomplete": 0},
      "schools": [{
        "schoolId": "...", "name": "...", "pecaId": "...", "coordinator": "Ana Pérez",
        "iaaRaw": 28.0,
        "components": {"iaa": 80.0, "wordsPerMin": 100.0, "multiplicationsPerMin": 70.0, "operationsPerMin": 50.0},
        "integralIndex": 75.0,
        "teacherIndex": 84.0, "nCompletedCoevaluations": 3,
        "finalIndex": 79.5,
        "missing": [],
        "missingLabels": [],
        "status": "awarded",
        "award": "silver", "awardLabel": "Escuela HQS – Nivel PLATA"
      }]
    }
    ```
    - `status`: `"awarded"` (tiene premio), `"none"` (datos completos, final < 40), `"incomplete"` (falta algo). `awardLabel` = etiqueta del nivel, `NO_AWARD_LABEL` o `INCOMPLETE_LABEL`.
    - `missing` = faltantes de `integral_index` + `"teacherIndex"` al final si no hay coevaluaciones completas; `missingLabels` = `COMPONENT_LABELS` de cada uno.
    - `counts`: `gold/silver/bronze` por premio, `none` y `incomplete` por `status`.
    - Orden de `schools`: `finalIndex` descendente (los `None` al final), luego `name` sin distinguir mayúsculas.
  - Errores: `schoolYearId` inválido o inexistente → `({"message": "School year not found", "schoolYearId": ...}, 404)`.

Cómo obtener cada dato (por cada `PecaProject(schoolYear=..., isDeleted=False)`, filtrado por `project__school__id=schoolId` si llega; usar `.only(...)` sin cargar `school.sections` para no traer estudiantes):
- Académicos: `peca.school.diagnostics.lapse3.<clave>Index` → `cap_index`.
- IAA: una sola consulta `EnvironmentalDiagnosticEvaluator.objects(pecaId__in=[...], lapse="3", isDeleted=False, hasEvaluated=True)`; agrupar por `pecaId`, promediar los `index` no nulos → `iaaRaw` (`round(.., 2)`) → `iaa_percentage`.
- Docentes: una sola consulta `TeacherCoevaluation.objects(pecaId__in=[...], teacherSubmittedAt__ne=None, coordinatorSubmittedAt__ne=None)`; por `pecaId`, `school_index([c.percentage ...])`; `nCompletedCoevaluations` = cantidad.
- `name`: `peca.project.school.name`; `coordinator`: `peca.project.coordinator.name` o `None`. Saltar PECA sin `project` o sin `project.school`.

- [ ] **Step 1: Escribir las pruebas que fallan** en `hqs_award_report_test.py`, clase `HqsAwardReportTest(unittest.TestCase)`. `setUp` igual al de `app/tests/integration/teacher_coevaluation_test.py:42-67` (app de testing, `create_entities()`, `seed_base()`, ubicación, año escolar, coordinador, padrino, escuela, `Project`). Helpers propios:
  - `newPeca(self, lapse3=None, deleted=False)`: crea `PecaProject` como `newPeca` del test de coevaluación (sin secciones), con `school["diagnostics"] = {"lapse3": lapse3 or {}}` e `isDeleted=deleted`.
  - `addEvaluator(self, peca, index, lapse="3", evaluated=True, deleted=False)`: crea `EnvironmentalDiagnosticEvaluator(pecaId=str(peca.id), lapse=lapse, name="Eval", email="eval@test.com", phone="04140000000", token=<único, p. ej. uuid4().hex>, hasEvaluated=evaluated, index=index, isDeleted=deleted)`.
  - `addCoevaluation(self, peca, teacherId, score, complete=True)`: crea `TeacherCoevaluation(pecaId=str(peca.id), schoolYearId=str(self.schoolYear.id), schoolId=str(self.school.id), teacherId=teacherId, teacherScores=[score]*15, coordinatorScores=[score]*15, teacherSubmittedAt=datetime.utcnow(), coordinatorSubmittedAt=datetime.utcnow() if complete else None)` y `.save()` (el `clean()` del modelo calcula `percentage`).
  - `get(self, schoolId=None)`: `GET /statistics/hqsawardsreport/<id>` (+ `?schoolId=`) y devuelve `(status_code, json)`.
  Pruebas (valores exactos):
```python
def test_report_caps_and_awards_gold(self):
    peca = self.newPeca(lapse3={"wordsPerMinIndex": 130.0, "multiplicationsPerMinIndex": 90.0,
                                "operationsPerMinIndex": 80.0})
    self.addEvaluator(peca, 35)          # IAA 100 %
    self.addCoevaluation(peca, "t1", 5)  # 100 %
    self.addCoevaluation(peca, "t2", 4)  # 80 %
    status, data = self.get()
    self.assertEqual(status, 200)
    s = data["schools"][0]
    self.assertEqual(s["components"], {"iaa": 100.0, "wordsPerMin": 100.0,
                                       "multiplicationsPerMin": 90.0, "operationsPerMin": 80.0})
    self.assertEqual(s["integralIndex"], 92.5)
    self.assertEqual(s["teacherIndex"], 90.0)
    self.assertEqual(s["nCompletedCoevaluations"], 2)
    self.assertEqual(s["finalIndex"], 91.25)
    self.assertEqual(s["status"], "awarded")
    self.assertEqual(s["award"], "gold")
    self.assertEqual(s["awardLabel"], u"Escuela HQS – Nivel ORO")
    self.assertEqual(data["counts"]["gold"], 1)

def test_iaa_uses_only_valid_lapse3_evaluators(self):
    peca = self.newPeca(lapse3={"wordsPerMinIndex": 50.0, "multiplicationsPerMinIndex": 50.0,
                                "operationsPerMinIndex": 50.0})
    self.addEvaluator(peca, 21)                   # válido
    self.addEvaluator(peca, 7)                    # válido -> promedio 14 -> 40 %
    self.addEvaluator(peca, 35, lapse="2")        # otro lapso
    self.addEvaluator(peca, 35, evaluated=False)  # sin evaluar
    self.addEvaluator(peca, 35, deleted=True)     # borrado
    self.addEvaluator(peca, None)                 # sin índice
    self.addCoevaluation(peca, "t1", 2)           # 40 %
    s = self.get()[1]["schools"][0]
    self.assertEqual(s["iaaRaw"], 14.0)
    self.assertEqual(s["components"]["iaa"], 40.0)
    self.assertEqual(s["finalIndex"], 43.75)  # integral (40+50+50+50)/4 = 47.5; docentes 40
    self.assertEqual(s["award"], "bronze")

def test_missing_lapse3_is_incomplete(self):
    peca = self.newPeca(lapse3={"wordsPerMinIndex": 90.0})
    self.addEvaluator(peca, 30)
    self.addCoevaluation(peca, "t1", 5)
    s = self.get()[1]["schools"][0]
    self.assertIsNone(s["integralIndex"])
    self.assertIsNone(s["finalIndex"])
    self.assertEqual(s["missing"], ["multiplicationsPerMin", "operationsPerMin"])
    self.assertEqual(s["missingLabels"], [u"M2M", u"60LM"])
    self.assertEqual(s["status"], "incomplete")
    self.assertIsNone(s["award"])
    self.assertEqual(s["awardLabel"], u"Datos incompletos")

def test_no_completed_coevaluation_is_incomplete(self):
    peca = self.newPeca(lapse3={"wordsPerMinIndex": 90.0, "multiplicationsPerMinIndex": 90.0,
                                "operationsPerMinIndex": 90.0})
    self.addEvaluator(peca, 35)
    self.addCoevaluation(peca, "t1", 5, complete=False)
    s = self.get()[1]["schools"][0]
    self.assertIsNone(s["teacherIndex"])
    self.assertEqual(s["nCompletedCoevaluations"], 0)
    self.assertEqual(s["missing"], ["teacherIndex"])
    self.assertEqual(s["status"], "incomplete")

def test_low_score_has_no_award(self):
    peca = self.newPeca(lapse3={"wordsPerMinIndex": 20.0, "multiplicationsPerMinIndex": 20.0,
                                "operationsPerMinIndex": 20.0})
    self.addEvaluator(peca, 7)           # 20 %
    self.addCoevaluation(peca, "t1", 1)  # 20 %
    s = self.get()[1]["schools"][0]
    self.assertEqual(s["finalIndex"], 20.0)
    self.assertEqual(s["status"], "none")
    self.assertEqual(s["awardLabel"], u"Sin premio")

def test_errors_deleted_peca_and_school_filter(self):
    self.newPeca(deleted=True)
    self.assertEqual(self.get()[1]["schools"], [])
    self.assertEqual(self.client().get('/statistics/hqsawardsreport/abc').status_code, 404)
    self.assertEqual(self.client().get(
        '/statistics/hqsawardsreport/{}'.format("0" * 24)).status_code, 404)
    self.newPeca()
    self.assertEqual(len(self.get(schoolId=str(self.school.id))[1]["schools"]), 1)
    self.assertEqual(self.get(schoolId="0" * 24)[1]["schools"], [])
```

- [ ] **Step 2: Ejecutar y comprobar que falla**
Run: `docker exec amblema_development_back sh -c 'cd /home && python -m unittest app.tests.integration.hqs_award_report_test -v'` (vía el Ing. Fidel).
Expected: 404 en todas (ruta inexistente) → FAIL.

- [ ] **Step 3: Implementar** `HqsAwardService.report` (reglas de la sección Interfaces), el controlador (mismo estilo que `TeacherCoevaluationReportController` en `app/controllers/teacher_coevaluation_controller.py:85-95`, importando `admin_required` de `app.helpers.handler_authorization`) y registrar la ruta en `app/__init__.py`.

- [ ] **Step 4: Ejecutar el módulo y luego la batería completa** (comando de Global Constraints). Expected: módulo `Ran 6 tests ... OK`; batería sin fallos nuevos frente a la línea base (anotar la línea base antes de empezar: si ya había fallos por permisos de `resources/files/*`, documentarlos, no arreglarlos).

- [ ] **Step 5: Verificación manual por cURL** (el Ing. Fidel, con un token de admin en `$TOKEN`):
`curl -s -H "Authorization: Bearer $TOKEN" http://localhost:10505/statistics/hqsawardsreport/<schoolYearId 2026-2027> | python -m json.tool | head -60` → `counts` y `schools` con la forma del contrato.

- [ ] **Step 6: Commit** (si está autorizado)
```bash
git add app/services/hqs_award_service.py app/controllers/hqs_award_controller.py app/__init__.py app/tests/integration/hqs_award_report_test.py
git commit -m "feat(premios-hqs): endpoint del reporte de premios Escuela HQS"
```

---

### Task 3: Pantalla del reporte en el backoffice

**Files (todo en `amblema-backoffice/src/app/`):**
- Create: `_models/report/hqs-award-report.model.ts`
- Create: `services/report/hqs-award-report.service.ts`
- Create: `pages/report/hqs-award-report/hqs-award-report.module.ts`, `hqs-award-report-routing.module.ts`, `hqs-award-report.component.ts`, `.html`, `.scss`
- Modify: `pages/report/report-routing.module.ts` (entrada junto a `coevaluation-report`, ~línea 48)
- Modify: `pages/pages-routing.module.ts` (entrada junto a `coevaluation-report`, ~línea 182). **Obligatorio en ambos**: Angular usa los `children` explícitos de `pages-routing`; si falta allí la URL cae en `**`.
- Modify: `pages/pages-menu.ts` (después de "Coevaluación docentes HQS", ~línea 228): `{ title: "Premios Escuela HQS", link: "/pages/report/hqs-award-report" }`

**Interfaces:**
- Consumes: contrato JSON de Task 2.
- Produces:
  - Tipos: `HqsAwardCode = 'gold' | 'silver' | 'bronze'`, `HqsAwardStatus = 'awarded' | 'none' | 'incomplete'`, `HqsComponentKey = 'iaa' | 'wordsPerMin' | 'multiplicationsPerMin' | 'operationsPerMin'`, interfaces `HqsAwardLevel`, `HqsAwardSchool`, `HqsAwardReport` con los campos exactos del contrato (`number | null` donde el backend puede mandar `null`).
  - `HqsAwardReportService.getReport(schoolYearId: string, schoolId?: string | null): Observable<HqsAwardReport>` contra `${environment.api}statistics/hqsawardsreport/${schoolYearId}` con `HttpParams` `schoolId` opcional (copiar `services/report/coevaluation-report.service.ts`).
  - `HqsAwardReportComponent` (selector `app-hqs-award-report`) con `report: HqsAwardReport | null`, `loading`, `exporting`, `exportingFormat: 'pdf' | 'xlsx' | null`, `onSearch()`, `onExport(format)`, `filtersLabel(): string`, `hasData(report): boolean` — mismos nombres y comportamiento que `CoevaluationReportComponent` (`pages/report/coevaluation-report/coevaluation-report.component.ts`), sin el filtro de nivel ni `expanded`.
  - `HqsAwardReportModule` con los mismos imports Nebular/NgSelect que `CoevaluationReportModule` salvo `NbTabsetModule`.

- [ ] **Step 1: Modelo y servicio** con los tipos y la firma de Interfaces.

- [ ] **Step 2: Componente + plantilla.** Estructura (copiar clases y SCSS base del reporte de coevaluación: una sola `nb-card`, filtros en una fila, `results-bar`):
```
┌ Reporte de premios Escuela HQS ─────────────────────────────────────────┐
│ [Período académico *  v] [Escuela (Todas)  v]            [ Consultar ]  │
│ 2026 - 2027 · Todas las escuelas                 [Exportar PDF][Excel]  │
│ ( ORO 3 ) ( PLATA 5 ) ( BRONCE 4 ) ( Sin premio 2 ) ( Incompletos 6 )   │
│ Escuela | Coord. | IAA | PPM | M2M | 60LM | Í. Integral | Í. Docentes   │
│         |        |     |     |     |      |             | HQS | Promedio│
│         |        |     |     |     |      |             |     | Premio  │
│ Esc. A  | Ana P. | 100 | 100 | 90  | 80   | 92.5        | 90  | 91.25 ORO
│ Esc. B  | ...    |  —  | 90  |  —  |  —   |  —          | 80  |  —  Datos incompletos (falta: IAA, M2M, 60LM)
└─────────────────────────────────────────────────────────────────────────┘
```
  - Números con 2 decimales como máximo (reusar la lógica de `num()` del export de coevaluación); `null` → `—`.
  - Columna Premio: insignia con fondo ORO `#D4AF37`, PLATA `#A8A9AD`, BRONCE `#CD7F32`, texto `#222b45`; "Sin premio" y "Datos incompletos" en gris, y en incompletos el texto `falta: ` + `missingLabels.join(', ')`.
  - Nota al pie de la tabla: "Índice Integral = promedio de IAA, PPM, M2M y 60LM del lapso 3 (máximo 100 cada uno; IAA convertido de 35 puntos a %). Premio: Oro ≥ 80, Plata ≥ 60, Bronce ≥ 40."
  - Toast `info` "No se encontraron escuelas con esos filtros" si `schools` viene vacío; `error` "No se pudo obtener la información del reporte" si falla.
  - Si la tabla no cabe, scroll horizontal con la columna Escuela fija (`position: sticky; left: 0; background: #fff`).

- [ ] **Step 3: Rutas y menú** en los 3 archivos indicados.

- [ ] **Step 4: Verificar compilación**
Run (desde `amblema-backoffice`): `node_modules/.bin/tsc --noEmit -p tsconfig.app.json`
Expected: sin salida.

- [ ] **Step 5: Verificación manual** en `http://localhost:2004` (`ambleadministrador@gmail.com` / `12345678`): Reportes → Premios Escuela HQS → período 2026 - 2027 → Consultar. Con los datos de `scripts/seed_teacher_coevaluations.py` deben verse escuelas con Índice de Docentes; las que no tengan IAA o diagnósticos del lapso 3 deben verse como "Datos incompletos" con lo que falta. Navegar a la URL directa `/pages/report/hqs-award-report` y recargar: no debe redirigir al inicio.

- [ ] **Step 6: Commit** (si está autorizado)
```bash
git add src/app/_models/report/hqs-award-report.model.ts src/app/services/report/hqs-award-report.service.ts src/app/pages/report/hqs-award-report src/app/pages/report/report-routing.module.ts src/app/pages/pages-routing.module.ts src/app/pages/pages-menu.ts
git commit -m "feat(premios-hqs): reporte de premios Escuela HQS en el backoffice"
```

---

### Task 4: Exportación a PDF y Excel (backoffice)

**Files:**
- Create: `amblema-backoffice/src/app/pages/report/hqs-award-report/hqs-award-report-export.service.ts`
- Modify: `hqs-award-report.component.ts` (proveer y usar el exportador en `onExport`)

**Interfaces:**
- Consumes: `HqsAwardReport` (Task 3); `IMAGE` de `../img-base-64`.
- Produces: `@Injectable() class HqsAwardReportExport` con `toPdf(report: HqsAwardReport, filters: string): Promise<void>` y `toExcel(report: HqsAwardReport, filters: string): Promise<void>`, con el mismo patrón que `CoevaluationReportExport` (`pages/report/coevaluation-report/coevaluation-report-export.service.ts`): diferido de un ciclo, `withTimeout` de 2 min, `download(fileName, callback)`, y en el componente el bloqueo de botones con liberación a los 800 ms.
  - Nombre de archivo: `Reporte-premios-HQS-<año sin espacios>_<dd-mm-aaaa_hh-mm>.<pdf|xlsx>`.

- [ ] **Step 1: PDF** (A4 horizontal, `pageMargins [25, 30, 25, 30]`, `defaultStyle.fontSize 8`, pie con `página / total`):
  1. Logo `IMAGE` (absoluto, como en coevaluación) y título "Reporte de premios Escuela HQS" (color `#2e8aaa`, 16, negrita, `margin [0, 35, 0, 10]`).
  2. Tabla de datos: Período académico, Fecha, Filtros.
  3. Tabla de conteos: ORO, PLATA, BRONCE, Sin premio, Datos incompletos.
  4. Tabla principal con las 10 columnas de la pantalla (`headerRows: 1`), cabecera verde `#81b03e` con texto blanco, **centrada en horizontal y vertical** con el mismo `header()` de coevaluación (márgenes según `\n`; títulos de dos líneas con salto explícito: `"Índice\nIntegral"`, `"Índice\nDocentes HQS"`). Celda Premio con `fillColor` del nivel.
  5. Nota de cálculo (mismo texto de Task 3) en `fontSize 7`, cursiva.

- [ ] **Step 2: Excel** con una hoja "Premios": filas de intro (título, Período académico, Filtros, vacía), cabecera y una fila por escuela con las mismas columnas más `IAA (puntos /35)` = `iaaRaw` después de IAA, y `Falta` = `missingLabels.join(', ')` al final. Estilos con el `appendSheet` del reporte de coevaluación (sin Arial, ARGB de 8 dígitos).

- [ ] **Step 3: Verificar compilación** (`tsc` como en Task 3). Expected: sin salida.

- [ ] **Step 4: Verificación manual:** exportar PDF y Excel desde la pantalla. PDF: logo sin tapar la tabla de datos, cabeceras centradas, insignias con color. Excel: abrir en LibreOffice; la cabecera debe verse (texto blanco sobre verde) y los números como números. Los botones se bloquean mientras se genera y no hay doble descarga con doble clic.

- [ ] **Step 5: Commit** (si está autorizado)
```bash
git add src/app/pages/report/hqs-award-report
git commit -m "feat(premios-hqs): exportación a PDF y Excel del reporte de premios"
```

---

### Task 5: Cierre

- [ ] **Step 1:** Actualizar `/home/fidel/public_html/amblema/HANDOFF.md` con una sección "2026-11-14 — Premios a la Escuela HQS" (estado por repo, endpoint y contrato resumido, decisiones D1–D6, resultados de las pruebas y pasos de verificación manual). Reemplazar en "Coevaluación … Reglas acordadas" la línea "Fuera de alcance: Premios a la Escuela HQS…" por una referencia a la nueva sección.
- [ ] **Step 2:** Entregar al Ing. Fidel: resumen corto, resultados reales de las pruebas (o que no se pudieron correr y por qué) y la lista de pasos de verificación manual de Tasks 2–4.
