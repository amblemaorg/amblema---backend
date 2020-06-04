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
        name="Encontrar escuela",
        devName="findSchool",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna una escuela al proyecto"
    )
    findSchool.save()

    findSponsor = Step(
        name="Encontrar padrino",
        devName="findSponsor",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna un padrino al proyecto"
    )
    findSponsor.save()

    findCoordinator = Step(
        name="Encontrar coordinador",
        devName="findCoordinator",
        tag="1",
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Asigna un coordinador al proyecto"
    )
    findCoordinator.save()

    initialWorkshopPlanning = Step(
        name="Planificación del taller inicial",
        devName="initialWorkshopPlanning",
        tag="1",
        hasText=True,
        hasVideo=True,
        isStandard=True,
        approvalType="4",
        text="Descripción de la planificación inicial",
        video={"name": "some video", "url": "https://youtube.com"}
    )
    initialWorkshopPlanning.save()

    amblemaConfirmation = Step(
        name="Confirmación de AmbLeMa",
        devName="amblemaConfirmation",
        tag="1",
        isStandard=True,
        approvalType="1",
        hasText=True,
        text="some description"
    )
    amblemaConfirmation.save()

    coordinatorFillSchoolForm = Step(
        name="Llenar planilla de escuela",
        devName="coordinatorFillSchoolForm",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    coordinatorFillSchoolForm.save()

    coordinatorFillSponsorForm = Step(
        name="Llenar planilla de padrino",
        devName="coordinatorFillSponsorForm",
        tag="2",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    coordinatorFillSponsorForm.save()

    coordinatorSendCurriculum = Step(
        name="Enviar currículo vitae",
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
        name="Completar módulos de formación",
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
        checklist=[{"name": "Reunión con la escuela"},
                   {"name": "Reunión con el padrino"}],
        approvalType="2"
    )
    checklistInitialWorkshop.save()

    sponsorPresentationSchool = Step(
        name="Presentación a la escuela",
        devName="sponsorPresentationSchool",
        tag="3",
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="some description",
        file={"name": "Some_name.pdf", "url": "https://someurl.com/file.pdf"}
    )
    sponsorPresentationSchool.save()

    sponsorKnowAmblemaMethod = Step(
        name="Conoce el método AmbLeMa",
        devName="sponsorKnowAmblemaMethod",
        tag="3",
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="some description",
        file={"name": "Some_name.pdf", "url": "https://someurl.com/file.pdf"}
    )
    sponsorKnowAmblemaMethod.save()

    sponsorFillSchoolForm = Step(
        name="Llenar planilla de escuela",
        devName="sponsorFillSchoolForm",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    sponsorFillSchoolForm.save()

    sponsorFillCoordinatorForm = Step(
        name="Llenar planilla de coordinador",
        devName="sponsorFillCoordinatorForm",
        tag="3",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    sponsorFillCoordinatorForm.save()

    sponsorAgreementSchool = Step(
        name="Convenio padrino - escuela",
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
        name="Convenio escuela - fundación",
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

    schoolPresentationSponsor = Step(
        name="Presentación al padrino",
        devName="schoolPresentationSponsor",
        tag="4",
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="some description",
        file={"name": "Some_name.pdf", "url": "https://someurl.com/file.pdf"}
    )
    schoolPresentationSponsor.save()

    schoolFillSponsorForm = Step(
        name="Llenar planilla de padrino",
        devName="schoolFillSponsorForm",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    schoolFillSponsorForm.save()

    schoolFillCoordinatorForm = Step(
        name="Llenar planilla de coordinador",
        devName="schoolFillCoordinatorForm",
        tag="4",
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="some description"
    )
    schoolFillCoordinatorForm.save()

    schoolAgreementSponsor = Step(
        name="Convenio escuela - padrino",
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
        name="Convenio escuela - fundación",
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


def create_states_and_municipalities():
    from app.models.state_model import State, Municipality

    # Amazonas
    s1 = State(name="Amazonas").save()
    Municipality(name="Alto Orinoco", state=s1).save()
    Municipality(name="Atabapo", state=s1).save()
    Municipality(name="Atures", state=s1).save()
    Municipality(name="Autana", state=s1).save()
    Municipality(name="Manapiare", state=s1).save()
    Municipality(name="Maroa", state=s1).save()
    Municipality(name="Río Negro", state=s1).save()

    # Anzoategui
    s2 = State(name="Anzoátegui").save()
    Municipality(name="Anaco", state=s2).save()
    Municipality(name="Aragua", state=s2).save()
    Municipality(name="Bolívar", state=s2).save()
    Municipality(name="Bruzual", state=s2).save()
    Municipality(name="Cajigal", state=s2).save()
    Municipality(name="Carvajal", state=s2).save()
    Municipality(name="Freites", state=s2).save()
    Municipality(name="Guanipa", state=s2).save()
    Municipality(name="Guanta", state=s2).save()
    Municipality(name="Independencia", state=s2).save()
    Municipality(name="Libertad", state=s2).save()
    Municipality(name="McGregor", state=s2).save()
    Municipality(name="Miranda", state=s2).save()
    Municipality(name="Monagas", state=s2).save()
    Municipality(name="Peñalver", state=s2).save()
    Municipality(name="Píritu", state=s2).save()
    Municipality(name="San Juan de Capistrano", state=s2).save()
    Municipality(name="Santa Ana", state=s2).save()
    Municipality(name="Simón Rodríguez", state=s2).save()
    Municipality(name="Sotillo", state=s2).save()
    Municipality(name="Urbaneja", state=s2).save()

    # Apure
    s3 = State(name="Apure").save()
    Municipality(name="Achaguas", state=s3).save()
    Municipality(name="Biruaca", state=s3).save()
    Municipality(name="Camejo", state=s3).save()
    Municipality(name="Muñoz", state=s3).save()
    Municipality(name="Páez", state=s3).save()
    Municipality(name="Rómulo Gallegos", state=s3).save()
    Municipality(name="San Fernando", state=s3).save()

    # Aragua
    s4 = State(name="Aragua").save()
    Municipality(name="Alcántara", state=s4).save()
    Municipality(name="Bolívar", state=s4).save()
    Municipality(name="Camatagua", state=s4).save()
    Municipality(name="Girardot", state=s4).save()
    Municipality(name="Iragorry", state=s4).save()
    Municipality(name="Lamas", state=s4).save()
    Municipality(name="Libertador", state=s4).save()
    Municipality(name="Mariño", state=s4).save()
    Municipality(name="Michelena", state=s4).save()
    Municipality(name="Ocumare de la Costa de Oro", state=s4).save()
    Municipality(name="Revenga", state=s4).save()
    Municipality(name="Ribas", state=s4).save()
    Municipality(name="San Casimiro", state=s4).save()
    Municipality(name="San Sebastián", state=s4).save()
    Municipality(name="Sucre", state=s4).save()
    Municipality(name="Tovar", state=s4).save()
    Municipality(name="Urdaneta", state=s4).save()
    Municipality(name="Zamora", state=s4).save()

    # Barinas
    s5 = State(name="Barinas").save()
    Municipality(name="Alberto Arvelo Torrealba", state=s5).save()
    Municipality(name="Andrés Eloy Blanco", state=s5).save()
    Municipality(name="Antonio José de Sucre", state=s5).save()
    Municipality(name="Arismendi", state=s5).save()
    Municipality(name="Barinas", state=s5).save()
    Municipality(name="Bolívar", state=s5).save()
    Municipality(name="Cruz Paredes", state=s5).save()
    Municipality(name="Ezequiel Zamora", state=s5).save()
    Municipality(name="Obispos", state=s5).save()
    Municipality(name="Pedraza", state=s5).save()
    Municipality(name="Rojas", state=s5).save()
    Municipality(name="Sosa", state=s5).save()

    # Bolívar
    s6 = State(name="Bolívar").save()
    Municipality(name="Angostura", state=s6).save()
    Municipality(name="Angostura del Orinoco", state=s6).save()
    Municipality(name="Caroní", state=s6).save()
    Municipality(name="Cedeño", state=s6).save()
    Municipality(name="Chien", state=s6).save()
    Municipality(name="El Callao", state=s6).save()
    Municipality(name="Gran Sabana", state=s6).save()
    Municipality(name="Piar", state=s6).save()
    Municipality(name="Roscio", state=s6).save()
    Municipality(name="Sifontes", state=s6).save()
    Municipality(name="Sucre", state=s6).save()

    # Carabobo
    s7 = State(name="Carabobo").save()
    Municipality(name="Bejuma", state=s7).save()
    Municipality(name="Carlos Arvelo", state=s7).save()
    Municipality(name="Diego Ibarra", state=s7).save()
    Municipality(name="Guacara", state=s7).save()
    Municipality(name="Libertador", state=s7).save()
    Municipality(name="Los Guayos", state=s7).save()
    Municipality(name="Miranda", state=s7).save()
    Municipality(name="Mora", state=s7).save()
    Municipality(name="Montalbán", state=s7).save()
    Municipality(name="Naguanagua", state=s7).save()
    Municipality(name="Puerto Cabello", state=s7).save()
    Municipality(name="San Diego", state=s7).save()
    Municipality(name="San Joaquín", state=s7).save()
    Municipality(name="Valencia", state=s7).save()

    # Cojedes
    s8 = State(name="Cojedes").save()
    Municipality(name="Anzoátegui", state=s8).save()
    Municipality(name="Tinaquillo", state=s8).save()
    Municipality(name="Girardot", state=s8).save()
    Municipality(name="Lima Blanco", state=s8).save()
    Municipality(name="Pao de San Juan Bautista", state=s8).save()
    Municipality(name="Ricaurte", state=s8).save()
    Municipality(name="Rómulo Gallegos", state=s8).save()
    Municipality(name="Ezequiel Zamora", state=s8).save()
    Municipality(name="Tinaco", state=s8).save()

    # Delta Amacuro
    s9 = State(name="Delta Amacuro").save()
    Municipality(name="Antonio Díaz", state=s9).save()
    Municipality(name="Casacoima", state=s9).save()
    Municipality(name="Pedernales", state=s9).save()
    Municipality(name="Tucupita", state=s9).save()

    # Distrito Capital
    s10 = State(name="Distrito Capital").save()
    Municipality(name="Libertador", state=s10).save()

    # Falcón
    s11 = State(name="Falcón").save()
    Municipality(name="Acosta", state=s11).save()
    Municipality(name="Bolívar", state=s11).save()
    Municipality(name="Buchivacoa", state=s11).save()
    Municipality(name="Carirubana", state=s11).save()
    Municipality(name="Colina", state=s11).save()
    Municipality(name="Dabajuro", state=s11).save()
    Municipality(name="Democracia", state=s11).save()
    Municipality(name="Falcón", state=s11).save()
    Municipality(name="Federación", state=s11).save()
    Municipality(name="Iturriza", state=s11).save()
    Municipality(name="Jacura", state=s11).save()
    Municipality(name="Los Taques", state=s11).save()
    Municipality(name="Manaure", state=s11).save()
    Municipality(name="Mauroa", state=s11).save()
    Municipality(name="Miranda", state=s11).save()
    Municipality(name="Palmasola", state=s11).save()
    Municipality(name="Petit", state=s11).save()
    Municipality(name="Píritu", state=s11).save()
    Municipality(name="San Francisco", state=s11).save()
    Municipality(name="Sucre", state=s11).save()
    Municipality(name="Silva", state=s11).save()
    Municipality(name="Tocópero", state=s11).save()
    Municipality(name="Unión", state=s11).save()
    Municipality(name="Urumaco", state=s11).save()
    Municipality(name="Zamora", state=s11).save()

    # Guárico
    s12 = State(name="Guárico").save()
    Municipality(name="Camaguán", state=s12).save()
    Municipality(name="Chaguaramas", state=s12).save()
    Municipality(name="El Socorro", state=s12).save()
    Municipality(name="Las Mercedes", state=s12).save()
    Municipality(name="Leonardo Infante", state=s12).save()
    Municipality(name="Julián Mellado", state=s12).save()
    Municipality(name="Francisco de Miranda", state=s12).save()
    Municipality(name="Monagas", state=s12).save()
    Municipality(name="Ortiz", state=s12).save()
    Municipality(name="Ribas", state=s12).save()
    Municipality(name="Roscio", state=s12).save()
    Municipality(name="San Gerónimo de Guayabal", state=s12).save()
    Municipality(name="San José de Guaribe", state=s12).save()
    Municipality(name="Santa María de Ipire", state=s12).save()
    Municipality(name="Zaraza", state=s12).save()

    # La Guaira
    s13 = State(name="La Guaira").save()
    Municipality(name="Vargas", state=s13).save()

    # Lara
    s14 = State(name="Lara").save()
    Municipality(name="Blanco", state=s14).save()
    Municipality(name="Crespo", state=s14).save()
    Municipality(name="Iribarren", state=s14).save()
    Municipality(name="Jiménez", state=s14).save()
    Municipality(name="Morán", state=s14).save()
    Municipality(name="Palavecino", state=s14).save()
    Municipality(name="Planas", state=s14).save()
    Municipality(name="Torres", state=s14).save()
    Municipality(name="Urdaneta", state=s14).save()

    # Mérida
    s15 = State(name="Mérida").save()
    Municipality(name="Adriani", state=s15).save()
    Municipality(name="Andrés Bello", state=s15).save()
    Municipality(name="Aricagua", state=s15).save()
    Municipality(name="Briceño", state=s15).save()
    Municipality(name="Chacón", state=s15).save()
    Municipality(name="Campo Elías", state=s15).save()
    Municipality(name="Dávila", state=s15).save()
    Municipality(name="Febres Cordero", state=s15).save()
    Municipality(name="Guaraque", state=s15).save()
    Municipality(name="Libertador", state=s15).save()
    Municipality(name="Miranda", state=s15).save()
    Municipality(name="Noguera", state=s15).save()
    Municipality(name="Parra Olmedo", state=s15).save()
    Municipality(name="Pinto Salinas", state=s15).save()
    Municipality(name="Pueblo Llano", state=s15).save()
    Municipality(name="Quintero", state=s15).save()
    Municipality(name="Rangel", state=s15).save()
    Municipality(name="Ramos de Lora", state=s15).save()
    Municipality(name="Salas", state=s15).save()
    Municipality(name="Marquina", state=s15).save()
    Municipality(name="Sucre", state=s15).save()
    Municipality(name="Tovar", state=s15).save()
    Municipality(name="Zea", state=s15).save()

    # Miranda
    s16 = State(name="Miranda").save()
    Municipality(name="Acevedo", state=s16).save()
    Municipality(name="Andrés Bello", state=s16).save()
    Municipality(name="Baruta", state=s16).save()
    Municipality(name="Brión", state=s16).save()
    Municipality(name="Bolívar", state=s16).save()
    Municipality(name="Buroz", state=s16).save()
    Municipality(name="Carrizal", state=s16).save()
    Municipality(name="Chacao", state=s16).save()
    Municipality(name="Cristóbal Rojas", state=s16).save()
    Municipality(name="El Hatillo", state=s16).save()
    Municipality(name="Guaicaipuro", state=s16).save()
    Municipality(name="Gual", state=s16).save()
    Municipality(name="Independencia", state=s16).save()
    Municipality(name="Lander", state=s16).save()
    Municipality(name="Los Salias", state=s16).save()
    Municipality(name="Páez", state=s16).save()
    Municipality(name="Paz Castillo", state=s16).save()
    Municipality(name="Plaza", state=s16).save()
    Municipality(name="Sucre", state=s16).save()
    Municipality(name="Urdaneta", state=s16).save()
    Municipality(name="Zamora", state=s16).save()

    # Monagas
    s17 = State(name="Monagas").save()
    Municipality(name="Acosta", state=s17).save()
    Municipality(name="Aguasay", state=s17).save()
    Municipality(name="Bolívar", state=s17).save()
    Municipality(name="Caripe", state=s17).save()
    Municipality(name="Cedeño", state=s17).save()
    Municipality(name="Libertador", state=s17).save()
    Municipality(name="Maturín", state=s17).save()
    Municipality(name="Piar", state=s17).save()
    Municipality(name="Punceres", state=s17).save()
    Municipality(name="Santa Bárbara", state=s17).save()
    Municipality(name="Sotillo", state=s17).save()
    Municipality(name="Uracoa", state=s17).save()
    Municipality(name="Zamora", state=s17).save()

    # Nueva Esparta
    s18 = State(name="Nueva Esparta").save()
    Municipality(name="Antolín", state=s18).save()
    Municipality(name="Arismendi", state=s18).save()
    Municipality(name="Díaz", state=s18).save()
    Municipality(name="García", state=s18).save()
    Municipality(name="Gómez", state=s18).save()
    Municipality(name="Macanao", state=s18).save()
    Municipality(name="Maneiro", state=s18).save()
    Municipality(name="Marcano", state=s18).save()
    Municipality(name="Mariño", state=s18).save()
    Municipality(name="Tubores", state=s18).save()
    Municipality(name="Villalba", state=s18).save()

    # Portuguesa
    s19 = State(name="Portuguesa").save()
    Municipality(name="Agua Blanca", state=s19).save()
    Municipality(name="Araure", state=s19).save()
    Municipality(name="Esteller", state=s19).save()
    Municipality(name="Guanare", state=s19).save()
    Municipality(name="Guanarito", state=s19).save()
    Municipality(name="Ospino", state=s19).save()
    Municipality(name="Páez", state=s19).save()
    Municipality(name="Papelón", state=s19).save()
    Municipality(name="San Genaro de Boconoíto", state=s19).save()
    Municipality(name="San Rafael de Onoto", state=s19).save()
    Municipality(name="Santa Rosalía", state=s19).save()
    Municipality(name="Sucre", state=s19).save()
    Municipality(name="Turén", state=s19).save()
    Municipality(name="Unda", state=s19).save()

    # Sucre
    s20 = State(name="Sucre").save()
    Municipality(name="Arismendi", state=s20).save()
    Municipality(name="Benítez", state=s20).save()
    Municipality(name="Bermúdez", state=s20).save()
    Municipality(name="Blanco", state=s20).save()
    Municipality(name="Bolívar", state=s20).save()
    Municipality(name="Cajigal", state=s20).save()
    Municipality(name="Cruz Salmerón Acosta", state=s20).save()
    Municipality(name="Libertador", state=s20).save()
    Municipality(name="Mariño", state=s20).save()
    Municipality(name="Mata", state=s20).save()
    Municipality(name="Mejía", state=s20).save()
    Municipality(name="Montes", state=s20).save()
    Municipality(name="Ribero", state=s20).save()
    Municipality(name="Sucre", state=s20).save()
    Municipality(name="Valdez", state=s20).save()

    # Táchira
    s21 = State(name="Táchira").save()
    Municipality(name="Andrés Bello", state=s21).save()
    Municipality(name="Ayacucho", state=s21).save()
    Municipality(name="Bolívar", state=s21).save()
    Municipality(name="Cárdenas", state=s21).save()
    Municipality(name="Córdoba", state=s21).save()
    Municipality(name="Fernández", state=s21).save()
    Municipality(name="Guásimos", state=s21).save()
    Municipality(name="Hevia", state=s21).save()
    Municipality(name="Independencia", state=s21).save()
    Municipality(name="Jáuregui", state=s21).save()
    Municipality(name="Junín", state=s21).save()
    Municipality(name="Libertad", state=s21).save()
    Municipality(name="Libertador", state=s21).save()
    Municipality(name="Lobatera", state=s21).save()
    Municipality(name="Maldonado", state=s21).save()
    Municipality(name="Michelena", state=s21).save()
    Municipality(name="Miranda", state=s21).save()
    Municipality(name="Panamericano", state=s21).save()
    Municipality(name="Rómulo Costa", state=s21).save()
    Municipality(name="San Cristóbal", state=s21).save()
    Municipality(name="San Judas Tadeo", state=s21).save()
    Municipality(name="Seboruco", state=s21).save()
    Municipality(name="Simón Rodríguez", state=s21).save()
    Municipality(name="Sucre", state=s21).save()
    Municipality(name="Torbes", state=s21).save()
    Municipality(name="Urdaneta", state=s21).save()
    Municipality(name="Ureña", state=s21).save()
    Municipality(name="Uribante", state=s21).save()
    Municipality(name="Vargas", state=s21).save()

    # Trujillo
    s22 = State(name="Trujillo").save()
    Municipality(name="Andrés Bello", state=s22).save()
    Municipality(name="Boconó", state=s22).save()
    Municipality(name="Bolívar", state=s22).save()
    Municipality(name="Candelaria", state=s22).save()
    Municipality(name="Carache", state=s22).save()
    Municipality(name="Campos Elías", state=s22).save()
    Municipality(name="Carvajal", state=s22).save()
    Municipality(name="Escuque", state=s22).save()
    Municipality(name="La Ceiba", state=s22).save()
    Municipality(name="Márquez Cañizales", state=s22).save()
    Municipality(name="Miranda", state=s22).save()
    Municipality(name="Monte Carmelo", state=s22).save()
    Municipality(name="Motatán", state=s22).save()
    Municipality(name="Pampán", state=s22).save()
    Municipality(name="Pampanito", state=s22).save()
    Municipality(name="Rangel", state=s22).save()
    Municipality(name="Sucre", state=s22).save()
    Municipality(name="Trujillo", state=s22).save()
    Municipality(name="Urdaneta", state=s22).save()
    Municipality(name="Valera", state=s22).save()

    # Yaracuy
    s23 = State(name="Yaracuy").save()
    Municipality(name="Arístides Bastidas", state=s23).save()
    Municipality(name="Bolívar", state=s23).save()
    Municipality(name="Bruzual", state=s23).save()
    Municipality(name="Cocorote", state=s23).save()
    Municipality(name="Independencia", state=s23).save()
    Municipality(name="La Trinidad", state=s23).save()
    Municipality(name="Monge", state=s23).save()
    Municipality(name="Nirgua", state=s23).save()
    Municipality(name="Páez", state=s23).save()
    Municipality(name="Peña", state=s23).save()
    Municipality(name="San Felipe", state=s23).save()
    Municipality(name="Sucre", state=s23).save()
    Municipality(name="Urachiche", state=s23).save()
    Municipality(name="Veroes", state=s23).save()

    # Zulia
    s24 = State(name="Zulia").save()
    Municipality(name="Bolívar", state=s24).save()
    Municipality(name="Baralt", state=s24).save()
    Municipality(name="Cabimas", state=s24).save()
    Municipality(name="Catatumbo", state=s24).save()
    Municipality(name="Colón", state=s24).save()
    Municipality(name="Guajira", state=s24).save()
    Municipality(name="Padilla", state=s24).save()
    Municipality(name="Pulgar", state=s24).save()
    Municipality(name="Lossada", state=s24).save()
    Municipality(name="Semprún", state=s24).save()
    Municipality(name="La Cañada de Urdaneta", state=s24).save()
    Municipality(name="Lagunillas", state=s24).save()
    Municipality(name="Machiques", state=s24).save()
    Municipality(name="Mara", state=s24).save()
    Municipality(name="Maracaibo", state=s24).save()
    Municipality(name="Miranda", state=s24).save()
    Municipality(name="Rosario", state=s24).save()
    Municipality(name="San Francisco", state=s24).save()
    Municipality(name="Santa Rita", state=s24).save()
    Municipality(name="Sucre", state=s24).save()
    Municipality(name="Valmore Rodríguez", state=s24).save()
