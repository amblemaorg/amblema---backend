# app/services/environmental_diagnostic_service.py

import os
import uuid
from datetime import datetime
from flask import current_app

from app.models.environmental_diagnostic_model import EnvironmentalDiagnosticEvaluator
from app.models.peca_project_model import PecaProject
from app.helpers.error_helpers import RegisterNotFound
from app.helpers.handler_emails import send_email


class EnvironmentalDiagnosticService():

    def _get_origin(self, web_origin=None, req=None):
        if web_origin:
            return web_origin.rstrip('/')
        if req:
            origin = req.headers.get('Origin')
            if origin:
                return origin.rstrip('/')
            referer = req.headers.get('Referer')
            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                if parsed.scheme and parsed.netloc:
                    return "{}://{}".format(parsed.scheme, parsed.netloc)
            proto = req.headers.get('X-Forwarded-Proto', req.scheme)
            host = req.headers.get('X-Forwarded-Host', req.host)
            if host:
                return "{}://{}".format(proto, host).rstrip('/')
        env_url = os.getenv('WEB_URL')
        if env_url:
            return env_url.rstrip('/')
        if req and hasattr(req, 'host_url'):
            return req.host_url.rstrip('/')
        return 'http://localhost:4200'

    def register_evaluator(self, pecaId, lapse, jsonData, web_origin=None, req=None):
        peca = PecaProject.objects(id=pecaId, isDeleted=False).first()
        if not peca:
            raise RegisterNotFound(message="Peca project not found", status_code=404, payload={"pecaId": pecaId})

        name = jsonData.get('name')
        email = jsonData.get('email')
        phone = jsonData.get('phone')

        if not name or not email or not phone:
            return {"message": "Nombre, correo y teléfono son obligatorios"}, 400

        email = email.strip().lower()

        existing = EnvironmentalDiagnosticEvaluator.objects(
            pecaId=str(pecaId),
            lapse=str(lapse),
            email=email,
            isDeleted=False
        ).first()

        if existing:
            return {"message": "Ya existe un evaluador registrado con este correo electrónico para este lapso."}, 400

        token = uuid.uuid4().hex

        evaluator = EnvironmentalDiagnosticEvaluator(
            pecaId=str(pecaId),
            lapse=str(lapse),
            name=name,
            email=email,
            phone=phone,
            token=token,
            hasEvaluated=False,
            results={}
        )
        evaluator.save()

        base_url = self._get_origin(web_origin, req)
        link = "{}/evaluacion-ambiente/{}".format(base_url, token)

        school_name = peca.school.name if peca.school else "Escuela"
        subject = "Evaluación de Diagnóstico de Ambiente - Fundación Amblema"
        body = """
        <div style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
            <h2 style="color: #81B03E;">Evaluación de Diagnóstico Ambiental</h2>
            <p>Estimado/a <strong>{name}</strong>,</p>
            <p>Ha sido registrado/a como evaluador/a para el diagnóstico ambiental de la escuela <strong>{school_name}</strong> para el <strong>Lapso {lapse}</strong>.</p>
            <p>Por favor ingrese al siguiente enlace para completar la evaluación de los criterios correspondientes:</p>
            <p style="margin: 25px 0;">
                <a href="{link}" style="background-color: #81B03E; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                    Realizar Evaluación
                </a>
            </p>
            <p>O copie y pegue la siguiente dirección en su navegador:</p>
            <p><a href="{link}">{link}</a></p>
            <p style="color: #666; font-size: 0.9em;"><em>Nota: Este enlace es de un solo uso. Una vez enviada la evaluación no se podrá modificar.</em></p>
            <br>
            <p>Atentamente,</p>
            <p><strong>Fundación Amblema</strong></p>
        </div>
        """.format(name=name, school_name=school_name, lapse=lapse, link=link)
        plainTextBody = "Hola {}, has sido registrado/a como evaluador/a para el diagnóstico ambiental de la escuela {} (Lapso {}). Ingresa al siguiente enlace para evaluar: {}".format(name, school_name, lapse, link)

        try:
            send_email(body, plainTextBody, subject, email)
        except Exception as e:
            if hasattr(current_app, 'logger'):
                current_app.logger.error("Error sending email to evaluator {}: {}".format(email, str(e)))

        return {
            "id": str(evaluator.id),
            "name": evaluator.name,
            "email": evaluator.email,
            "phone": evaluator.phone,
            "token": evaluator.token,
            "link": link,
            "hasEvaluated": evaluator.hasEvaluated,
            "results": evaluator.results,
            "index": evaluator.index,
            "createdAt": evaluator.createdAt.isoformat() if evaluator.createdAt else None
        }, 201

    def get_evaluators(self, pecaId, lapse, web_origin=None, req=None):
        peca = PecaProject.objects(id=pecaId, isDeleted=False).first()
        if not peca:
            raise RegisterNotFound(message="Peca project not found", status_code=404, payload={"pecaId": pecaId})

        base_url = self._get_origin(web_origin, req)

        evaluators = EnvironmentalDiagnosticEvaluator.objects(pecaId=str(pecaId), lapse=str(lapse), isDeleted=False)
        result_list = []
        for ev in evaluators:
            link = "{}/evaluacion-ambiente/{}".format(base_url, ev.token)
            result_list.append({
                "id": str(ev.id),
                "name": ev.name,
                "email": ev.email,
                "phone": ev.phone,
                "token": ev.token,
                "link": link,
                "hasEvaluated": ev.hasEvaluated,
                "results": ev.results,
                "index": ev.index,
                "createdAt": ev.createdAt.isoformat() if ev.createdAt else None,
                "evaluatedAt": ev.evaluatedAt.isoformat() if ev.evaluatedAt else None
            })
        return {"evaluators": result_list}, 200

    def get_evaluation(self, token):
        evaluator = EnvironmentalDiagnosticEvaluator.objects(token=token, isDeleted=False).first()
        if not evaluator:
            return {"message": "Enlace de evaluación no encontrado o inválido"}, 404

        peca = PecaProject.objects(id=evaluator.pecaId, isDeleted=False).first()
        school_info = {}
        if peca and peca.school:
            school_info = {
                "name": peca.school.name if hasattr(peca.school, 'name') else "",
                "code": peca.school.code if hasattr(peca.school, 'code') else "",
                "address": peca.school.address if hasattr(peca.school, 'address') else ""
            }

        return {
            "evaluator": {
                "name": evaluator.name,
                "email": evaluator.email,
                "phone": evaluator.phone,
                "hasEvaluated": evaluator.hasEvaluated,
                "results": evaluator.results,
                "index": evaluator.index,
                "lapse": evaluator.lapse
            },
            "school": school_info
        }, 200

    def submit_evaluation(self, token, jsonData):
        evaluator = EnvironmentalDiagnosticEvaluator.objects(token=token, isDeleted=False).first()
        if not evaluator:
            return {"message": "Evaluación no encontrada"}, 404

        if evaluator.hasEvaluated:
            return {"message": "Los resultados para este evaluador ya han sido registrados.", "hasEvaluated": True}, 400

        indicator_definitions = {
            'cleanlinessAndCareOfSpaces': {
                'subcriteria': ['1.1', '1.2', '1.3'],
                'count': 3
            },
            'wasteManagement': {
                'subcriteria': ['2.1', '2.2', '2.3'],
                'count': 3
            },
            'biodiversityConservation': {
                'subcriteria': ['3.1', '3.2', '3.3'],
                'count': 3
            },
            'waterUse': {
                'subcriteria': ['4.1', '4.2', '4.3'],
                'count': 3
            },
            'communityRelations': {
                'subcriteria': ['5.1', '5.2'],
                'count': 2
            }
        }

        results_input = jsonData.get('results', {})
        processed_results = {}
        indicator_averages = []

        for key, defs in indicator_definitions.items():
            indicator_input = results_input.get(key, {})
            subcriteria_data = {}
            subtotal = 0.0

            if isinstance(indicator_input, dict) and 'subcriteria' in indicator_input:
                sub_input = indicator_input.get('subcriteria', {})
                applied_count = 0
                for sub_key in defs['subcriteria']:
                    sub_item = sub_input.get(sub_key, {})
                    val = sub_item.get('value', 0) if isinstance(sub_item, dict) else sub_item
                    try:
                        val_float = max(0.0, min(7.0, float(val)))
                    except (ValueError, TypeError):
                        val_float = 0.0
                    obs = sub_item.get('observation', '') if isinstance(sub_item, dict) else ''
                    applies = val_float > 0
                    subcriteria_data[sub_key] = {
                        'value': val_float,
                        'observation': obs,
                        'applies': applies
                    }
                    if applies:
                        subtotal += val_float
                        applied_count += 1
                avg = round(subtotal / applied_count, 2) if applied_count > 0 else 0.0
                processed_results[key] = {
                    'applies': applied_count > 0,
                    'value': avg,
                    'subtotal': round(subtotal, 2),
                    'average': avg,
                    'subcriteria': subcriteria_data
                }
                indicator_averages.append(avg)
            elif isinstance(indicator_input, dict) and 'value' in indicator_input:
                val = indicator_input.get('value')
                applies = bool(indicator_input.get('applies', True))
                if applies and val is not None and val != '':
                    try:
                        val_float = max(0.0, min(7.0, float(val)))
                    except (ValueError, TypeError):
                        val_float = 0.0
                else:
                    val_float = 0.0
                processed_results[key] = {
                    'applies': applies,
                    'value': val_float,
                    'subtotal': round(val_float * defs['count'], 2),
                    'average': val_float,
                    'subcriteria': {}
                }
                indicator_averages.append(val_float)
            else:
                processed_results[key] = {
                    'applies': False,
                    'value': 0.0,
                    'subtotal': 0.0,
                    'average': 0.0,
                    'subcriteria': {}
                }
                indicator_averages.append(0.0)

        total_index = round(sum(indicator_averages), 2)

        evaluator.results = processed_results
        evaluator.index = total_index
        evaluator.hasEvaluated = True
        evaluator.evaluatedAt = datetime.utcnow()
        evaluator.save()

        return {
            "message": "Resultados registrados exitosamente.",
            "evaluator": {
                "hasEvaluated": True,
                "index": evaluator.index,
                "results": evaluator.results
            }
        }, 200

    def delete_evaluator(self, pecaId, lapse, evaluatorId):
        peca = PecaProject.objects(id=pecaId, isDeleted=False).first()
        if not peca:
            raise RegisterNotFound(message="Peca project not found", status_code=404, payload={"pecaId": pecaId})

        evaluator = EnvironmentalDiagnosticEvaluator.objects(
            id=evaluatorId, pecaId=str(pecaId), lapse=str(lapse), isDeleted=False
        ).first()
        if not evaluator:
            raise RegisterNotFound(message="Evaluator not found", status_code=404, payload={"evaluatorId": evaluatorId})

        if evaluator.hasEvaluated:
            return {"message": "No se puede eliminar un evaluador que ya ha realizado la evaluación."}, 400

        evaluator.isDeleted = True
        evaluator.save()
        return {"message": "Evaluador eliminado exitosamente"}, 200
