# Plan de Acción — Actualización Metodología AmbLeMa HQS (26-11)

**Fecha:** 2026-11-27  
**Rama objetivo:** `feat/coevaluacion-docente` en `amblema---backend`, `amblema-backoffice` y `amblema-front`  
**Fuentes:**
- `COEVALUACION/Metodología de Evaluación 26-11.docx`
- `COEVALUACION/Prueba_Consolidado_AmbLeMa_HQS_Juan_Jacinto_Lara_II.xlsx`

---

## 0. Contexto y decisiones previas

- **Datos existentes de coevaluación:** son solo de prueba (en desarrollo). Al pasar a escala `0–7` y reordenar los ítems 11–15, se eliminarán/regenerarán los registros de prueba en la BD local (`teacher_coevaluations`) en lugar de mantener compatibilidad con la escala vieja `0–5`.
- **Ubicación de la Valoración del Coordinador:** el coordinador la responde desde el **PECA → Datos de la escuela** (`amblema-front`), mediante una opción desplegable/pestaña dedicada (con acceso también para admin por rol, misma regla que coevaluación).
- **Decisiones confirmadas por el Ing. Fidel (2026-11-27):**
  1. **Ajuste `< 40` por grado (Fase 3):** usar la fórmula del Excel consolidado — ponderada por participantes × factor (`0.5` si el índice del grado `< 40`, `1` si `>= 40`), excluyendo grados sin participantes.
  2. **Envío de Valoración del Coordinador (Fase 2):** una vez por PECA (año escolar), bloqueada tras enviar (mismo patrón atómico que la coevaluación).
  3. **Condición exacta del AmbLeMario *sine qua non* (Fase 3):** evaluar con el interruptor `yearbookDownloadEnabled == True` en `PecaProject`.
  4. **Promedio "Acordado" en `0–7` (Fase 1):** mantener truncado entero `int(t + c) // 2` acordado el 2026-11-10.
  5. **Cortes decimales (Fases 1 y 3):** usar límites inclusivos continuos (`>= 80`, `>= 60`, `>= 40`) para evitar huecos entre `79,x` y `80`.

---

## Fase 1 — Coevaluación Docente: Escala 0–7 (base 105), Dimensión C y Nivel Inicial

### 1.1 `amblema---backend`
- **`app/helpers/coevaluation_helper.py`**
  - Cambiar `MAX_SCORE = 7` (con `MAX_TOTAL = 15 * 7 = 105`).
  - Reemplazar `SCALE` por los 8 niveles (`0` a `7`):
    - `0`: *No iniciado / Sin evidencia*
    - `1`: *Arranque Incipiente*
    - `2`: *En Desarrollo Temprano*
    - `3`: *En Proceso de Consolidación*
    - `4`: *Aceptable / Básico*
    - `5`: *Funcional / Sólido*
    - `6`: *Desempeño Avanzado*
    - `7`: *Excelente / Óptimo*
  - Reordenar Dimensión C en `ITEMS` (ítems `11` a `15`) y actualizar redacciones según el `.docx`:
    - `11`: Asistencia
    - `12`: Amblemonedas
    - `13`: Bodega AmbLeMa
    - `14`: Actividad especial 2do lapso
    - `15`: Feria AmbLeMa (*"¿Planifica con su grupo la participación en la Feria AmbLeMa?"*)
    - Ajustes menores de texto en ítems 4 (`JUMP Math`), 5, 6 (`ecotemas`), 8 (`presente`) y 10 (`sus estudiantes`).
  - Actualizar `LEVELS`:
    - `excellence`: `minTotal: 84`, `minPercentage: 80` (`Docente HQS con Excelencia`)
    - `commitment`: `minTotal: 63`, `minPercentage: 60` (`Docente HQS con Compromiso`)
    - `progress`: `minTotal: 42`, `minPercentage: 40` (`Docente HQS en Avance`)
    - `beginning`: `minTotal: 0`, `minPercentage: 0` (`Docente en Fase Inicial (Requiere acompañamiento prioritario)`)
