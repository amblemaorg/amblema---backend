# Habilitar descarga del AmbLeMario — Plan de implementación

> **Para agentes ejecutores:** SUB-SKILL REQUERIDA: usar `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans` para ejecutar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para el seguimiento.

**Objetivo:** que un administrador active o desactive, desde `/pages/projects` del backoffice, la descarga del AmbLeMario del PECA del año escolar en curso; en el front, los coordinadores solo ven "Versión Impresa" y "Descargar PDF" cuando está activada.

**Arquitectura:** una bandera `yearbookDownloadEnabled` (por defecto `False`) en `PecaProject`, así cada año arranca desactivado. El backend expone tres operaciones en endpoints nuevos y ligeros (no se tocan `/projects` ni `PecaProjectSchema`). El backoffice añade una columna con interruptor en la tabla de proyectos. El front consulta la bandera al abrir `/pdf-template/yearbook` y oculta los dos botones solo al coordinador.

**Stack:** Flask 1.1.2 + Flask-RESTful + MongoEngine 0.24.1 (Python 2.7 prod / 3.6 Docker), Angular 11 + ng2-smart-table + NGXS en backoffice y front.

**Especificación (requisitos del Ing. Fidel, 2026-11-15):**
1. Backoffice, pantalla `/pages/projects`: botón para activar/desactivar la descarga de AmbLeMarios.
2. Solo aplica a proyectos con un `PecaProject` del año escolar en curso (`SchoolYear.status == "1"`).
3. Front, `/pdf-template/yearbook`: "Versión Impresa" y "Descargar PDF" se muestran al coordinador solo si está habilitado.
4. El administrador ve esos botones siempre. La restricción aplica solo a coordinadores.

## Restricciones globales

- Repos y rama: `amblema---backend`, `amblema-backoffice`, `amblema-front`, todos en `feat/coevaluacion-docente` (ya existe, ya es la rama actual). No crear ramas nuevas.
- **No hacer commits ni push**: el Ing. Fidel los autoriza aparte. Cada tarea termina en "cambios listos, sin commit".
- Backend compatible con Python 2.7: sin f-strings, sin anotaciones de tipo, `# -*- coding: utf-8 -*-` en archivos con texto no ASCII.
- Antes de escribir código de una librería, consultar context7 (`resolve-library-id` + `query-docs`) para MongoEngine 0.24 (`update_one`, `LazyReferenceField.fetch`), Flask-RESTful, ng2-smart-table (columna `type: 'custom'` + `renderComponent`) y NGXS 3.7 (`selectSnapshot`). Si context7 falla, avisar al Ing. Fidel antes de seguir.
- Nombres exactos (no cambiarlos entre repos):
  - Campo Mongo/JSON: `yearbookDownloadEnabled` (bool).
  - Campo JSON: `schoolYearActive` (bool), `projectId`, `pecaId` (str).
  - Rutas: `GET /pecaprojects/yearbook-download` y `GET|PATCH /pecaprojects/<id>/yearbook-download`.
- Códigos de tipo de usuario: `"1"` admin, `"2"` coordinador, `"3"` padrino, `"4"` escuela. "Coordinador" = `userType === '2'`.
- Archivos protegidos (`.env`, `docker-compose*.yml`, `Dockerfile`…): no se tocan.
- Front y backoffice: sin tests automatizados (validación manual).
- Backend: pruebas de la Tarea 2 **autorizadas por el Ing. Fidel (2026-11-15)**: escribirlas y ejecutar la batería completa.

## Asignación de modelos

Cada tarea la ejecuta un subagente con el modelo indicado (parámetro `model` del Agent tool). Si una tarea falla dos veces su verificación, se reintenta con el modelo del nivel superior.

| Tarea | Modelo | Motivo |
|---|---|---|
| 1. Backend: modelo, servicio, rutas | Sonnet 5.5 (`sonnet`) | Lógica de negocio y contrato JSON del que dependen los otros dos repos. |
| 2. Backend: pruebas de integración | Sonnet 5.5 (`sonnet`) | Debe interpretar fallas y decidir si el error está en el código o en la prueba. |
| 3. Backoffice: columna con interruptor | Sonnet 5.5 (`sonnet`) | Componente nuevo con estado compartido, reversión en error y permisos. |
| 4. Front: ocultar botones | Haiku 5.5 (`haiku`) | Cambio acotado: un método de servicio, una bandera y dos `*ngIf`, con la regla ya escrita. |
| 5. Documentación (handoff) | Haiku 5.5 (`haiku`) | Resumen mecánico de lo hecho. |
| Revisión final de la rama (3 repos) | Opus 5.5 (`opus`) | Coherencia entre servicios, seguridad del PATCH y compatibilidad con Python 2.7. |

