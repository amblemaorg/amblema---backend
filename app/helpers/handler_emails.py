# app/helpers/handler_emails.py

from flask import current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from smtplib import SMTP


def send_email(body, subject, to):
    """
    Params:  
    -  body: string html
    -  subject: string
    -  to: string list separated by ',' 
    """

    SMTP_USERNAME = current_app.config.get('SMTP_USERNAME')
    SMTP_PASSWORD = current_app.config.get('SMTP_PASSWORD')
    SMTP_FROM = current_app.config.get('SMTP_FROM')
    SMTP_HOST = current_app.config.get('SMTP_HOST')
    SMTP_PORT = current_app.config.get('SMTP_PORT')

    msg = MIMEMultipart()
    to = to
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = SMTP_FROM
    msg['To'] = to
    html = body
    part = MIMEText(html, 'html')
    msg.attach(part)
    try:
        server = SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(msg['From'], to.split(','), msg.as_string())
        server.close()
        return True
    except Exception as e:
        return {'msg': str(e), 'to': str(to.split())}, 400