- **`app/services/teacher_coevaluation_service.py`**
  - En `_send_email()` (línea ~400), reemplazar `"escala de <strong>0 a 5</strong>"` por los valores dinámicos `MIN_SCORE` y `MAX_SCORE` (`0 a 7`).
- **`app/schemas/teacher_coevaluation_schema.py`** y **`app/models/teacher_coevaluation_model.py`**
  - Verificar docstrings (`0-5` → `0-7`); la validación ya usa `MIN_SCORE`/`MAX_SCORE`.
- **Scripts y pruebas**
  - Actualizar `scripts/seed_teacher_coevaluations.py` para generar puntajes `0–7` con los nuevos cortes (`84`, `63`, `42`).
  - Actualizar `app/tests/unitary/coevaluation_helper_test.py` y `app/tests/integration/teacher_coevaluation_test.py` (rangos `0–7`, totales sobre `105`, validación de `8` como error 400, nueva etiqueta de `beginning`).
- **BD local (previa confirmación y respaldo)**
  - Limpiar `teacher_coevaluations` de prueba y re-ejecutar el seed con escala `0–7`.

### 1.2 `amblema-front`
- **`src/app/peca/peca-page/blocks/teacher-coevaluation/teacher-coevaluation-modal.component.ts` y `.scss`**
  - Derivar `scoreOptions` desde `detail.instrument.scale.map(s => s.score)` en lugar de `[0, 1, 2, 3, 4, 5]`.
  - Quitar fallback `: 5` en `groupMax()`.
  - Ajustar estilos para 8 botones por ítem y 8 tarjetas en `.scale-grid` (evitar desborde en pantallas pequeñas).
- **`src/app/web/pages/teacher-coevaluation/teacher-coevaluation.component.ts` y `.scss`**
  - Derivar `scoreOptions` desde `data.instrument.scale.map(s => s.score)`.
  - Verificar layout móvil y escritorio con 8 opciones (`0`–`7`).

### 1.3 `amblema-backoffice`
- **`src/app/pages/report/coevaluation-report/coevaluation-report.component.ts` y `.html`**
  - Actualizar `levelOptions` para `beginning` (`Docente en Fase Inicial`).
  - Ajustar `shortLevel()` para que formatee correctamente `"Docente en Fase Inicial (Requiere acompañamiento prioritario)"` → `"Fase inicial"` (sin romper los otros 3 niveles).
  - Reemplazar encabezados `Puntaje / 75` por `Puntaje / {{ report.instrument.maxTotal }}`.
- **`src/app/pages/report/coevaluation-report/coevaluation-report-export.service.ts`**
  - Reemplazar `'Puntaje (75)'` (PDF y Excel) usando `report.instrument.maxTotal`.

### Verificación Fase 1
- Backend: `python -m unittest app.tests.unitary.coevaluation_helper_test app.tests.integration.teacher_coevaluation_test -v` en `amblema_development_back`.
- Front y Backoffice: `tsc --noEmit` + `ng build --aot` a `/tmp/aot-check` (y borrar `/tmp/aot-check`).
- Manual: abrir modal en PECA (`localhost:2005`), enlace público `/coevaluacion/:token`, y reporte + PDF/Excel en backoffice (`localhost:2004`).

---

## Fase 2 — Instrumento de Valoración del Coordinador (4 preguntas cerradas)

### 2.1 `amblema---backend`
- **Catálogo y cálculo — `app/helpers/coordinator_evaluation_helper.py` (nuevo)**
  - Fuente única de las 4 preguntas (redacción de la hoja `Opinión Coordinador` del Excel) y de la escala:
    - `never` (`Nunca`): `25.0` pts (`100 %`)
    - `rarely` (`Pocas veces`): `25 * 2 / 3` (`16.67` pts / `66.7 %`)
    - `frequently` (`Con frecuencia`): `25 * 1 / 3` (`8.33` pts / `33.3 %`)
    - `always` (`Siempre`): `0.0` pts (`0 %`)
  - Función `compute_coordinator_score(answers)` → suma exacta redondeada a 2 decimales (escala `0–100`).
  - `get_coordinator_instrument()` para servir catálogo y opciones al front/backoffice sin duplicación.
