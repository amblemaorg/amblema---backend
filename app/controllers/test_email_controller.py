from flask import request
from flask_restful import Resource
from app.helpers.handler_emails import send_email

class TestEmailController(Resource):
    def post(self):
        jsonData = request.get_json()
        to = jsonData.get('to')
        subject = jsonData.get('subject', 'Prueba de correo AmbLeMa')
        body = jsonData.get('body', '<h1>Este es un correo de prueba</h1>')
        plainTextBody = jsonData.get('plainTextBody', 'Este es un correo de prueba')
        
        if not to:
            return {'msg': 'Destinatario (to) es requerido'}, 400
            
        result = send_email(body, plainTextBody, subject, to)
        if result == True:
            return {'msg': 'Correo enviado exitosamente'}, 200
        else:
            return result
