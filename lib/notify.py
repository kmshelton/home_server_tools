#!/usr/bin/python3
"""Module for sending mail via gmail."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def mail(gmail_username, app_password, email_subject, email_body):
    """Send mail via gmail."""
    msg = MIMEMultipart('alternative')
    user = gmail_username + '@gmail.com'
    msg['Subject'] = email_subject
    msg['From'] = msg['To'] = user

    msg.attach(MIMEText(email_body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(user, app_password)
        server.sendmail(user, user, msg.as_string())