- **Modelo — `app/models/coordinator_evaluation_model.py` (nuevo)**
  - Colección `coordinator_evaluations` con índice único por `pecaId` (misma filosofía desacoplada que `teacher_coevaluations`, sin engordar el documento `PecaProject`).
  - Campos: `pecaId`, `schoolYearId`, `schoolId`, `schoolName`, `coordinator` (`id`, `name`), `answers` (`[{number, option, score}]`), `totalScore` (`0–100`), `submittedAt`, `submittedBy`, `createdAt`, `updatedAt`.
- **Schema, Servicio, Controlador y Rutas**
  - `app/schemas/coordinator_evaluation_schema.py`: valida las 4 respuestas obligatorias con opciones válidas.
  - `app/services/coordinator_evaluation_service.py`:
    - `get_evaluation(pecaId, caller)` → devuelve instrumento, estado (`not_started` / `completed`), respuestas, puntaje y bandera `canEvaluate`.
    - `save_evaluation(pecaId, jsonData, caller)` → validación de acceso (admin o coordinador del PECA con permiso `teacher_coevaluation`, o permiso propio si se define), guardado único (409 si ya fue enviada) con `update_one`/índice único.
  - `app/controllers/coordinator_evaluation_controller.py` y registro en `app/__init__.py`:
    - `GET /pecaprojects/<pecaId>/coordinator-evaluation` (JWT)
    - `POST /pecaprojects/<pecaId>/coordinator-evaluation` (JWT)
- **Pruebas**
  - `app/tests/unitary/coordinator_evaluation_helper_test.py`
  - `app/tests/integration/coordinator_evaluation_test.py` (GET inicial, POST exitoso, POST duplicado 409, payload inválido 400, permisos 403).

### 2.2 `amblema-front`
- **Servicio — `src/app/services/peca/coordinator-evaluation.service.ts` (nuevo)**
  - `get(pecaId)` y `save(pecaId, payload)` + `open$` / `changed$` si se usa modal, o carga directa en panel desplegable.
- **UI en PECA → Datos de la escuela**
  - Componente `src/app/peca/peca-page/blocks/coordinator-evaluation/` (desplegable/acordeón o modal disparado desde una opción en **Datos de la escuela**).
  - Integración en `school-data-config.ts`, `school-data-page.component.ts` y `peca.module.ts` (declarar en `entryComponents` si se monta dinámicamente por View Engine).
  - Mostrar solo si el usuario tiene permiso (`teacher_coevaluation` / coordinador o admin); nunca visible para usuario de escuela.
  - Mostrar las 4 preguntas con radio buttons de las 4 frecuencias, puntaje en vivo o resumen, confirmación antes de enviar, y vista de solo lectura una vez completada.

### Verificación Fase 2
- Backend: pruebas unitarias e integración nuevas + batería completa.
- Front: `tsc --noEmit` + `ng build --aot` a `/tmp/aot-check`.
- Manual: entrar a PECA → Datos de la escuela como coordinador/admin, desplegar la Valoración del Coordinador, responder las 4 preguntas, guardar y verificar persistencia y bloqueo al recargar.

---

## Fase 3 — Premios Escuela HQS: Ajuste `< 40`, Fórmula 40/40/20 y AmbLeMario Obligatorio

### 3.1 `amblema---backend`
- **`app/helpers/hqs_award_helper.py`**
  - Actualizar constantes y reglas:
    - Pesos: `INTEGRAL_WEIGHT = 0.40`, `TEACHER_WEIGHT = 0.40`, `COORDINATOR_WEIGHT = 0.20`.
    - `COMPONENT_LABELS`: incluir `"coordinatorIndex": u"Valoración Coordinador"` y `"yearbook": u"AmbLeMario"`.
  - Agregar helper puro `adjusted_area_index(grade_stats, threshold=40.0, low_weight=0.5)`:
    - Recibe lista de `(grade, index, participants)` por grado; ignora `participants <= 0` o `index is None`.
    - Aplica factor `0.5` si `index < 40`, si no `1.0`.
    - Devuelve `(adjusted_index, raw_index)` topados en `0–100` y redondeados a 2 decimales.
  - Actualizar `final_index(integral, teacherIndex, coordinatorIndex)`:
    - `round(integral * 0.40 + teacherIndex * 0.40 + coordinatorIndex * 0.20, 2)` (o `None` si falta alguno).
  - Actualizar `get_award(globalScore, yearbookCompleted)`:
    - Si `not yearbookCompleted` o `globalScore is None` → `None`.
    - Si `globalScore >= 80` → `gold`; `>= 60` → `silver`; `>= 40` → `bronze`; `< 40` → `None`.
