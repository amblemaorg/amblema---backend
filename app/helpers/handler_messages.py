
class HandlerMessages():
    entities_labels = {
        'ActivityPeca': 'Actividades Genéricas',
        'ActivitiesSlider': 'Slider de actividades',
        'AmblecoinsPeca':   'AmbLeMonedas',
        'AnnualConventionPeca': 'Convención anual',
        'AnnualPreparationPeca': 'Preparación anual',
        'InitialWorkshopPeca': 'Taller Inicial',
        'LapsePlanningPeca': 'Planificación de lapso',
        'OlympicsPeca': 'Olimpíadas',
        'SchoolPeca': 'Escuela',
        'Teacher': 'Docente',
        'TeacherTestimonial': 'Testimonios de docentes',
        'Section': 'Sección',
        'Student': 'Estudiante',
        'Yearbook': 'Anuario',
        'SpecialActivity': 'Actividad Especial de lapso',
        'AdminUser': 'Usuario Administrador',
        'CoordinatorUser': 'Usuario Coordinador',
        'SchoolUser': 'Usuario Escuela',
        'SponsorUser': 'Usuario Padrino',
        'EnvironmentalProject': 'Proyecto Ambiental',
        'MonitoringActivity': 'Estrategias de seguimiento de actividades',
        'GoalSetting': 'Metas',
        'LearningModule': 'Módulo de aprendizaje',
        'Project': 'Proyecto',
        'PecaProject': 'PECA',
        'RequestContentApproval': 'Solicitud de aprobación de contenido',
        'RequestFindUser': 'Solicitud de creación de usuario',
        'RequestCreateProject': 'Solicitud de creación de proyectos',
        'RequestProjectApproval': 'Solicitud de confirmación de proyectos',
        'Role': 'Roles',
        'SchoolYear': 'Período escolar',
        'Municipality': 'Municipio',
        'Step': 'Paso previo',
        'Activities': 'Actividades genéricas',
        'Report': 'Reportes',
        'Web': 'Web'
    }

    def getEntityLabel(self, entity):
        return self.entities_labels[entity]

    def getDeleteEntityMsg(self, entity):
        return 'Error al eliminar. El registro está relacionado con {}'.format(self.getEntityLabel(entity))
