# -*- coding: utf-8 -*-
# app/services/yearbook_order_service.py

from app.models.school_year_model import SchoolYear
from app.models.peca_project_model import PecaProject
from app.models.peca_setting_model import YearbookOrder, YearbookOrderItem


# Bloques de diagnóstico (gráficos) en el orden por defecto en que se muestran hoy
DIAGNOSTIC_ITEMS = [
    ('diagnosticEnvironmental', u'Gráfica de IAA (diagnóstico de ambiente)'),
    ('diagnosticReading', u'Gráfico de lectura'),
    ('diagnosticMath', u'Gráfico de multiplicación'),
    ('diagnosticLogic', u'Gráfico de lógica matemática'),
]

# (campo en pecaSetting.lapseN, id con el que la actividad sale en yearbook.lapseN.activities, nombre)
# annualPreparation no se incluye porque no forma parte del AmbLeMario
STANDARD_ACTIVITIES = [
    ('initialWorkshop', 'initialWorkshop', u'Taller inicial'),
    ('ambleCoins', 'ambleCoins', u'AmbLeMonedas'),
    ('lapsePlanning', 'lapsePlanning', u'Planificación de lapso'),
    ('annualConvention', 'annualConvention', u'Convención anual'),
    ('mathOlympic', 'olympics', u'Olimpíada Recreativas de Matemática'),
    ('readingOlympics', 'readingolympics', u'Olimpíada Recreativas de Lengua'),
    ('specialLapseActivity', 'specialActivity', u'Actividad especial de lapso'),
]

# (campo en PecaProject.lapseN, id en yearbook.lapseN.activities); espejo de PecaProjectService.getYearbookData
PECA_STANDARD_ACTIVITIES = [
    ('initialWorkshop', 'initialWorkshop'),
    ('ambleCoins', 'ambleCoins'),
    ('lapsePlanning', 'lapsePlanning'),
    ('annualConvention', 'annualConvention'),
    ('olympics', 'olympics'),
    ('readingOlympics', 'readingolympics'),
    ('specialActivity', 'specialActivity'),
]

LAPSES = ('1', '2', '3')


