# app/helpers/handler_emails.py

from flask import current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import smtplib
import ssl


def send_email(body, plainTextBody, subject, to):
    """
    Params:  
    -  body: string html
    -  plainTextBody: string 
    -  subject: string
    -  to: string list separated by ',' 
    """

    SMTP_USERNAME = current_app.config.get('SMTP_USERNAME')
    SMTP_PASSWORD = current_app.config.get('SMTP_PASSWORD')
    SMTP_FROM = current_app.config.get('SMTP_FROM')
    SMTP_HOST = current_app.config.get('SMTP_HOST')
    SMTP_PORT = current_app.config.get('SMTP_PORT')
    
    msg = MIMEMultipart("alternative")
    to = to
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = SMTP_FROM
    msg['To'] = to
    text = plainTextBody
    html = body

    partPlain = MIMEText(text, "plain")
    part = MIMEText(html, "html")
    msg.attach(partPlain)
    msg.attach(part)
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(
                SMTP_FROM, to, msg.as_string()
            )
            return True
        
        """with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            print("entro al with")
            server.ehlo()  # Identificarse con el servidor
            print("elo session")
            server.starttls(context=context)  # Iniciar cifrado TLS
            print("starttls")
            server.ehlo()  # Re-identificarse después de TLS
            print("ehlo()")
            # Iniciar sesión con credenciales de Gmail
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("login smtp")
            # Enviar correo
            server.sendmail(SMTP_FROM, to.split(','), msg.as_string())
            print("sendemail")
            
            return True"""
    except Exception as e:
        return {'msg': str(e), 'to': str(to.split())}, 400