## Decisiones tomadas (confirmar con el Ing. Fidel si alguna no encaja)

- **D1 — Años anteriores:** la restricción solo afecta al PECA del año en curso. Si el coordinador abre el AmbLeMario de un año cerrado (`schoolYearActive == false`), ve los botones (como hoy). Así no se bloquean AmbLeMarios viejos cuya bandera nunca se activó.
- **D2 — Coordinador vs. admin:** se decide por `userType`, no por rol. Un usuario con `userType "2"` sufre la restricción aunque tenga rol admin. Padrino y escuela (`"3"`, `"4"`) no tienen restricción.
- **D3 — Falla cerrada:** si el front no puede leer la bandera (error HTTP), al coordinador se le ocultan los botones.
- **D4 — Solo UI:** el PDF se genera en el navegador (html2canvas/jsPDF). La restricción oculta botones; no impide un Ctrl+P del navegador. Se acepta.
- **D5 — Escritura atómica:** el PATCH usa `update_one(set__yearbookDownloadEnabled=...)`, no `save()`, para no disparar `pre_save`/`clean` ni reescribir el documento PECA completo.

## Puntos a vigilar en revisión

1. PATCH sobre un PECA de año cerrado → 400, la bandera no cambia.
2. PATCH con `yearbookDownloadEnabled` ausente o no booleano (`"true"`, `1`) → 400.
3. Proyecto sin PECA del año en curso → la celda del backoffice muestra "—", sin interruptor.
4. Coordinador mientras carga la bandera → botones ocultos (no parpadean visibles y luego desaparecen).
5. Ruta `/pecaprojects/yearbook-download` no debe caer en `PecaProjectHandlerController` (`/pecaprojects/<string:id>`). Werkzeug prioriza la regla estática; verificarlo con la prueba o con cURL.

---

### Task 1 (Tarea 1): Backend — modelo, servicio, controlador y rutas

**Archivos:**
- Modificar: `amblema---backend/app/models/peca_project_model.py` (clase `PecaProject`, junto a `isDeleted`)
- Crear: `amblema---backend/app/services/yearbook_download_service.py`
- Crear: `amblema---backend/app/controllers/yearbook_download_controller.py`
- Modificar: `amblema---backend/app/__init__.py` (imports de controladores ~línea 106 y `add_resource` junto a `/pecaprojects/<string:id>/printoptions`, ~línea 370)

**Interfaces:**
- Produce (consumidas por backoffice y front):
  - `GET /pecaprojects/yearbook-download` (`@admin_required`) → `200 {"records": [{"projectId": str, "pecaId": str, "yearbookDownloadEnabled": bool}]}`. Solo PECAs con `isDeleted=False` del `SchoolYear` con `status="1"` e `isDeleted=False`. Sin año activo → `{"records": []}`.
  - `GET /pecaprojects/<id>/yearbook-download` (`@jwt_required`) → `200 {"pecaId": str, "schoolYearActive": bool, "yearbookDownloadEnabled": bool}`; PECA inexistente o borrado → 404 (`RegisterNotFound`).
  - `PATCH /pecaprojects/<id>/yearbook-download` (`@admin_required`), cuerpo `{"yearbookDownloadEnabled": bool}` → `200` con el mismo cuerpo que el GET. 404 si no existe; 400 `{"msg": "yearbookDownloadEnabled debe ser booleano"}` si falta o no es `bool`; 400 `{"msg": "Solo se puede cambiar en el año escolar en curso"}` si el año del PECA no tiene `status "1"`.
- Python: `YearbookDownloadService` con `listActive()`, `get(pecaId)`, `setEnabled(pecaId, jsonData)`; cada uno devuelve `(dict, status_code)`.

