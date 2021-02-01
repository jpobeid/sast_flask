import os
import json
import smtplib
from email.message import EmailMessage

PASS_VAR = json.loads(os.environ.get('PASS_VAR'))
EMAIL_ADDRESS = PASS_VAR['email']['user']
EMAIL_PASSWORD = PASS_VAR['email']['pass']


def send_email(to_address, token, attachment):
    msg = EmailMessage()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_address
    if token:
        msg['Subject'] = 'SAST Registration Verification'
        msg.set_content(f'This is your 6-digit verification token {token}')
    elif attachment:
        msg['Subject'] = 'SAST Output RT-Struct'
        msg.set_content(f'This is the output RT-Struct DICOM file')
        with open(attachment, 'rb') as f:
            data = f.read()
            msg.add_attachment(data, maintype='application',
                               subtype='dcm', filename='output.dcm')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
