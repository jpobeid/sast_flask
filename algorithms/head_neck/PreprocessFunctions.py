import glob
import numpy as np
import os
import os.path
import pydicom
import pickle
from matplotlib import pyplot, cm   
from pathlib import Path
#import SimpleITK as sitk
from skimage import data, color
from skimage.transform import rescale, resize, downscale_local_mean
import cv2
#from PIL import Image
import skimage.io as io
import copy
from skimage import measure


import re
numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

def GetPatientNameAndId(datadir):
    patientname=[]
    for filename in sorted(glob.glob(datadir+'*'), key=numericalSort):# read all files in this directory
        patientname+=[filename.split('\\')[-1]]  #extract only the name after the last'/' in the whole directory
    patientid=[k+1 for k in range(len(patientname))]  # if there is no name list, the ID is 1, 2, 3...
    return np.array(patientid+patientname).reshape(2,-1).T  #return ID and name list, n*2

def GetSubfolderName(folderdir):
    name=[]
    for filename in sorted(glob.glob(folderdir+'/*'), key=numericalSort):
        name+=[folderdir+'/'+filename.split('\\')[-1]]
    return name

 
def ReadCTData(rawdatadir):
    patientnameid = GetPatientNameAndId(rawdatadir)
    file_dir = GetSubfolderName(rawdatadir + patientnameid[0, 1])
    imagelist = []
    for file in file_dir:
        if ("CT" in str(file)):
            imagelist += [file]

    onedcm = pydicom.dcmread(imagelist[0])
    OrigPosition = (float(onedcm.ImagePositionPatient[1]), float(onedcm.ImagePositionPatient[0]))
    OrigPixelDims = (int(onedcm.Rows), int(onedcm.Columns), len(imagelist))
    if ('SpacingBetweenSlices' in onedcm.dir()):
        zspace = onedcm.SpacingBetweenSlices
    else:
        zspace = onedcm.SliceThickness
    OrigPixelSpacing = (float(onedcm.PixelSpacing[1]), float(onedcm.PixelSpacing[0]), float(zspace))
    ArrayDicom = np.zeros((OrigPixelDims[0], OrigPixelDims[1], OrigPixelDims[2]), dtype=onedcm.pixel_array.dtype)
    CTUID = [None for i in range(len(imagelist))]
    zpositionlist = np.zeros((OrigPixelDims[2]))

    InstanceData = []
    for img_dir in imagelist:
        dataset = pydicom.dcmread(img_dir)
        if InstanceData is None:
            InstanceData = [int(dataset.InstanceNumber)]
        else:
            if int(dataset.InstanceNumber) in InstanceData:
                print(dataset.InstanceNumber, 'Duplicate Instance number!!!!!!')
            else:
                InstanceData += [int(dataset.InstanceNumber)]
    InstanceData.sort()
    for i in range(len(InstanceData) - 1):
        if (InstanceData[i + 1] - InstanceData[i]) != 1:
            print('Instance number is not consecutive!!!!!!')

    for img_dir in imagelist:
        dataset = pydicom.dcmread(img_dir)
        InstanceNo = int(dataset.InstanceNumber)
        ArrayDicom[:, :, InstanceData.index(InstanceNo)] = dataset.pixel_array
        zpositionlist[InstanceData.index(InstanceNo)] = float(dataset.ImagePositionPatient[2])
        CTUID[InstanceData.index(InstanceNo)] = str(dataset.SOPInstanceUID)
    ArrayDicom = ArrayDicom.astype("float")* onedcm.RescaleSlope + onedcm.RescaleIntercept

    img_th = np.where(ArrayDicom > -160, 1, 0).astype(int)
    conn_img = measure.label(img_th, connectivity=1)
    conn_properties = measure.regionprops(conn_img)
    conn_vlm = 0
    for conn_prop in conn_properties:
        if conn_prop.area > conn_vlm:
            conn_vlm = conn_prop.area
            minx, miny, minz, maxx, maxy, maxz = np.array(conn_prop.bbox)

    crop_size = [192, 352, maxz-minz]
    new_size = np.array(OrigPixelDims[0:2]) * (np.array(crop_size[0:2]) / np.array([maxx-minx, maxy-miny]))
    new_size = np.ceil([new_size[0], new_size[1], OrigPixelDims[2]]).astype(np.int)
    ArrayCrop = np.zeros((crop_size[0], crop_size[1], crop_size[2]), dtype='float32')
    minx = np.floor(minx* new_size[0]/OrigPixelDims[0])
    miny = np.floor(miny* new_size[1]/OrigPixelDims[1])
    crop_begin = np.array([minx, miny, minz]).astype(np.int)
    try:
        image_resized = resize(ArrayDicom, new_size, preserve_range=True)
    except:
        print('Problem with resampling image.')

    MIN_BOUND = -160.0
    MAX_BOUND = 240.0
    MID_BOUND = 40.0
    image_resized = 2 * (image_resized - MID_BOUND) / (MAX_BOUND - MIN_BOUND)
    image_resized[image_resized > 1] = 1.
    image_resized[image_resized < -1] = -1.
    ArrayCrop = image_resized[crop_begin[0]:crop_begin[0]+crop_size[0], crop_begin[1]:crop_begin[1]+crop_size[1], crop_begin[2]:crop_begin[2]+crop_size[2]]
    ArrayCrop = ArrayCrop.transpose(2, 0, 1)

    ImportArray = np.zeros((crop_size[2]-2, crop_size[0], crop_size[1], 3))
    ImportArray[:, :, :, 0] = ArrayCrop[1:-1, :, :]
    ImportArray[:, :, :, 1] = ArrayCrop[:-2, :, :]
    ImportArray[:, :, :, 2] = ArrayCrop[2:, :, :]

    return ImportArray, patientnameid[0, 1]

