# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, '/home')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import current_app
from app import create_app

app = create_app(os.getenv('INSTANCE', 'development'))

with app.app_context():
    from app.models.school_year_model import SchoolYear
    from app.models.step_model import Step
    from app.models.project_model import Project

    print("Iniciando sincronización del paso 'Acuerdo entre Coordinador – Fundación AmbLeMa' en los proyectos...")

    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    if not schoolYear:
        print("Error: No hay un año escolar activo.")
        sys.exit(1)

    print(f"Año escolar activo: {schoolYear.name} ({schoolYear.id})")

    step = Step.objects(
        schoolYear=schoolYear.id,
        isDeleted=False,
        name__icontains="Acuerdo entre Coordinador"
    ).first()

    if not step:
        step = Step.objects(
            schoolYear=schoolYear.id,
            isDeleted=False,
            devName="coordinatorAgreementFundation"
        ).first()

    if not step:
        print("Error: No se encontró el paso 'Acuerdo entre Coordinador – Fundación AmbLeMa' en la colección de steps.")
        sys.exit(1)

    print(f"Paso encontrado en BD (steps):")
    print(f"  ID: {step.id}")
    print(f"  Nombre: {step.name}")
    print(f"  devName: {step.devName}")
    print(f"  hasFile: {step.hasFile}")
    print(f"  files: {step.files}")
    print(f"  hasUpload: {step.hasUpload}")
    print(f"  isStandard: {step.isStandard}")
    print(f"  sort: {step.sort}")

    step_id_str = str(step.id)
    projects = Project.objects(schoolYear=schoolYear.id, isDeleted=False)
    print(f"Total proyectos a revisar: {projects.count()}")

    updated_count = 0
    for project in projects:
        step_ctrl = None
        for s in project.stepsProgress.steps:
            if s.id == step_id_str or s.devName in ("coordinatorInitialWorkshop", "coordinatorAgreementFundation") or "Acuerdo entre Coordinador" in s.name:
                step_ctrl = s
                break

        if step_ctrl:
            step_ctrl.id = step_id_str
            step_ctrl.name = step.name
            step_ctrl.devName = step.devName
            step_ctrl.hasText = step.hasText
            step_ctrl.hasDate = step.hasDate
            step_ctrl.hasFile = step.hasFile
            step_ctrl.hasVideo = step.hasVideo
            step_ctrl.hasChecklist = step.hasChecklist
            step_ctrl.hasUpload = step.hasUpload
            step_ctrl.text = step.text
            step_ctrl.file = step.file
            step_ctrl.file2 = step.file2
            step_ctrl.files = []
            step_ctrl.video = step.video
            step_ctrl.approvalType = step.approvalType
            step_ctrl.isStandard = step.isStandard
            step_ctrl.sort = step.sort

            # Clean up any approvalHistory entry that had PRESENTACION_AMBLEMA.pdf incorrectly attached
            if step_ctrl.approvalHistory:
                valid_approvals = []
                for apprv in step_ctrl.approvalHistory:
                    uploaded = apprv.data.get('stepUploadedFile') if apprv.data else None
                    if uploaded and 'PRESENTACION_AMBLEMA' in str(uploaded):
                        continue
                    valid_approvals.append(apprv)
                if len(valid_approvals) != len(step_ctrl.approvalHistory):
                    step_ctrl.approvalHistory = valid_approvals
                    if not valid_approvals and step_ctrl.status == "2":
                        step_ctrl.status = "1"
                        step_ctrl.uploadedFile = None

            project.stepsProgress.updateProgress()
            project.save()
            updated_count += 1
            print(f"  [OK] Proyecto {project.id} ({project.code}) actualizado.")
        else:
            print(f"  [WARN] Paso no encontrado en proyecto {project.id}")

    print(f"\nSincronización completada exitosamente. Total proyectos actualizados: {updated_count}")