class YearbookOrderService():

    def _getActivities(self, settingLapse):
        activities = []
        for field, key, name in STANDARD_ACTIVITIES:
            standard = getattr(settingLapse, field, None)
            if standard and standard.status == "1":
                activities.append({'key': key, 'name': name, 'menuOrder': standard.order})
        for activity in settingLapse.activities.filter(isDeleted=False):
            if activity.status == "1":
                activities.append({'key': str(activity.id), 'name': activity.name, 'menuOrder': activity.order})
        return sorted(activities, key=lambda a: a['menuOrder'])

    def _getPecaActivities(self, pecaLapse):
        activities = []
        for field, key in PECA_STANDARD_ACTIVITIES:
            standard = getattr(pecaLapse, field, None)
            if standard:
                activities.append({'key': key, 'menuOrder': standard.order})
        for activity in pecaLapse.activities:
            if activity.status == "1" or activity.status == "3":
                activities.append({'key': str(activity.id), 'menuOrder': activity.order})
        return sorted(activities, key=lambda a: a['menuOrder'])

    def resolveLapse(self, pecaSetting, lapse):
        """
        Devuelve los items del lapso ordenados para el AmbLeMario.
        Sin configuración: diagnósticos primero y luego actividades por el order del menú.
        Con configuración: el order guardado; lo no configurado (p. ej. actividades nuevas)
        conserva su posición relativa por defecto y va después de lo configurado.
        """
        settingLapse = pecaSetting['lapse{}'.format(lapse)]
        items = [{'key': key, 'name': name, 'type': 'graphic'} for key, name in DIAGNOSTIC_ITEMS]
        if settingLapse:
            items += [{'key': a['key'], 'name': a['name'], 'type': 'activity'}
                      for a in self._getActivities(settingLapse)]
        return self._applySavedOrder(items, pecaSetting, lapse)

    def _applySavedOrder(self, items, pecaSetting, lapse):
        saved = {}
        yearbookOrder = pecaSetting.yearbookOrder if pecaSetting else None
        if yearbookOrder and yearbookOrder['lapse{}'.format(lapse)]:
            saved = dict((item.key, item.order) for item in yearbookOrder['lapse{}'.format(lapse)])

        maxSaved = max(saved.values()) if saved else 0
        for idx, item in enumerate(items):
            item['isCustom'] = item['key'] in saved
            item['sortKey'] = (saved[item['key']], idx) if item['isCustom'] else (maxSaved + 1, idx)

        items = sorted(items, key=lambda i: i['sortKey'])
        for position, item in enumerate(items):
            item['order'] = position + 1
            del item['sortKey']
        return items

    def getSetting(self):
        try:
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            if not schoolYear:
                return {'status': 0, 'message': u'No hay un año escolar activo'}, 404
            records = {}
            for lapse in LAPSES:
                records['lapse{}'.format(lapse)] = self.resolveLapse(schoolYear.pecaSetting, lapse)
            return records, 200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

    def saveSetting(self, lapse, jsonData):
        try:
            if lapse not in LAPSES:
                return {'status': 0, 'message': u'Lapso inválido'}, 400
            schoolYear = SchoolYear.objects(isDeleted=False, status="1").first()
            if not schoolYear:
                return {'status': 0, 'message': u'No hay un año escolar activo'}, 404

            items = (jsonData or {}).get('items')
            if not isinstance(items, list):
                return {'status': 0, 'message': u'Debe enviar la lista de items'}, 400

            validKeys = set(i['key'] for i in self.resolveLapse(schoolYear.pecaSetting, lapse))
            orderItems = []
            seen = set()
            for item in items:
                key = item.get('key') if isinstance(item, dict) else None
                order = item.get('order') if isinstance(item, dict) else None
                if key not in validKeys or key in seen:
                    return {'status': 0, 'message': u'Item inválido o repetido: {}'.format(key)}, 400
                try:
                    order = int(order)
                except (TypeError, ValueError):
                    return {'status': 0, 'message': u'Orden inválido para: {}'.format(key)}, 400
                if order < 0:
                    return {'status': 0, 'message': u'El orden no puede ser negativo'}, 400
                seen.add(key)
                orderItems.append(YearbookOrderItem(key=key, order=order))

            # Lista vacía = volver al orden por defecto
            if not schoolYear.pecaSetting.yearbookOrder:
                schoolYear.pecaSetting.yearbookOrder = YearbookOrder()
            schoolYear.pecaSetting.yearbookOrder['lapse{}'.format(lapse)] = orderItems
            schoolYear.save()

            return {'lapse{}'.format(lapse): self.resolveLapse(schoolYear.pecaSetting, lapse)}, 200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400

    def getPecaOrder(self, pecaId):
        """
        Orden (solo keys) para el AmbLeMario web y PDF de un PECA de cualquier año escolar.
        Las actividades salen del propio PECA (no del ajuste del año, que puede cambiar al cerrar
        el año) y el orden guardado es el del año escolar al que pertenece el PECA.
        """
        try:
            peca = PecaProject.objects(isDeleted=False, id=pecaId).only(
                'schoolYear', 'lapse1', 'lapse2', 'lapse3').first()
            if not peca:
                return {'status': 0, 'message': u'No se encontró el proyecto'}, 404
            schoolYear = SchoolYear.objects(id=peca.schoolYear.id).only('pecaSetting').first()
            pecaSetting = schoolYear.pecaSetting if schoolYear else None
            records = {}
            for lapse in LAPSES:
                pecaLapse = peca['lapse{}'.format(lapse)]
                items = [{'key': key} for key, name in DIAGNOSTIC_ITEMS]
                if pecaLapse:
                    items += [{'key': a['key']} for a in self._getPecaActivities(pecaLapse)]
                records['lapse{}'.format(lapse)] = [
                    item['key'] for item in self._applySavedOrder(items, pecaSetting, lapse)]
            return records, 200
        except Exception as e:
            return {'status': 0, 'message': str(e)}, 400