#######################   private   ######################       
def GetAllDcmDataNameUnderADirectory(directory):
    filenamelist=[]
    for dirpath, dirnames, filenames in os.walk(directory): # get all the directory and files including subfolders
        for filename in [f for f in filenames if f.endswith('.dcm')]:
            filenamelist+=[os.path.join(dirpath, filename)] # get the whole directory of all DICOM files in this directory
    return filenamelist

def ArrayNormalization(std_array, image_array):
    array_float = np.array(image_array, dtype=np.float)
    std_float = np.array(std_array, dtype=np.float)
    mean = np.mean(std_float)
    std = np.std(std_float)
#    print(mean, std)
    image_standardized = (array_float - mean) / std
    return image_standardized

def ReadContour(OrigPixelDims, ContourData, CTUID, OrigPosition, OrigPixelSpacing, new_size, crop_size, crop_begin):
    ProstateDicom = np.zeros((OrigPixelDims[0], OrigPixelDims[1], OrigPixelDims[2]))
    for sequenceIndex in range(len(ContourData.ContourSequence)):
        RefUID = ContourData.ContourSequence[sequenceIndex].ContourImageSequence[0].ReferencedSOPInstanceUID
        index_CT = CTUID.index(RefUID)

        contour_data = np.array(ContourData.ContourSequence[sequenceIndex].ContourData).reshape((-1, 3))
        rows = contour_data[:, 1]
        rows = ((rows - OrigPosition[0]) / OrigPixelSpacing[0])
        rows = rows.astype(int)
        cols = contour_data[:, 0]
        cols = ((cols - OrigPosition[1]) / OrigPixelSpacing[1])
        cols = cols.astype(int)
        arr = np.zeros((OrigPixelDims[0], OrigPixelDims[1]))
        poly = np.zeros((len(rows), 2)).astype(int)
        poly[:, 0] = cols
        poly[:, 1] = rows
        contour_array = arr
        cv2.fillPoly(contour_array, pts=[poly], color=1)
        ProstateDicom[:, :, index_CT] += contour_array
    ProstateDicom[ProstateDicom>1] = 1
    try:
        image_resized = resize(ProstateDicom, (new_size[0], new_size[1], new_size[2]), order=0, preserve_range=True, anti_aliasing=False)
    except:
        print('Problem with resampling contour.')
    Arraymask = np.zeros((crop_size[0], crop_size[1], crop_size[2]))
    Arraymask = image_resized[crop_begin[0]:crop_begin[0]+crop_size[0], crop_begin[1]:crop_begin[1]+crop_size[1], crop_begin[2]:crop_begin[2]+crop_size[2]]
    Arraymask = np.where(Arraymask > 0.5, 1, 0)

    return Arraymask.transpose(2, 0, 1)
        
        


