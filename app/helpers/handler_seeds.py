# app/helpers/handler_seeds.py


def create_entities():
    from app.models.entity_model import Entity

    Entity(
        name="PECA Actividades genéricas",
        devName="ActivityPeca",
        actions=[
            {
                "name": "activity_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "activity_peca_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="PECA Agenda de actividades",
        devName="ScheduleActivity",
        actions=[
            {
                "name": "schedule_peca_view",
                "label": "Ver",
                "sort": 1
            }
        ]
    ).save()

    Entity(
        name="PECA Slider de actividades",
        devName="ActivitiesSlider",
        actions=[
            {
                "name": "activities_slider_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "activities_slider_edit",
                "label": "Enviar solicitud",
                "sort": 3
            },
            {
                "name": "activities_slider_delete",
                "label": "Cancelar solicitud",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="PECA AmbLeMonedas",
        devName="AmblecoinsPeca",
        actions=[
            {
                "name": "amblecoins_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "amblecoins_peca_edit",
                "label": "Editar",
                "sort": 3
            }
        ]
    ).save()

    Entity(
        name="PECA Convención anual",
        devName="AnnualConventionPeca",
        actions=[
            {
                "name": "annual_convention_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "annual_convention_peca_edit",
                "label": "Editar",
                "sort": 3
            },
        ]
    ).save()

    Entity(
        name="PECA preparación anual",
        devName="AnnualPreparationPeca",
        actions=[
            {
                "name": "annual_preparation_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "annual_preparation_peca_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="PECA Taller inicial",
        devName="InitialWorkshopPeca",
        actions=[
            {
                "name": "initial_workshop_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "initial_workshop_edit",
                "label": "Editar",
                "sort": 2
            },
            {
                "name": "initial_workshop_delete",
                "label": "Cancelar solicitud",
                "sort": 3
            }
        ]
    ).save()

    Entity(
        name="PECA Planificación de lapso",
        devName="LapsePlanningPeca",
        actions=[
            {
                "name": "lapse_planning_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "lapse_planning_peca_edit",
                "label": "Editar",
                "sort": 2
            },
            {
                "name": "lapse_planning_peca_delete",
                "label": "Cancelar solicitud",
                "sort": 3
            }
        ]
    ).save()

    Entity(
        name="PECA Olimpíadas",
        devName="OlympicsPeca",
        actions=[
            {
                "name": "olympics_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "olympics_peca_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "olympics_peca_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "olympics_peca_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="PECA Escuela",
        devName="SchoolPeca",
        actions=[
            {
                "name": "school_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "school_peca_edit",
                "label": "Editar",
                "sort": 3
            }
        ]
    ).save()

    Entity(
        name="PECA Docente",
        devName="Teacher",
        actions=[
            {
                "name": "teacher_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "teacher_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "teacher_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "teacher_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="PECA Testimonio de docentes",
        devName="TeacherTestimonial",
        actions=[
            {
                "name": "teacher_testimonial_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "teacher_testimonial_edit",
                "label": "Enviar solicitud",
                "sort": 3
            },
            {
                "name": "teacher_testimonial_delete",
                "label": "Cancelar solicitud",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="PECA Sección",
        devName="Section",
        actions=[
            {
                "name": "section_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "section_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "section_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "section_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="PECA Estudiante",
        devName="Student",
        actions=[
            {
                "name": "student_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "student_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "student_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "student_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="PECA Anuario",
        devName="Yearbook",
        actions=[
            {
                "name": "yearbook_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "yearbook_edit",
                "label": "Enviar solicitud",
                "sort": 2
            },
            {
                "name": "yearbook_delete",
                "label": "Cancelar solicitud",
                "sort": 3
            },

        ]
    ).save()

    Entity(
        name="PECA Actividad especial de lapso",
        devName="SpecialActivity",
        actions=[
            {
                "name": "special_activity_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "special_activity_edit",
                "label": "Enviar solicitud",
                "sort": 2
            },
            {
                "name": "special_activity_delete",
                "label": "Cancelar solicitud",
                "sort": 3
            }
        ]
    ).save()

    Entity(
        name="PECA Estrategias de seguimiento de actividades",
        devName="MonitoringActivityPeca",
        actions=[
            {
                "name": "monitoring_activity_peca_view",
                "label": "Ver",
                "sort": 1
            },
        ]
    ).save()

    Entity(
        name="PECA temática ambiental",
        devName="EnvironmentalProjectPeca",
        actions=[
            {
                "name": "environmental_project_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "environmental_project_peca_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="PECA Diagnósticos",
        devName="Diagnostics",
        actions=[
            {
                "name": "diagnostics_peca_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "diagnostics_peca_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "diagnostics_peca_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "diagnostics_peca_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Usuario administrador",
        devName="AdminUser",
        actions=[
            {
                "name": "admin_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "admin_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "admin_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "admin_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Usuario coordinador",
        devName="CoordinatorUser",
        actions=[
            {
                "name": "coordinator_user_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "coordinator_user_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "coordinator_user_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "coordinator_user_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Usuario escuela",
        devName="SchoolUser",
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
        name="Usuario padrino",
        devName="SponsorUser",
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
        name="Proyecto ambiental",
        devName="EnvironmentalProject",
        actions=[
            {
                "name": "environmental_project_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "environmental_project_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="Estrategias de seguimiento de actividades",
        devName="MonitoringActivity",
        actions=[
            {
                "name": "monitoring_activity_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "monitoring_activity_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="Metas",
        devName="GoalSetting",
        actions=[
            {
                "name": "goal_setting_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "goal_setting_edit",
                "label": "Editar",
                "sort": 2
            }
        ]
    ).save()

    Entity(
        name="Módulos de aprendizaje",
        devName="LearningModule",
        actions=[
            {
                "name": "learning_module_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "learning_module_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "learning_module_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "learning_module_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Proyecto",
        devName="Project",
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
        name="Solicitud de aprobación de contenido",
        devName="RequestContentApproval",
        actions=[
            {
                "name": "request_content_approval_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_content_approval_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_content_approval_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud de creación de usuario",
        devName="RequestFindUser",
        actions=[
            {
                "name": "request_find_user_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_find_user_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "request_find_user_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_find_user_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Solicitud de creación de proyectos",
        devName="RequestCreateProject",
        actions=[
            {
                "name": "request_create_project_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_create_project_edit",
                "label": "Editar",
                "sort": 2
            },
            {
                "name": "request_create_project_delete",
                "label": "Eliminar",
                "sort": 3
            }
        ]
    ).save()

    Entity(
        name="Solicitud de confirmación de proyectos",
        devName="RequestProjectApproval",
        actions=[
            {
                "name": "request_project_approval_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "request_project_approval_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "request_project_approval_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Rol",
        devName="Role",
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
        name="Período escolar",
        devName="SchoolYear",
        actions=[
            {
                "name": "school_year_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "school_year_create",
                "label": "Iniciar",
                "sort": 2
            },
            {
                "name": "school_year_enable_activity",
                "label": "Habilitar actividades por lapso",
                "sort": 3
            },
            {
                "name": "school_year_enroll_school",
                "label": "Inscribir escuelas",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Municipio",
        devName="Municipality",
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
        name="Pasos previos",
        devName="Step",
        actions=[
            {
                "name": "step_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "step_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "step_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "step_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Actividades",
        devName="Activity",
        actions=[
            {
                "name": "activity_view",
                "label": "Ver",
                "sort": 1
            },
            {
                "name": "activity_create",
                "label": "Crear",
                "sort": 2
            },
            {
                "name": "activity_edit",
                "label": "Editar",
                "sort": 3
            },
            {
                "name": "activity_delete",
                "label": "Eliminar",
                "sort": 4
            }
        ]
    ).save()

    Entity(
        name="Reportes",
        devName="Report",
        actions=[
            {
                "name": "report_diagnostics_view",
                "label": "Diagnósticos",
                "sort": 1
            },
            {
                "name": "report_sponsors_view",
                "label": "Padrinos",
                "sort": 2
            },
            {
                "name": "report_sponsor_actives_view",
                "label": "Padrinos activos - inactivos",
                "sort": 3
            },
            {
                "name": "report_coordinator_view",
                "label": "Coordinadores",
                "sort": 4
            },
            {
                "name": "report_school_view",
                "label": "Escuelas",
                "sort": 5
            },
            {
                "name": "report_teacher_view",
                "label": "Docentes",
                "sort": 6
            },
            {
                "name": "report_olympics_view",
                "label": "Olimpíadas de matemáticas",
                "sort": 7
            },
            {
                "name": "report_enrolled_schools_view",
                "label": "Escuelas inscritas",
                "sort": 8
            }
        ]
    ).save()

    Entity(
        name="Web",
        devName="Web",
        actions=[
            {
                "name": "home_page_edit",
                "label": "Configurar página inicio",
                "sort": 1
            },
            {
                "name": "about_us_page_edit",
                "label": "Administrar página nosotros",
                "sort": 2
            },
            {
                "name": "sponsor_page_edit",
                "label": "Administrar página padrinos",
                "sort": 3
            },
            {
                "name": "coordinator_page_edit",
                "label": "Administrar página coordinadores",
                "sort": 4
            },
            {
                "name": "school_page_edit",
                "label": "Administrar página escuelas",
                "sort": 4
            },
            {
                "name": "blog_page_edit",
                "label": "Administrar blog",
                "sort": 4
            }
        ]
    ).save()


def create_initial_steps():

    from app.models.school_year_model import SchoolYear
    from app.models.step_model import Step

    schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
    if not schoolYear:
        return "An active school year is required"

    # Hard-delete old step templates for the active school year to avoid duplicates
    Step.objects(schoolYear=schoolYear.id).delete()

    # ----------------------------------------------------
    # ROL PADRINO (Sponsor) - tag = "3"
    # ----------------------------------------------------
    sponsorKnowAmblemaMethod = Step(
        name="Conoce el método AmbLeMa",
        devName="sponsorKnowAmblemaMethod",
        tag="3",
        sort=1,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="Si aún no está familiarizado con el método AmbLeMa, le invitamos a consultar el documento adjunto (dossier), donde encontrará respuestas claras a las preguntas fundamentales: <strong>¿Qué es AmbLeMa?, ¿en qué consiste? y ¿cuál es su propósito?</strong> Este material describe de manera precisa el método, su estructura y su alcance dentro de las escuelas, lo que le permitirá comprender cómo funciona la Herramienta Socio Educativa y el impacto que genera en la calidad educativa.",
        file={"name": "Metodo_AmbLeMa.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    sponsorKnowAmblemaMethod.save()

    sponsorFindSchool = Step(
        name="Encontrar escuela",
        devName="sponsorFindSchool",
        tag="3",
        sort=2,
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Si deseas apoyar la expansión de la Herramienta Educativa AmbLeMa, puedes encontrar una escuela cercana que presente necesidades diversas y cuente con un equipo directivo y docente dispuesto a asumir con responsabilidad y sentido de pertenencia la aplicación y supervisión de la Herramienta Educativa AmbLeMa, con el propósito de impulsar un verdadero salto en la Calidad Educativa.",
        schoolYear=schoolYear
    )
    sponsorFindSchool.save()

    sponsorPresentationSchool = Step(
        name="Presentación a la escuela",
        devName="sponsorPresentationSchool",
        tag="3",
        sort=3,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="Una vez que haya identificado una escuela con necesidades y disposición para trabajar con la Herramienta Socio Educativa AmbLeMa, solicite una reunión con el personal directivo y docente para presentarles en qué consiste la herramienta y expresar su interés en apadrinar la institución.<br><br>Para facilitar esta reunión, le recomendamos revisar el documento adjunto, que contiene un resumen claro sobre la Fundación AmbLeMa, así como el enlace al video de AmbLeMa. Estos materiales le permitirán ofrecer una explicación precisa y completa del programa.<br><br>Durante este encuentro, es fundamental que la directiva comprenda el alcance del apadrinamiento, los compromisos que implica y el <strong>acompañamiento permanente que AmbLeMa brinda a los docentes</strong>, orientado a fortalecer sus prácticas pedagógicas y promover un verdadero salto en la calidad educativa. Su rol como padrino será determinante para motivar, orientar y acompañar a la escuela en este primer acercamiento al programa.",
        file={"name": "Presentacion_Escuela.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    sponsorPresentationSchool.save()

    sponsorFillSchoolForm = Step(
        name="Registrar Escuela en la página web de AmbLeMa",
        devName="sponsorFillSchoolForm",
        tag="3",
        sort=4,
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="Si la escuela está de acuerdo en asumir el compromiso, <strong>indica a su director(a)</strong> que debe ingresar a la página web de AmbLeMa (<a href=\"https://www.amblema.org\" target=\"_blank\">www.amblema.org</a>), ir a la <strong>pestaña Inicio</strong>, desplazarse hasta el final y seleccionar la opción <strong>“¿Te gustaría que AmbLeMa esté en tu escuela?”</strong> para llenar todos los datos de la institución. Este paso es indispensable para iniciar el proceso de evaluación.<br><br>Después del registro de la escuela, deben esperar la <strong>aprobación de Fundación AmbLeMa</strong> para organizar el <strong>Taller Inicial</strong> de la herramienta educativa con todo el equipo docente.",
        schoolYear=schoolYear
    )
    sponsorFillSchoolForm.save()

    sponsorFindCoordinator = Step(
        name="Encontrar un Coordinador",
        devName="sponsorFindCoordinator",
        tag="3",
        sort=5,
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="El Coordinador AmbLeMa es una persona proactiva y con un alto sentido de responsabilidad, encargada de supervisar y evaluar en cada escuela la aplicación de la Herramienta Socio Educativa. Para desempeñarse este rol, debe cumplir con los requisitos establecidos y ser aprobado por la Fundación AmbLeMa.<br><br>Para conocer con mayor detalle el <strong>rol y las competencias</strong> que debe tener un <strong>Coordinador AmbLeMa</strong>, descarga el documento adjunto.<br><br>Si conoces a una persona que reúna el perfil de un Coordinador AmbLeMa, pídele que ingrese a la página web de AmbLeMa (<a href=\"https://www.amblema.org\" target=\"_blank\">www.amblema.org</a>), vaya a la <strong>pestaña Inicio</strong>, se desplace hasta el final y seleccione la opción <strong>“¿Te gustaría ser Coordinador AmbLeMa?”</strong>. Allí deberá llenar todos los datos solicitados.",
        schoolYear=schoolYear
    )
    sponsorFindCoordinator.save()

    sponsorWorkshopPlanning = Step(
        name="Planificación del Taller Inicial",
        devName="sponsorWorkshopPlanning",
        tag="3",
        sort=6,
        isStandard=True,
        approvalType="1",
        hasText=True,
        hasFile=False,
        hasUpload=False,
        hasVideo=True,
        text="El Taller Inicial va dirigido al personal docente y directivo de la institución. Planifica con la Fundación AmbLeMa el día, lugar y la logística necesaria para dictar el taller. Asegura la participación de todo el personal docente de la escuela.",
        video={"name": "Video AmbLeMa", "url": "https://www.youtube.com/watch?v=0c19cCw92FY"},
        schoolYear=schoolYear
    )
    sponsorWorkshopPlanning.save()

    sponsorAgreementSchool = Step(
        name="Convenio Padrino - Escuela",
        devName="sponsorAgreementSchool",
        tag="3",
        sort=7,
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=False,
        hasUpload=True,
        text="Para formalizar la relación entre el <strong>Padrino y la Escuela</strong>, se procede a elaborar un <strong>convenio</strong> mediante el cual se establecen los compromisos de ambas partes y se notifica a la Fundación AmbLeMa del acuerdo alcanzado. Este documento, <strong>que será firmado el día del Taller Inicial</strong>, es indispensable para autorizar la aplicación de la Herramienta Socio Educativa en la institución. En tal sentido, se adjunta un modelo de convenio como referencia.",
        schoolYear=schoolYear
    )
    sponsorAgreementSchool.save()

    # ----------------------------------------------------
    # ROL COORDINADOR (Coordinator) - tag = "2"
    # ----------------------------------------------------
    coordinatorKnowAmblemaMethod = Step(
        name="Conoce el método AmbLeMa",
        devName="coordinatorKnowAmblemaMethod",
        tag="2",
        sort=1,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="Si aún no está familiarizado con el método AmbLeMa, le invitamos a consultar el documento adjunto (dossier), donde encontrará respuestas claras a las preguntas fundamentales: <strong>¿Qué es AmbLeMa?, ¿en qué consiste? y ¿cuál es su propósito?</strong> Este material describe de manera precisa el método, su estructura y su alcance dentro de las escuelas, lo que le permitirá comprender cómo funciona la Herramienta Socio Educativa y el impacto que genera en la calidad educativa.",
        file={"name": "Metodo_AmbLeMa.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    coordinatorKnowAmblemaMethod.save()

    coordinatorProfile = Step(
        name="Perfil del Coordinador AmbLeMa",
        devName="coordinatorProfile",
        tag="2",
        sort=2,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="El Coordinador AmbLeMa es una persona proactiva y con un alto sentido de responsabilidad, encargada de supervisar y evaluar en cada escuela la aplicación de la Herramienta Socio Educativa. Para desempeñarse este rol, debe cumplir con los requisitos establecidos y ser aprobado por la Fundación AmbLeMa.<br><br>Para conocer con mayor detalle el <strong>rol y las competencias</strong> que debe tener un <strong>Coordinador AmbLeMa</strong>, descarga el documento adjunto.<br><br>.",
        file={"name": "Perfil_Coordinador.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    coordinatorProfile.save()

    coordinatorSendCurriculum = Step(
        name="Enviar Síntesis Curricular en formato PDF",
        devName="coordinatorSendCurriculum",
        tag="2",
        sort=3,
        isStandard=True,
        approvalType="3",
        hasUpload=True,
        hasText=True,
        text="Adjunta tu currículum vitae actualizado en formato PDF. Una vez realizado este paso, mantente atento(a), ya que el Gerente General de AmbLeMa se comunicará contigo para <strong>realizar la entrevista</strong> correspondiente. Después de esta etapa, se te informarán las siguientes fases del proceso de aceptación y formación como Coordinador AmbLeMa.",
        schoolYear=schoolYear
    )
    coordinatorSendCurriculum.save()

    corrdinatorCompleteTrainingModules = Step(
        name="Completar Módulos de Formación (AmbLePensum)",
        devName="corrdinatorCompleteTrainingModules",
        tag="2",
        sort=4,
        isStandard=True,
        hasText=True,
        approvalType="2",
        text="<strong>¡Bienvenido Fundación AmbLeMa, que comience el aprendizaje!</strong><br><br>Bienvenido al AmbLePENSUM.<br>Los Módulos de Aprendizaje muestran el Método AmbLeMa y detalla las responsabilidades del Coordinador para Hacer Que Suceda (HQS)",
        schoolYear=schoolYear
    )
    corrdinatorCompleteTrainingModules.save()

    coordinatorFindSchool = Step(
        name="Encontrar escuela",
        devName="coordinatorFindSchool",
        tag="2",
        sort=5,
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="Si deseas apoyar la expansión de la Herramienta Educativa AmbLeMa, puedes encontrar una escuela cercana que presente necesidades diversas y cuente con un equipo directivo y docente dispuesto a asumir con responsabilidad y sentido de pertenencia la aplicación y supervisión de la Herramienta Educativa AmbLeMa, con el propósito de impulsar un verdadero salto en la Calidad Educativa.",
        schoolYear=schoolYear
    )
    coordinatorFindSchool.save()

    coordinatorPresentationSchool = Step(
        name="Presentación a la escuela",
        devName="coordinatorPresentationSchool",
        tag="2",
        sort=6,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="Una vez que haya identificado una escuela con necesidades y disposición para trabajar con la Herramienta Socio Educativa AmbLeMa, solicite una reunión con el personal directivo y docente para presentarles en qué consiste la herramienta y expresar su interés en apadrinar la institución.<br><br>Para facilitar esta reunión, le recomendamos revisar el documento adjunto, que contiene un resumen claro sobre la Fundación AmbLeMa, así como el enlace al video de AmbLeMa. Estos materiales le permitirán ofrecer una explicación precisa y completa del programa.<br><br>Durante este encuentro, es fundamental que la directiva comprenda el alcance del apadrinamiento, los compromisos que implica y el <strong>acompañamiento permanente que AmbLeMa brinda a los docentes</strong>, orientado a fortalecer sus prácticas pedagógicas y promover un verdadero salto en la calidad educativa. Su rol como padrino será determinante para motivar, orientar y acompañar a la escuela en este primer acercamiento al programa.",
        file={"name": "Presentacion_Escuela.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    coordinatorPresentationSchool.save()

    coordinatorFillSchoolForm = Step(
        name="Registrar Escuela en la página web de AmbLeMa",
        devName="coordinatorFillSchoolForm",
        tag="2",
        sort=7,
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="Si la escuela está de acuerdo en asumir el compromiso, <strong>indica a su director(a)</strong> que debe ingresar a la página web de AmbLeMa (<a href=\"https://www.amblema.org\" target=\"_blank\">www.amblema.org</a>), ir a la <strong>pestaña Inicio</strong>, desplazarse hasta el final y seleccionar la opción <strong>“¿Te gustaría que AmbLeMa esté en tu escuela?”</strong> para llenar todos los datos de la institución. Este paso es indispensable para iniciar el proceso de evaluación.<br><br>Después del registro de la escuela, deben esperar la <strong>aprobación de Fundación AmbLeMa</strong> para organizar el <strong>Taller Inicial</strong> de la herramienta educativa con todo el equipo docente.",
        schoolYear=schoolYear
    )
    coordinatorFillSchoolForm.save()

    coordinatorFindSponsor = Step(
        name="Encontrar un Padrino",
        devName="coordinatorFindSponsor",
        tag="2",
        sort=8,
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="El padrino puede ser una empresa, una institución pública o privada, un particular o una familia con un auténtico sentido de responsabilidad social, dispuestos a invertir de manera efectiva la razón social de su organización para que la Herramienta Educativa AmbLeMa pueda ser aplicada en una escuela.",
        schoolYear=schoolYear
    )
    coordinatorFindSponsor.save()

    coordinatorFillSponsorForm = Step(
        name="Presentación al Padrino",
        devName="coordinatorFillSponsorForm",
        tag="2",
        sort=9,
        isStandard=True,
        approvalType="3",
        hasText=True,
        text="Contacte al posible padrino y solicite una reunión para explicarle en qué consiste la <strong>Herramienta Socio Educativa AmbLeMa</strong> y cómo, a través de su razón social, puede contribuir a que sea aplicada en la escuela, con el propósito de impulsar una educación de calidad.<br><br>Para ofrecer una explicación detallada sobre AmbLeMa, puede consultar el <strong>documento adjunto</strong>, que contiene la presentación de <em>AmbLeMa</em> y el siguiente <strong>video</strong>, materiales que le permitirán comprender de manera precisa el método y su alcance.<br><br>Si conoces una empresa o institución que pueda apadrinar una escuela, indica a su representante que debe ingresar a la página web de AmbLeMa (<a href=\"https://www.amblema.org\" target=\"_blank\">www.amblema.org</a>), ir a la <strong>pestaña Inicio</strong>, desplazarse hasta el final y seleccionar la opción <strong>“¿Te gustaría ser Padrino de una escuela?”</strong> para llenar todos los datos solicitados. Este paso es indispensable para formalizar el proceso de apadrinamiento.",
        schoolYear=schoolYear
    )
    coordinatorFillSponsorForm.save()

    initialWorkshopPlanning = Step(
        name="Planificación del Taller Inicial",
        devName="initialWorkshopPlanning",
        tag="2",
        sort=10,
        hasText=True,
        hasVideo=True,
        isStandard=True,
        approvalType="1",
        text="El Taller Inicial va dirigido al personal docente y directivo de la institución. Planifica con la Fundación AmbLeMa el día, lugar y la logística necesaria para dictar el taller. Asegura la participación de todo el personal docente de la escuela.",
        video={"name": "Video AmbLeMa", "url": "https://www.youtube.com/watch?v=0c19cCw92FY"},
        schoolYear=schoolYear
    )
    initialWorkshopPlanning.save()

    checklistInitialWorkshop = Step(
        name="Acuerdo entre Coordinador – Fundación AmbLeMa",
        devName="coordinatorInitialWorkshop",
        tag="2",
        sort=11,
        isStandard=True,
        hasText=True,
        hasFile=False,
        hasUpload=True,
        hasChecklist=False,
        text="El Acuerdo entre el Coordinador y la Fundación AmbLeMa formaliza la participación del Coordinador como voluntario y establece sus responsabilidades dentro de la escuela. Define los compromisos operativos y éticos necesarios para aplicar la Herramienta Educativa AmbLeMa. Este acuerdo se firma el día del Taller Inicial, momento en que el Coordinador confirma oficialmente su incorporación al programa. En tal sentido, se adjunta un modelo del acuerdo como referencia.",
        approvalType="3",
        schoolYear=schoolYear
    )
    checklistInitialWorkshop.save()

    # ----------------------------------------------------
    # ROL ESCUELA (School) - tag = "4"
    # ----------------------------------------------------
    schoolKnowAmblemaMethod = Step(
        name="Conoce el método AmbLeMa",
        devName="schoolKnowAmblemaMethod",
        tag="4",
        sort=1,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="Si aún no está familiarizado con el método AmbLeMa, le invitamos a consultar el documento adjunto (dossier), donde encontrará respuestas claras a las preguntas fundamentales: <strong>¿Qué es AmbLeMa?, ¿en qué consiste? y ¿cuál es su propósito?</strong> Este material describe de manera precisa el método, su estructura y su alcance dentro de las escuelas, lo que le permitirá comprender cómo funciona la Herramienta Socio Educativa y el impacto que genera en la calidad educativa.",
        file={"name": "Metodo_AmbLeMa.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    schoolKnowAmblemaMethod.save()

    schoolFindSponsor = Step(
        name="Encontrar un Padrino",
        devName="schoolFindSponsor",
        tag="4",
        sort=2,
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="El padrino puede ser una empresa, una institución pública o privada, un particular o una familia con un auténtico sentido de responsabilidad social, dispuestos a invertir de manera efectiva la razón social de su organización para que la Herramienta Educativa AmbLeMa pueda ser aplicada en una escuela.",
        schoolYear=schoolYear
    )
    schoolFindSponsor.save()

    schoolPresentationSponsor = Step(
        name="Presentación al Padrino",
        devName="schoolPresentationSponsor",
        tag="4",
        sort=3,
        isStandard=True,
        approvalType="4",
        hasText=True,
        hasFile=True,
        text="Contacte al posible padrino y solicite una reunión para explicarle en qué consiste la <strong>Herramienta Socio Educativa AmbLeMa</strong> y cómo, a través de su razón social, puede contribuir a que sea aplicada en la escuela, con el propósito de impulsar una educación de calidad.<br><br>Para ofrecer una explicación detallada sobre AmbLeMa, puede consultar el <strong>documento adjunto</strong>, que contiene la presentación de <em>AmbLeMa</em> y el siguiente <strong>video</strong>, materiales que le permitirán comprender de manera precisa el método y su alcance.<br><br>Si conoces una empresa o institución que pueda apadrinar una escuela, indica a su representante que debe ingresar a la página web de AmbLeMa (<a href=\"https://www.amblema.org\" target=\"_blank\">www.amblema.org</a>), ir a la <strong>pestaña Inicio</strong>, desplazarse hasta el final y seleccionar la opción <strong>“¿Te gustaría ser Padrino de una escuela?”</strong> para llenar todos los datos solicitados. Este paso es indispensable para formalizar el proceso de apadrinamiento.",
        file={"name": "Presentacion_Padrino.pdf", "url": "https://someurl.com/file.pdf"},
        schoolYear=schoolYear
    )
    schoolPresentationSponsor.save()

    schoolFindCoordinator = Step(
        name="Encontrar un Coordinador",
        devName="schoolFindCoordinator",
        tag="4",
        sort=4,
        hasText=True,
        isStandard=True,
        approvalType="1",
        text="El Coordinador AmbLeMa es una persona proactiva y con un alto sentido de responsabilidad, encargada de supervisar y evaluar en cada escuela la aplicación de la Herramienta Socio Educativa. Para desempeñarse este rol, debe cumplir con los requisitos establecidos y ser aprobado por la Fundación AmbLeMa.<br><br>Para conocer con mayor detalle el <strong>rol y las competencias</strong> que debe tener un <strong>Coordinador AmbLeMa</strong>, descarga el documento adjunto.<br><br>Si conoces a una persona que reúna el perfil de un Coordinador AmbLeMa, pídele que ingrese a la página web de AmbLeMa (<a href=\"https://www.amblema.org\" target=\"_blank\">www.amblema.org</a>), vaya a la <strong>pestaña Inicio</strong>, se desplace hasta el final y seleccione la opción <strong>“¿Te gustaría ser Coordinador AmbLeMa?”</strong>. Allí deberá llenar todos los datos solicitados.",
        schoolYear=schoolYear
    )
    schoolFindCoordinator.save()

    schoolAgreementSponsor = Step(
        name="Convenio Padrino - Escuela",
        devName="schoolAgreementSponsor",
        tag="4",
        sort=5,
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=False,
        hasUpload=True,
        text="Para formalizar la relación entre el <strong>Padrino y la Escuela</strong>, se procede a elaborar un <strong>convenio</strong> mediante el cual se establecen los compromisos de ambas partes y se notifica a la Fundación AmbLeMa del acuerdo alcanzado. Este documento, <strong>que será firmado el día del Taller Inicial</strong>, es indispensable para autorizar la aplicación de la Herramienta Socio Educativa en la institución. En tal sentido, se adjunta un modelo de convenio como referencia.",
        schoolYear=schoolYear
    )
    schoolAgreementSponsor.save()

    schoolAgreementFoundation = Step(
        name="Convenio Escuela - Fundación",
        devName="schoolAgreementFoundation",
        tag="4",
        sort=6,
        isStandard=True,
        approvalType="3",
        hasText=True,
        hasFile=False,
        hasUpload=True,
        text="Para formalizar la relación entre <strong>la Escuela y Fundación AmbLeMa</strong>, se procede a elaborar un <strong>convenio</strong> mediante el cual se establecen los compromisos de ambas partes, <strong>que será firmado el día del Taller Inicial</strong>, indispensable para autorizar la aplicación de la Herramienta Socio Educativa en la institución. En tal sentido, se adjunta un modelo de convenio como referencia.",
        schoolYear=schoolYear
    )
    schoolAgreementFoundation.save()

    from app.models.project_model import StepControl, CheckElement, Approval, Project
    from app.schemas.school_user_schema import SchoolUserSchema
    from app.schemas.coordinator_user_schema import CoordinatorUserSchema
    from app.schemas.sponsor_user_schema import SponsorUserSchema

    all_new_steps = Step.objects(schoolYear=schoolYear.id, isDeleted=False, status="1").order_by('tag', 'sort').all()
    projects = Project.objects(schoolYear=schoolYear.id, isDeleted=False).all()
    for project in projects:
        new_step_controls = []
        for step in all_new_steps:
            stepCtrl = StepControl(
                id=str(step.id),
                name=step.name,
                devName=step.devName,
                tag=step.tag,
                sort=step.sort,
                approvalType=step.approvalType,
                hasText=step.hasText,
                hasFile=step.hasFile,
                hasDate=step.hasDate,
                hasVideo=step.hasVideo,
                hasChecklist=step.hasChecklist,
                hasUpload=step.hasUpload,
                text=step.text,
                file=step.file,
                video=step.video,
                createdAt=step.createdAt,
                updatedAt=step.updatedAt
            )
            if step.hasChecklist:
                for check in step.checklist:
                    stepCtrl.checklist.append(
                        CheckElement(name=check.name, id=check.id))
            if project.school:
                if step.devName in ("findSchool", "coordinatorFillSchoolForm", "sponsorFillSchoolForm"):
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data=SchoolUserSchema().dump(project.school),
                            status="2"
                        )
                    )
            if project.sponsor:
                if step.devName in ("findSponsor", "coordinatorFillSponsorForm", "schoolFillSponsorForm"):
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data=SponsorUserSchema().dump(project.sponsor),
                            status="2"
                        )
                    )
            if project.coordinator:
                if step.devName in ("findCoordinator", "sponsorFindCoordinator", "schoolFindCoordinator"):
                    stepCtrl.status = "3"
                    stepCtrl.approvalHistory.append(
                        Approval(
                            id="",
                            data=CoordinatorUserSchema().dump(project.coordinator),
                            status="2"
                        )
                    )
            new_step_controls.append(stepCtrl)

        project.stepsProgress.steps = new_step_controls
        project.stepsProgress.updateProgress()
        project.save()

    return "ok"

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
        else:
            role.permissions = []
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
                        sort=action.sort,
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
