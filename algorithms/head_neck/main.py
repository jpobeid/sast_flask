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

Inputdata_dir = 'InputData/'
Model_path = 'MBUnet_1.pth'
Template_dir = 'TemplateRT/'
Contour_path = 'OutputData/ContouredByAI.dcm'
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def AutoSeg(ImageData, model_path):
    model = MBUnet(1, 17)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.to(device)
    test_dataset = EDataset(ImageData)
    dataloaders = DataLoader(test_dataset, batch_size=1, shuffle=False)
    model.eval()
    with torch.no_grad():
        SegResult = np.empty(shape=[0, 192, 352, 16])
        for x1, x2, x3 in dataloaders:
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
    return SegResult


def main():
    os.chdir(r'algorithms\head_neck')
    added = os.listdir(Inputdata_dir)
    if len(added) == 1:
        print("Start processing case:", ", ".join(added))
        time.sleep(1)

        ImageData, PatientName = ReadCTData(Inputdata_dir)
        print('Pre-processed CT image data size:', ImageData.shape)

        SegResult = AutoSeg(ImageData, Model_path)
        print('Segmentation results sizes:', SegResult.shape)

        WriteContourData(Inputdata_dir, PatientName,
                         SegResult, Template_dir, Contour_path)
        print('Segmentation of case: ' + PatientName + ' has been completed!')
        shutil.rmtree(Inputdata_dir + "/" + added[0] + "/")

        os.chdir(r'OutputData')
