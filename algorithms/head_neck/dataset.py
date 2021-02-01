import torch
from torch.utils.data import Dataset
import numpy as np


class EDataset(Dataset):
    def __init__(self, ImageData):
        self.img_data = ImageData

    def __getitem__(self, index):
        start_idx = index*(self.img_data.shape[0]//19)
        end_idx = (index+1)*(self.img_data.shape[0]//19)
        if index==19:
            end_idx = self.img_data.shape[0]
        img_x = self.img_data[start_idx:end_idx, :, :, :]
        img_x = np.transpose(img_x, (0, 3, 1, 2))
        img_x = torch.from_numpy(img_x)
        return img_x[:, 0:1, :, :].float(), img_x[:, 1:2, :, :].float(), img_x[:, 2:3, :, :].float()

    def __len__(self):
        return 20
