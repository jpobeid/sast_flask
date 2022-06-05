import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = 'stanfordxrtresidents@gmail.com'
EMAIL_PASSWORD = 'Qu4dsh0t'

### Need to fix this, now that gmail disabled less secure access!!!

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