- [ ] **Paso 1: Campo en el modelo.** En `PecaProject` añadir `yearbookDownloadEnabled = fields.BooleanField(default=False)`. No tocar `PecaProjectSchema`.
- [ ] **Paso 2: Servicio** `app/services/yearbook_download_service.py`:
  - `listActive()`: `SchoolYear.objects(status="1", isDeleted=False).first()`; si no hay, `{"records": []}, 200`. Si hay, `PecaProject.objects(schoolYear=sy.id, isDeleted=False).only("id", "project", "yearbookDownloadEnabled")` y mapear a `projectId = peca.project.id`. Omitir PECAs sin `project`.
  - `get(pecaId)`: cargar `.only("id", "schoolYear", "yearbookDownloadEnabled")`; 404 con `RegisterNotFound(message="Record not found", status_code=404, payload={"recordId": pecaId})` (mismo patrón que `PecaProjectService.getPrintOptions`). `schoolYearActive` = el `SchoolYear` referenciado existe, no está borrado y su `status == "1"` (usar `peca.schoolYear.fetch()` dentro de `try` por `DoesNotExist`; consultar context7). Un valor `None` en BD cuenta como `False`.
  - `setEnabled(pecaId, jsonData)`: validar `isinstance(value, bool)` (antes de tocar BD), cargar como en `get`, rechazar año no activo, `PecaProject.objects(id=pecaId).update_one(set__yearbookDownloadEnabled=value)`, devolver `self.get(pecaId)`.
- [ ] **Paso 3: Controlador** `app/controllers/yearbook_download_controller.py`: `YearbookDownloadListController(Resource).get` con `@admin_required`; `YearbookDownloadController(Resource).get` con `@jwt_required` y `.patch` con `@admin_required` (lee `request.get_json(silent=True) or {}`). Decoradores de `app/helpers/handler_authorization.py`.
- [ ] **Paso 4: Rutas** en `app/__init__.py`:
  ```python
  api.add_resource(YearbookDownloadListController, '/pecaprojects/yearbook-download')
  api.add_resource(YearbookDownloadController, '/pecaprojects/<string:id>/yearbook-download')
  ```
- [ ] **Paso 5: Verificación rápida** con el backend levantado (`amblema_development_back`, puerto 10505), con un token de admin (`POST /auth/login` con las credenciales locales del CLAUDE.md):
  ```bash
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:10505/pecaprojects/yearbook-download
  # Esperado: {"records": [{"projectId": "...", "pecaId": "...", "yearbookDownloadEnabled": false}, ...]}
  curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"yearbookDownloadEnabled": true}' http://localhost:10505/pecaprojects/<pecaId>/yearbook-download
  # Esperado: {"pecaId": "<pecaId>", "schoolYearActive": true, "yearbookDownloadEnabled": true}
  ```
  Nota: el contenedor es de solo lectura desde el entorno del agente (Docker vía proxy). Si no se puede llamar al backend, dejar los cURL al Ing. Fidel.
- [ ] **Paso 6:** cambios listos, sin commit.

### Task 2 (Tarea 2): Backend — pruebas de integración

**Archivos:**
- Crear: `amblema---backend/app/tests/integration/yearbook_download_test.py`

**Interfaces:**
- Consume: rutas de la Tarea 1; fixtures `seed_base`, `create_location`, `create_coordinator`, `create_sponsor`, `create_school`, `create_school_year` de `app/tests/fixtures.py`; `drop_testing_database` de `app/tests/base.py`. Montar `setUp`/`tearDown` como en `app/tests/integration/teacher_coevaluation_test.py` (incluido un helper `newPeca(schoolYear)` igual al suyo). En TESTING los decoradores no validan JWT, así que no se prueba el 403.

- [ ] **Paso 1: Escribir las pruebas** (clase `YearbookDownloadTest`):
  - `test_default_is_disabled`: GET `/pecaprojects/<id>/yearbook-download` → 200, `yearbookDownloadEnabled is False`, `schoolYearActive is True`.
  - `test_patch_enables_and_disables`: PATCH `true` → 200 y `True`; recargar `PecaProject` y comprobar `True`; PATCH `false` → `False`.
  - `test_patch_rejects_non_boolean`: cuerpos `{}`, `{"yearbookDownloadEnabled": "true"}`, `{"yearbookDownloadEnabled": 1}` → 400 y la bandera sigue `False`.
  - `test_patch_rejects_closed_school_year`: PECA de `create_school_year(name="2024 - 2025", status="2", ...)` → PATCH 400; GET → `schoolYearActive is False`.
  - `test_unknown_peca_returns_404`: id `"5f0000000000000000000000"` → 404 en GET y PATCH.
  - `test_list_only_active_year`: un PECA del año activo y otro de año cerrado; `GET /pecaprojects/yearbook-download` → `records` con un solo elemento, cuyo `projectId == str(self.project.id)`; un PECA con `isDeleted=True` del año activo tampoco aparece.
