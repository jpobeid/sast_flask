import os
import json
import smtplib
from email.message import EmailMessage

PASS_VAR = json.loads(os.environ.get('PASS_VAR'))
EMAIL_ADDRESS = PASS_VAR['email']['user']
EMAIL_PASSWORD = PASS_VAR['email']['pass']

def send_email(to_address, token):
    msg = EmailMessage()
    msg['Subject'] = 'SAST Registration Verification'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_address
    msg.set_content(f'This is your 6-digit verification token {token}')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)