- **`app/services/hqs_award_service.py`**
  - Proyectar en `PecaProject.objects(...)` también `school.sections.grade`, `school.sections.isDeleted`, `school.sections.diagnostics.lapse3` (manteniendo `as_pymongo()` y **sin** cargar `students` para conservar el rendimiento).
  - Agrupar secciones activas por `grade` para calcular el índice por grado de `wordsPerMin`, `multiplicationsPerMin` y `operationsPerMin` y aplicar `adjusted_area_index()` (IAA sigue sin ajuste `< 40`).
  - Consultar `CoordinatorEvaluation` por `pecaId__in=pecaIds` (una sola consulta en lote).
  - Incorporar `coordinatorIndex` y la condición *sine qua non* de AmbLeMario en `build_school_row()` (manteniendo `missing`/`missingLabels` claros cuando falte algún indicador o el AmbLeMario).
  - Devolver en la respuesta los campos nuevos (`coordinatorIndex`, `rawComponents` si se desea trazabilidad, `globalScore`/`finalIndex`, `yearbookCompleted`/`yearbookDownloadEnabled`).
- **Scripts y pruebas**
  - Actualizar `scripts/seed_hqs_award_data.py` para generar también evaluaciones del coordinador en local.
  - Actualizar `app/tests/unitary/hqs_award_helper_test.py`, `app/tests/unitary/hqs_award_service_test.py` y `app/tests/integration/hqs_award_report_test.py` (ajuste `< 40`, ponderación 40/40/20, bloqueo sin AmbLeMario, datos incompletos sin valoración del coordinador).

### 3.2 `amblema-backoffice`
- **`src/app/_models/report/hqs-award-report.model.ts`**
  - Agregar `coordinatorIndex: number | null` (y campos auxiliares que exponga el backend).
- **`src/app/pages/report/hqs-award-report/hqs-award-report.component.html`, `.ts` y `.scss`**
  - Añadir columna **Valoración Coord. (20 %)**.
  - Renombrar columna `Promedio` → **Puntaje Global HQS** (40/40/20).
  - Indicar visualmente cuando falta el AmbLeMario (requisito obligatorio) o la Valoración del Coordinador.
  - Actualizar la nota explicativa al pie de tabla con la nueva metodología (ajuste `< 40`, ponderación 40/40/20 y AmbLeMario obligatorio).
- **`src/app/pages/report/hqs-award-report/hqs-award-report-export.service.ts`**
  - Actualizar tablas PDF (filtros, general y por estado) y hojas Excel (`Premios`, `Resumen`, `Por estado`) con las nuevas columnas y nota de reglas.

### Verificación Fase 3
- Backend: batería completa con cobertura en `amblema_development_back`:
  ```bash
  docker exec amblema_development_back sh -c 'cd /home && python -m coverage run --source=app --omit="app/tests/*,app/scripts/*" -m unittest discover -s app/tests -p "*_test.py" -t . && python -m coverage report'
  ```
- Backoffice: `tsc --noEmit` + `ng build --aot` a `/tmp/aot-check`.
- Manual: `http://localhost:2004` → Reportes → Premios Escuela HQS → año `2026 - 2027` → verificar cálculo con un caso de prueba equivalente al Excel de *Juan Jacinto Lara II*, comprobar bloqueo cuando AmbLeMario está desactivado, y exportar PDF y Excel en los 3 modos.

---

## Fase 4 — Cierre y documentación
- Actualizar `HANDOFF.md` con decisiones, pruebas ejecutadas y pasos de verificación.
- Revisar `git status` y `git diff` en los tres repositorios.
- Realizar commits y PRs (orden **backend → backoffice → front**) únicamente cuando el Ing. Fidel lo autorice.
