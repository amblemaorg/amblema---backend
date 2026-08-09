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

    def register_evaluator(self, pecaId, lapse, jsonData, web_origin=None):
        peca = PecaProject.objects(id=pecaId, isDeleted=False).first()
        if not peca:
            raise RegisterNotFound(message="Peca project not found", status_code=404, payload={"pecaId": pecaId})

        name = jsonData.get('name')
        email = jsonData.get('email')
        phone = jsonData.get('phone')

        if not name or not email or not phone:
            return {"message": "Nombre, correo y teléfono son obligatorios"}, 400

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

        base_url = web_origin if web_origin else os.getenv('WEB_URL', 'http://localhost:4200')
        # Ensure base_url doesn't end with a trailing slash
        base_url = base_url.rstrip('/')
        link = f"{base_url}/evaluacion-ambiente/{token}"

        school_name = peca.school.name if peca.school else "Escuela"
        subject = "Evaluación de Diagnóstico de Ambiente - Fundación Amblema"
        body = f"""
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
        """
        plainTextBody = f"Hola {name}, has sido registrado/a como evaluador/a para el diagnóstico ambiental de la escuela {school_name} (Lapso {lapse}). Ingresa al siguiente enlace para evaluar: {link}"

        try:
            send_email(body, plainTextBody, subject, email)
        except Exception as e:
            if hasattr(current_app, 'logger'):
                current_app.logger.error(f"Error sending email to evaluator {email}: {str(e)}")

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

    def get_evaluators(self, pecaId, lapse, web_origin=None):
        peca = PecaProject.objects(id=pecaId, isDeleted=False).first()
        if not peca:
            raise RegisterNotFound(message="Peca project not found", status_code=404, payload={"pecaId": pecaId})

        base_url = web_origin if web_origin else os.getenv('WEB_URL', 'http://localhost:4200')
        base_url = base_url.rstrip('/')

        evaluators = EnvironmentalDiagnosticEvaluator.objects(pecaId=str(pecaId), lapse=str(lapse), isDeleted=False)
        result_list = []
        for ev in evaluators:
            link = f"{base_url}/evaluacion-ambiente/{ev.token}"
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

        criteria_keys = [
            'cleanlinessAndCareOfSpaces',
            'wasteManagement',
            'biodiversityConservation',
            'waterUse',
            'communityRelations'
        ]

        results_input = jsonData.get('results', {})
        valid_values = []
        processed_results = {}

        for key in criteria_keys:
            item = results_input.get(key, {'applies': False, 'value': None})
            applies = bool(item.get('applies', False))
            val = item.get('value')

            if applies and val is not None and val != '':
                try:
                    val_float = float(val)
                    val_float = max(0.0, min(7.0, val_float))
                    valid_values.append(val_float)
                    processed_results[key] = {'applies': True, 'value': val_float}
                except (ValueError, TypeError):
                    processed_results[key] = {'applies': True, 'value': 0.0}
                    valid_values.append(0.0)
            else:
                processed_results[key] = {'applies': False, 'value': None}

        index_val = (sum(valid_values) / len(valid_values)) if valid_values else None

        evaluator.results = processed_results
        evaluator.index = round(index_val, 2) if index_val is not None else None
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