- [ ] **Paso 2: Ejecutar la batería completa** dentro del contenedor (comando del CLAUDE.md, sección Testing). Esperado: las 6 nuevas OK; las únicas fallas previas conocidas son las 6 por permisos de `resources/files/*` (ver `HANDOFF.md`). Si aparece otra falla, explicar si el error está en el código o en la prueba.
- [ ] **Paso 3:** cambios listos, sin commit.

### Task 3 (Tarea 3): Backoffice — columna con interruptor en `/pages/projects`

**Archivos:**
- Crear: `amblema-backoffice/src/app/services/yearbook-download.service.ts`
- Crear: `amblema-backoffice/src/app/pages/projects/yearbook-download-toggle/yearbook-download-toggle.component.{ts,html}`
- Modificar: `amblema-backoffice/src/app/pages/projects/projects.module.ts` (`declarations`)
- Modificar: `amblema-backoffice/src/app/pages/projects/projects.component.ts` (`ngOnInit`, columnas)

**Interfaces:**
- Consume: `GET /pecaprojects/yearbook-download` y `PATCH /pecaprojects/<id>/yearbook-download` (Tarea 1).
- Produce:
  ```ts
  export interface YearbookDownloadStatus { projectId: string; pecaId: string; yearbookDownloadEnabled: boolean; }
  // YearbookDownloadService (providedIn: 'root')
  statusByProject$: BehaviorSubject<Record<string, YearbookDownloadStatus>>  // clave: projectId
  loadActive(): void                       // GET lista y emite el mapa; en error emite {} y muestra toastr.error
  setEnabled(pecaId: string, enabled: boolean): Observable<YearbookDownloadStatus & { schoolYearActive: boolean }>
  ```
  URL base: `${environment.api}pecaprojects/...` (mismo patrón que `ProjectService`).

- [ ] **Paso 1: Servicio** `yearbook-download.service.ts` con la interfaz de arriba. `setEnabled`, en éxito, actualiza la entrada del mapa (inmutable) y vuelve a emitir.
- [ ] **Paso 2: Componente de celda** `YearbookDownloadToggleComponent implements ViewCell, OnInit, OnDestroy` (patrón de `pages/main-content/peca-setting/admin-year-lapses/admin-lapses/special-toggle/`), `@Input() value`, `@Input() rowData` (el `Project`; usa `rowData.id`):
  - Se suscribe a `statusByProject$` y toma `status = map[rowData.id]`; desuscribirse en `ngOnDestroy`.
  - Sin `status` → texto `—` con `title="Sin PECA del año escolar en curso"`.
  - Con `status` → `custom-switch` de Bootstrap (como `special-toggle.component.html`), `id`/`for` = `'yb-dl-' + rowData.id`, etiqueta `Habilitada` / `Deshabilitada`. Sin `FormControl`: `[checked]` + `(change)`.
  - `disabled` mientras guarda o si `!new AuthService().isAllowed(ALL_ACTIONS.PROJECT_EDIT)`.
  - Al cambiar: `setEnabled(status.pecaId, checked)`. Éxito → `CustomToastrService.updateSuccess('AmbLeMario', checked ? 'Descarga habilitada para el coordinador' : 'Descarga deshabilitada para el coordinador')`. Error → revertir el interruptor y `error('AmbLeMario', err?.error?.msg || 'No se pudo actualizar la descarga')`.
- [ ] **Paso 3: Declarar** el componente en `ProjectsModule.declarations`.
- [ ] **Paso 4: Columna** en `ProjectsComponent.ngOnInit`, después de `status`:
  ```ts
  yearbookDownload: {
    title: 'Descarga AmbLeMario',
    type: 'custom',
    renderComponent: YearbookDownloadToggleComponent,
    filter: false,
    sort: false,
  },
  ```
  Y llamar `this.yearbookDownloadService.loadActive()` junto a `this.store.dispatch(new GetProjects())`. Tras borrar un proyecto (rama `DELETE`) no hace falta recargar.
- [ ] **Paso 5: Compilar** dentro del contenedor (lo ejecuta el Ing. Fidel en el host si el agente no puede): `docker-compose -f docker-compose.dev.yml exec run_amblema_backoffice npx ng build` → sin errores.
- [ ] **Paso 6: Verificación manual:** `http://localhost:2004` → login admin → **Proyectos**. Un proyecto en fase PECA con año en curso muestra el interruptor "Deshabilitada"; al activarlo sale el toastr y al recargar sigue "Habilitada". Un proyecto en fase pasos (sin PECA del año) muestra "—".
- [ ] **Paso 7:** cambios listos, sin commit.

