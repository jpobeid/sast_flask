import os
import numpy as np
import pydicom as pyd
from PIL import Image
import base64

import global_vars as var


class DicomImage():
    def __init__(self):
        self.n_total = len(os.listdir(var.path_upload_dir_full))

    @staticmethod
    def get_random_image_base64text():
        dir_main = os.getcwd()
        os.chdir(var.path_upload_dir_full)
        n_total = len(os.listdir())
        index_image = np.random.randint(n_total)
        d = pyd.dcmread(os.listdir()[index_image])
        m_pre = d.pixel_array
        norm_m = (m_pre - np.min(m_pre))/(np.max(m_pre) - np.min(m_pre))
        m_post = (norm_m * 255).astype(np.uint8)
        img = Image.fromarray(m_post)
        os.chdir(dir_main)
        img.save('temp_pic.jpg', format='JPEG')
        with open('temp_pic.jpg', 'rb') as f:
            code = base64.b64encode(f.read())
        os.remove('temp_pic.jpg')
        return code.decode('utf8')
