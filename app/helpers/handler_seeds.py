# app/helpers/handler_seeds.py


def create_entities():
    from app.models.entity_model import Entity

    Entity(
        name="Rol",
        actions=[
            {
                "name": "role_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "role_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "role_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "role_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Municipio",
        actions=[
            {
                "name": "municipality_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "municipality_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "municipality_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "municipality_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Año Escolar",
        actions=[
            {
                "name": "school_year_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "school_year_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "school_year_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "school_year_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Usuario Coordinador",
        actions=[
            {
                "name": "coord_user_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "coord_user_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "coord_user_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "coord_user_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Usuario Padrino",
        actions=[
            {
                "name": "sponsor_user_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "sponsor_user_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "sponsor_user_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "sponsor_user_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Usuario Escuela",
        actions=[
            {
                "name": "school_user_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "school_user_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "school_user_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "school_user_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Contenido Web",
        actions=[
            {
                "name": "web_content_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "web_content_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "web_content_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "web_content_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Post",
        actions=[
            {
                "name": "post_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "post_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "post_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "post_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Módulo de aprendizaje",
        actions=[
            {
                "name": "sponsor_user_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "sponsor_user_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "sponsor_user_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "sponsor_user_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud de Contacto Escuela",
        actions=[
            {
                "name": "request_school_contact_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_school_contact_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_school_contact_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_school_contact_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud de Contacto Padrino",
        actions=[
            {
                "name": "request_sponsor_contact_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_sponsor_contact_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_sponsor_contact_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_sponsor_contact_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud de Contacto Padrino",
        actions=[
            {
                "name": "request_coord_contact_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_coord_contact_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_coord_contact_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_coord_contact_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Paso Previo PECA",
        actions=[
            {
                "name": "peca_step_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "peca_step_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "peca_step_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "peca_step_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Proyecto",
        actions=[
            {
                "name": "project_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "project_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "project_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "project_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud de Aprobación Paso Previo PECA",
        actions=[
            {
                "name": "request_approval_step_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_approval_step_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_approval_step_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_approval_step_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud Encontrar Coordinador",
        actions=[
            {
                "name": "request_find_coord_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_find_coord_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_find_coord_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_find_coord_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud Encontrar Padrino",
        actions=[
            {
                "name": "request_find_sponsor_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_find_sponsor_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_find_sponsor_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_find_sponsor_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud Encontrar Escuela",
        actions=[
            {
                "name": "request_find_school_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_find_school_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_find_school_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_find_school_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Configuración Taller Inicial",
        actions=[
            {
                "name": "config_initial_workshop_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "config_initial_workshop_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="Configuración Planificación de Lapso",
        actions=[
            {
                "name": "config_lapse_planning_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "config_lapse_planning_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()


def create_initial_steps():

    from app.models.school_year_model import SchoolYear
    from app.models.step_model import Step

    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    if not schoolYear:
        return "An active school year is required"

    findSchool = Step(
        name="Encontrar Escuela",
        devName="findSchool",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna una escuela al proyecto"
    )
    findSchool.save()

    findSponsor = Step(
        name="Encontrar Padrino",
        devName="findSponsor",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna un padrino al proyecto"
    )
    findSponsor.save()

    findCoordinator = Step(
        name="Encontrar Coordinador",
        devName="findCoordinator",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna un coordinador al proyecto"
    )
    findCoordinator.save()

    amblemaConfirmation = Step(
        name="Confirmacion de AmbLeMa",
        devName="amblemaConfirmation",
        tag="1",
        isStandard=True,
        approvalType="1",
        hasText=True,
        text="some description"
    )
    amblemaConfirmation.save()

    coordinatorFillSchoolForm = Step(
        name="Rellenar planilla de escuela",
        devName="coordinatorFillSchoolForm",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    coordinatorFillSchoolForm.save()

    coordinatorFillSponsorForm = Step(
        name="Rellenar planilla de padrino",
        devName="coordinatorFillSponsorForm",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    coordinatorFillSponsorForm.save()

    coordinatorSendCurriculum = Step(
        name="Enviar curriculo Vitae",
        devName="coordinatorSendCurriculum",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasUpload=True,
        hasText=True,
        text="some description"

    )
    coordinatorSendCurriculum.save()

    corrdinatorCompleteTrainingModules = Step(
        name="Completar modulos de formacion",
        devName="corrdinatorCompleteTrainingModules",
        tag="2",
        isStandard=True,
        approvalType="2"
    )
    corrdinatorCompleteTrainingModules.save()

    checklistInitialWorkshop = Step(
        name="Taller inicial",
        tag="2",
        hasText=True,
        hasChecklist=True,
        text="some description",
        checklist=[{"name": "Reunion con la escuela"},
                   {"name": "reunion con el padrino"}],
        approvalType="2"
    )
    checklistInitialWorkshop.save()

    sponsorFillSchoolForm = Step(
        name="Rellenar planilla de escuela",
        devName="sponsorFillSchoolForm",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    sponsorFillSchoolForm.save()

    sponsorFillCoordinatorForm = Step(
        name="Rellenar planilla de coordinador",
        devName="sponsorFillCoordinatorForm",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    sponsorFillCoordinatorForm.save()

    sponsorAgreementSchool = Step(
        name="Convenio Padrino - Escuela",
        devName="sponsorAgreementSchool",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=True,
        hasUpload=True,
        text="some description",
        file={"name": "Agreement name",
                "url": "https://urlserver.com/files/asd.pdf"}
    )
    sponsorAgreementSchool.save()

    sponsorAgreementSchoolFoundation = Step(
        name="Convenio Escuela - Fundacion",
        devName="sponsorAgreementSchoolFoundation",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=True,
        hasUpload=True,
        text="some description",
        file={"name": "Agreement name",
                "url": "https://urlserver.com/files/asd.pdf"}
    )
    sponsorAgreementSchoolFoundation.save()

    schoolFillSponsorlForm = Step(
        name="Rellenar planilla de padrino",
        devName="schoolFillSponsorlForm",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    schoolFillSponsorlForm.save()

    schoolFillCoordinatorForm = Step(
        name="Rellenar planilla de coordinador",
        devName="schoolFillCoordinatorForm",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    schoolFillCoordinatorForm.save()

    schoolAgreementSponsor = Step(
        name="Convenio Escuela - Padrino",
        devName="schoolAgreementSponsor",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=True,
        hasUpload=True,
        text="some description",
        file={"name": "Agreement name",
                "url": "https://urlserver.com/files/asd.pdf"}
    )
    schoolAgreementSponsor.save()

    schoolAgreementFoundation = Step(
        name="Convenio Escuela - Fundacion",
        devName="schoolAgreementFoundation",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=True,
        hasUpload=True,
        text="some description",
        file={"name": "Agreement name",
                "url": "https://urlserver.com/files/asd.pdf"}
    )
    schoolAgreementFoundation.save()


def create_standard_roles():

    from app.models.role_model import Role, Permission, ActionHandler
    from app.models.entity_model import Entity

    nameDict = {
        'superadmin': 'Super Admin',
        'admin': 'Administrador',
        'coordinator': 'Coordinador',
        'sponsor': 'Padrino',
        'school': 'Escuela'
    }
    for i in range(5):
        if i == 0:
            name = 'superadmin'
        elif i == 1:
            name = 'admin'
        elif i == 2:
            name = 'coordinator'
        elif i == 3:
            name = 'sponsor'
        elif i == 4:
            name = 'school'

        role = Role.objects(devName=name).first()
        if not role:
            role = Role(
                devName=name,
                name=nameDict[name],
                isStandard=True,
                permissions=[]
            )
            entities = Entity.objects(isDeleted=False)
            for entity in entities:
                permission = Permission(
                    entityId=str(entity.id),
                    entityName=entity.name
                )
                for action in entity.actions:
                    permission.actions.append(
                        ActionHandler(
                            name=action.name,
                            label=action.label,
                            sort=1,
                            allowed=True
                        )
                    )
                role.permissions.append(permission)
            role.save()
    return "ok"