### Task 4 (Tarea 4): Front — ocultar botones al coordinador

**Archivos:**
- Modificar: `amblema-front/src/app/services/peca/pdf-yearbook.service.ts` (junto a `getPrintOptions`, ~línea 1558)
- Modificar: `amblema-front/src/app/peca/peca-page/pdf-templates/yearbook-pdf-template/yearbook-pdf-template.component.ts`
- Modificar: `amblema-front/src/app/peca/peca-page/pdf-templates/yearbook-pdf-template/yearbook-pdf-template.component.html:9-14`

**Interfaces:**
- Consume: `GET /pecaprojects/<id>/yearbook-download` (Tarea 1); `PecaState.getUserResume` (`src/app/store/states/peca/peca.state.ts`, devuelve `{ id, type }` con `type = userType` string).
- Produce:
  ```ts
  // PdfYearbookService
  getYearbookDownloadStatus(pecaProjectId: string): Promise<{ pecaId: string; schoolYearActive: boolean; yearbookDownloadEnabled: boolean }>
  // YearbookPdfTemplateComponent
  canDownload = false;
  ```

- [ ] **Paso 1: Servicio:** `getYearbookDownloadStatus` con `this.http.get(\`/pecaprojects/${pecaProjectId}/yearbook-download\`).toPromise()` (mismo patrón que `getPrintOptions`).
- [ ] **Paso 2: Componente:** inyectar `Store` (`@ngxs/store`). Nuevo método privado `resolveCanDownload(): Promise<void>` llamado al inicio de `setInitialData()` (dentro del `if (this.pdfData)`), antes de las demás cargas, sin bloquearlas:
  - `const type = String(this.store.selectSnapshot(PecaState.getUserResume)?.type ?? '')`.
  - Si `type !== '2'` → `canDownload = true` y salir (admin, padrino, escuela: siempre).
  - Si es `'2'` → pedir el estado: `canDownload = !status.schoolYearActive || status.yearbookDownloadEnabled` (D1). En `catch` → `canDownload = false` (D3).
  - Si `selectSnapshot` lanza (estado sin `user`), tratar como coordinador sin permiso: `false`.
- [ ] **Paso 3: Plantilla:** poner `*ngIf="canDownload"` en los botones `btn-print-version` y `btn-download-pdf`. "Regresar" y "Activar escala de grises" quedan igual. Como `canDownload` empieza en `false`, el coordinador no ve los botones mientras carga.
- [ ] **Paso 4: Compilar:** `docker-compose -f docker-compose.dev.yml exec angular8local npx ng build` → sin errores.
- [ ] **Paso 5: Verificación manual** (usar un proyecto en fase PECA del año en curso, p. ej. `2026 - 2027`):
  1. Backoffice → Proyectos → interruptor "Deshabilitada" en ese proyecto.
  2. Entrar al front como su **coordinador** → PECA → AmbLeMario → botón de descarga → `/pdf-template/yearbook`: solo "Regresar" y "Activar escala de grises".
  3. Habilitar en el backoffice; volver a abrir la vista previa: aparecen "Versión Impresa" y "Descargar PDF" y funcionan.
  4. Entrar como **admin** (`ambleadministrador@gmail.com`) desde el backoffice: Proyectos → proyecto → año escolar → PECA → AmbLeMario → vista previa. Con la bandera deshabilitada, los dos botones se ven.
  5. Como coordinador, abrir el AmbLeMario de un año cerrado (si existe): los botones se ven (D1).
- [ ] **Paso 6:** cambios listos, sin commit.

### Task 5 (Tarea 5): Documentación

**Archivos:**
- Modificar: `/home/fidel/public_html/amblema/HANDOFF.md` (raíz del ecosistema; reemplazar lo obsoleto, no solo añadir)
- Modificar o crear: `handoff.md` en la raíz de cada repo tocado, si existe la convención (si no existe, crearlo con las secciones Estado actual / Hecho / Pendiente / Decisiones).

- [ ] **Paso 1:** entrada `## 2026-11-15 — Habilitar descarga del AmbLeMario (sin commit)` con: rama, archivos por repo, endpoints y contrato JSON, decisiones D1–D5, resultado de la batería de pruebas (totales, OK y fallas con su causa), y los pasos de verificación manual pendientes.
- [ ] **Paso 2:** sin commit.

---

## Orden de ejecución

Tarea 1 → Tarea 2 → Tareas 3 y 4 (independientes entre sí, ambas dependen solo de los contratos de la Tarea 1) → Tarea 5.
