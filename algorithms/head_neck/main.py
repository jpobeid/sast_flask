import os
import time
import torch

from torch.utils.data import DataLoader
from algorithms.head_neck.mbunet import MBUnet
from algorithms.head_neck.dataset import EDataset
import numpy as np
from algorithms.head_neck.PreprocessFunctions import ReadCTData
from algorithms.head_neck.PostprocessFunctions import WriteContourData
import shutil
import global_vars as var

Model_path = os.path.join('algorithms', var.name_dir_head_neck, 'MBUnet_1.pth')
Template_dir = os.path.join(
    'algorithms', var.name_dir_head_neck, 'TemplateRT/')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def AutoSeg(ImageData, model_path):
    model = MBUnet(1, 17)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.to(device)
    test_dataset = EDataset(ImageData)
    dataloaders = DataLoader(test_dataset, batch_size=1, shuffle=False)
    L_dataloaders = len(dataloaders)
    model.eval()
    with torch.no_grad():
        SegResult = np.empty(shape=[0, 192, 352, 16])
        for j, (x1, x2, x3) in enumerate(dataloaders):
            x1 = torch.squeeze(x1, 0)
            x2 = torch.squeeze(x2, 0)
            x3 = torch.squeeze(x3, 0)
            x1 = x1.to(device)
            x2 = x2.to(device)
            x3 = x3.to(device)
            y, dsy1, dsy2, dsy3, dsy4 = model(x1, x2, x3)
            y = y.to("cpu")
            y_pred = y.numpy()
            e_output = np.zeros(
                (y_pred.shape[0], 16, y_pred.shape[2], y_pred.shape[3]))
            for i in range(16):
                esuboutput = np.zeros(
                    (y_pred.shape[0], y_pred.shape[2], y_pred.shape[3]))
                esuboutput[np.argmax(y_pred, axis=1) == i] = 1.0
                e_output[:, i, :, :] = esuboutput
            SegResult = np.append(
                SegResult, e_output.transpose(0, 2, 3, 1), axis=0)
            print(str(np.round(100*(j+1)/L_dataloaders)) + r'% complete...')
    return SegResult


def main(str_email):
    Inputdata_dir = var.name_dir_input + '/'
    if str_email not in os.listdir(var.name_dir_output):
        os.mkdir(os.path.join(var.name_dir_output, str_email))
    Outputdata_dir = os.path.join(var.name_dir_output, str_email, var.name_output_file)
    dir_process = [str_email]
    if len(dir_process) == 1:
        print("Start processing case:", ", ".join(dir_process))
        time.sleep(1)

        ImageData, PatientName = ReadCTData(Inputdata_dir)
        print('Pre-processed CT image data size:', ImageData.shape)

        SegResult = AutoSeg(ImageData, Model_path)
        print('Segmentation results sizes:', SegResult.shape)

        WriteContourData(Inputdata_dir, PatientName,
                         SegResult, Template_dir, Outputdata_dir)
        print('Segmentation of case: ' + PatientName + ' has been completed!')
        shutil.rmtree(Inputdata_dir + "/" + dir_process[0] + "/")
