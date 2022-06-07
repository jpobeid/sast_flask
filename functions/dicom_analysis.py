import os
import numpy as np
import pydicom as pyd
from PIL import Image
import base64

import global_vars as var
from models import db, SeriesModel

def verify_series(user_email, path_user_input):
    for i, e in enumerate(os.listdir(path_user_input)):
        dcm = pyd.dcmread(os.path.join(path_user_input, e),
                            stop_before_pixels=True)
        if dcm.Modality != 'CT':
            # Any non-CT will return an error
            return {'success': False, 'message': 'Only CT scans can be accepted'}, 406
        elif i == 0:
            # First file uploaded, assign values to Series db entry
            series = SeriesModel.query.filter_by(
                user=user_email).first()
            series.patient_id, series.accession_number, series.series_number = dcm.PatientID, dcm.AccessionNumber, dcm.SeriesNumber
            db.session.commit()
        else:
            # Subsequent files must match the Series entry, return error if not
            series = SeriesModel.query.filter_by(
                user=user_email).first()
            is_different_id = str(
                series.patient_id) != str(dcm.PatientID)
            is_different_accession = str(
                series.accession_number) != str(dcm.AccessionNumber)
            is_different_series = str(
                series.series_number) != str(dcm.SeriesNumber)
            if is_different_id or is_different_accession or is_different_series:
                return {'success': False, 'message': 'Multiple studies or series present'}, 406
    # If no error has returned, then verification is successful
    return var.json_success, 200

def get_random_image_base64text(path_user_input):
    n_images = len(os.listdir(path_user_input))
    i_image = np.random.randint(n_images)
    dcm = pyd.dcmread(os.path.join(path_user_input, os.listdir(path_user_input)[i_image]))
    m_pre = dcm.pixel_array
    m_norm = (m_pre - np.min(m_pre))/(np.max(m_pre) - np.min(m_pre))
    m_post = (m_norm * 255).astype(np.uint8)
    img = Image.fromarray(m_post)
    img.save('temp_pic.jpg', format='JPEG')
    with open('temp_pic.jpg', 'rb') as f:
        code = base64.b64encode(f.read())
    os.remove('temp_pic.jpg')
    return code.decode('utf8')
