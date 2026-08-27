# app/helpers/handler_emails.py

from flask import current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import smtplib
import ssl
import requests
import base64
import json


def send_email(body, plainTextBody, subject, to):
    """
    Main email entry point. Defaults to Gmail API REST, falls back to SMTP.
    """
    res = send_email_gmail(body, plainTextBody, subject, to)
    if res == True:
        return True

    if current_app.config.get('DISABLE_SMTP_FALLBACK', False):
        current_app.logger.error("Gmail API failed and SMTP fallback is disabled.")
        return res

    current_app.logger.info("Gmail API unavailable or token invalid, trying SMTP fallback...")
    return send_email_smtp(body, plainTextBody, subject, to)


def send_email_gmail(body, plainTextBody, subject, to):
    """
    Sends email using Gmail API REST
    Params:  
    -  body: string html
    -  plainTextBody: string 
    -  subject: string
    -  to: string list separated by ',' 
    """
    client_id = current_app.config.get('GMAIL_CLIENT_ID')
    client_secret = current_app.config.get('GMAIL_CLIENT_SECRET')
    refresh_token = current_app.config.get('GMAIL_REFRESH_TOKEN')
    from_email = current_app.config.get('GMAIL_FROM')
    from_name = current_app.config.get('GMAIL_FROM_NAME')

    if not client_id or not client_secret or not refresh_token:
        missing = []
        if not client_id: missing.append("GMAIL_CLIENT_ID")
        if not client_secret: missing.append("GMAIL_CLIENT_SECRET")
        if not refresh_token: missing.append("GMAIL_REFRESH_TOKEN")
        error_msg = "Faltan variables de entorno de Gmail: " + ", ".join(missing)
        current_app.logger.error(error_msg)
        return {'msg': error_msg}, 400

    # 1. Refresh access token
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    try:
        r = requests.post(token_url, data=payload, timeout=10)
        if r.status_code != 200:
            current_app.logger.error("Gmail API Token Error: " + str(r.text))
            return {'msg': 'Error al refrescar el token de Gmail (GMAIL_REFRESH_TOKEN inválido o expirado)', 'error': r.text}, 400
        
        access_token = r.json().get('access_token')
        
        # 2. Build the email message
        msg = MIMEMultipart("alternative")
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((from_name, from_email))
        msg['To'] = to
        
        partPlain = MIMEText(plainTextBody, "plain", "utf-8")
        partHtml = MIMEText(body, "html", "utf-8")
        msg.attach(partPlain)
        msg.attach(partHtml)
        
        # 3. Base64 encode the message
        msg_str = msg.as_string()
        if isinstance(msg_str, str) and hasattr(msg_str, 'encode'):
            msg_bytes = msg_str.encode('utf-8')
        else:
            msg_bytes = msg_str
            
        raw_bytes = base64.urlsafe_b64encode(msg_bytes)
        
        if hasattr(raw_bytes, 'decode'):
            raw_message = raw_bytes.decode('utf-8')
        else:
            raw_message = raw_bytes
        
        # 4. Send the message
        send_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            'Authorization': 'Bearer {0}'.format(access_token),
            'Content-Type': 'application/json'
        }
        send_payload = {'raw': raw_message}
        
        r_send = requests.post(send_url, headers=headers, json=send_payload, timeout=15)
        
        if r_send.status_code == 200:
            current_app.logger.info("Email sent successfully to {0} via Gmail API".format(to))
            return True
        else:
            current_app.logger.error("Gmail API Send Error: " + str(r_send.text))
            return {'msg': 'Error al enviar el correo via Gmail API', 'error': r_send.text}, 400
            
    except Exception as e:
        current_app.logger.error("Gmail API Exception: " + str(e))
        return {'msg': str(e), 'to': str(to)}, 400


def send_email_smtp(body, plainTextBody, subject, to):
    """
    SMTP fallback method for sending email.
    """
    SMTP_USERNAME = current_app.config.get('SMTP_USERNAME')
    SMTP_PASSWORD = current_app.config.get('SMTP_PASSWORD')
    SMTP_FROM = current_app.config.get('SMTP_FROM')
    SMTP_HOST = current_app.config.get('SMTP_HOST') or 'smtp.gmail.com'
    SMTP_PORT = int(current_app.config.get('SMTP_PORT') or 587)
    from_name = current_app.config.get('GMAIL_FROM_NAME') or 'AmbLeMa'

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return {'msg': 'SMTP credenciales no configuradas'}, 400

    msg = MIMEMultipart("alternative")
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr((from_name, SMTP_FROM))
    msg['To'] = to

    partPlain = MIMEText(plainTextBody, "plain", "utf-8")
    partHtml = MIMEText(body, "html", "utf-8")
    msg.attach(partPlain)
    msg.attach(partHtml)

    try:
        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=5) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [t.strip() for t in to.split(',')], msg.as_string())
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
                server.starttls(context=context)
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [t.strip() for t in to.split(',')], msg.as_string())
        current_app.logger.info("Email sent successfully to {0} via SMTP".format(to))
        return True
    except Exception as e:
        current_app.logger.error("SMTP Exception: " + str(e))
        return {'msg': str(e), 'to': str(to)}, 400
