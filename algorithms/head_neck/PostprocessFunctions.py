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
from pydicom.dataset import Dataset
#from PIL import Image
from skimage import measure

import re
numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

def GetSubfolderName(folderdir):
    name=[]
    for filename in sorted(glob.glob(folderdir+'/*'), key=numericalSort):
        name+=[folderdir+'/'+filename.split('\\')[-1]]
    return name

 
def WriteContourData(rawdatadir, patientid, predArray, templatedir, savename):
    file_dir = GetSubfolderName(rawdatadir + patientid)
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
    ArrayDicom = ArrayDicom.astype("float") * onedcm.RescaleSlope + onedcm.RescaleIntercept

    img_th = np.where(ArrayDicom > -160, 1, 0).astype(int)
    conn_img = measure.label(img_th, connectivity=1)
    conn_properties = measure.regionprops(conn_img)
    conn_vlm = 0
    for conn_prop in conn_properties:
        if conn_prop.area > conn_vlm:
            conn_vlm = conn_prop.area
            minx, miny, minz, maxx, maxy, maxz = np.array(conn_prop.bbox)

    crop_size = [192, 352, maxz - minz]
    new_size = np.array(OrigPixelDims[0:2]) * (np.array(crop_size[0:2]) / np.array([maxx - minx, maxy - miny]))
    new_size = np.ceil([new_size[0], new_size[1], OrigPixelDims[2]]).astype(np.int)
    minx = np.floor(minx * new_size[0] / OrigPixelDims[0])
    miny = np.floor(miny * new_size[1] / OrigPixelDims[1])
    crop_begin = np.array([minx, miny, minz]).astype(np.int)

    dcm0 = GetAllDcmDataNameUnderADirectory(templatedir)
    savedata = pydicom.dcmread(dcm0[0])
       
    savedata.AccessionNumber= onedcm.AccessionNumber
#    savedata.StudyDescription= onedcm.StudyDescription
    savedata.PatientName= onedcm.PatientName
    savedata.PatientID= onedcm.PatientID
    savedata.StudyInstanceUID= onedcm.StudyInstanceUID
    savedata.StudyID = onedcm.StudyID
    savedata.ReferringPhysicianName = onedcm.ReferringPhysicianName
    savedata.PatientBirthDate= onedcm.PatientBirthDate
    savedata.PatientSex = onedcm.PatientSex

    savedata.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID = onedcm.FrameOfReferenceUID
    savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPInstanceUID = onedcm.StudyInstanceUID
    savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID = onedcm.SeriesInstanceUID
    if len(savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence)>len(CTUID):
        del savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[len(CTUID):]
    if len(savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence)<len(CTUID):
        savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence += [Dataset() for i in range(len(CTUID)-len(savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence))]
    classUID = savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[0].ReferencedSOPClassUID       
    for index in range(len(savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence)):
        savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[index].ReferencedSOPClassUID = classUID	
        savedata.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[index].ReferencedSOPInstanceUID = CTUID[index]
    
    for i in range(0, len(savedata.StructureSetROISequence)):
        savedata.StructureSetROISequence[i].ReferencedFrameOfReferenceUID = onedcm.FrameOfReferenceUID

    if len(savedata.ROIContourSequence[0].ContourSequence)>len(CTUID):
        for i in range(0, len(savedata.StructureSetROISequence)):
            del savedata.ROIContourSequence[i].ContourSequence[len(CTUID):]

    if len(savedata.ROIContourSequence[0].ContourSequence)<len(CTUID):
        for i in range(0, len(savedata.StructureSetROISequence)):
            norg = len(savedata.ROIContourSequence[i].ContourSequence)
            savedata.ROIContourSequence[i].ContourSequence += [Dataset() for i in range(len(CTUID)-norg)]
            for j in range(norg, len(CTUID)):
                savedata.ROIContourSequence[i].ContourSequence[j].ContourImageSequence = [Dataset()]

    for sequenceIndex in range(len(CTUID)):
        zp = zpositionlist[sequenceIndex]
        if(sequenceIndex >= crop_begin[2]+1) and (sequenceIndex < crop_begin[2]+crop_size[2]-1):
            mask = np.zeros((crop_size[0], crop_size[1], 16))
            mask = predArray[sequenceIndex-crop_begin[2]-1, :,:,:]    #!!!!!!Should agree with the data processing
            mask = mask[:,:, [1,2,0,3,4,5,6,7,8,9,10,11,12,13,14,15]]
            for organ_idx in range (0, 16):
                if mask[:,:, organ_idx].max()>=1:
                     SaveContour(mask[:,:, organ_idx], zp, savedata.ROIContourSequence[organ_idx], sequenceIndex, OrigPixelDims, OrigPosition, OrigPixelSpacing, new_size, crop_size, crop_begin, CTUID[sequenceIndex], classUID)
                else:
                     savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].NumberOfContourPoints = 0
                     savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourData = []
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourGeometricType = 'CLOSED_PLANAR'
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourImageSequence[0].ReferencedSOPInstanceUID = CTUID[sequenceIndex]
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourImageSequence[0].ReferencedSOPClassUID = classUID
        else:
            for organ_idx in range(0, 16):
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].NumberOfContourPoints = 0
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourData = []
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourGeometricType = 'CLOSED_PLANAR'
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourImageSequence[0].ReferencedSOPInstanceUID = CTUID[sequenceIndex]
                savedata.ROIContourSequence[organ_idx].ContourSequence[sequenceIndex].ContourImageSequence[0].ReferencedSOPClassUID = classUID

    savedata.save_as(savename)
    print('Contour has been saved to '+savename)    

#######################   private   ######################
def GetAllDcmDataNameUnderADirectory(directory):
    filenamelist=[]
    for dirpath, dirnames, filenames in os.walk(directory): # get all the directory and files including subfolders
        for filename in [f for f in filenames if f.endswith('.dcm')]:
            filenamelist+=[os.path.join(dirpath, filename)] # get the whole directory of all DICOM files in this directory
    return filenamelist


def SaveContour(mask, zp, contourslice, sequenceIndex, OrigPixelDims, OrigPosition, OrigPixelSpacing, new_size, crop_size, crop_begin, UIDCT, UIDClass):
    extentmask = np.zeros((new_size[0], new_size[1]))
    extentmask[crop_begin[0]:crop_begin[0]+crop_size[0], crop_begin[1]:crop_begin[1]+crop_size[1]] = mask
    dicommask = np.zeros((OrigPixelDims[0], OrigPixelDims[1]))
    try:
        dicommask = resize(extentmask, (OrigPixelDims[0], OrigPixelDims[1]), order=0, preserve_range=True, anti_aliasing=False)
    except:
        print('Problem with resampling mask:' + sequenceIndex)
    dicommask = np.where(dicommask > 0.5, 1, 0)
    cvmask = np.array(dicommask, dtype=np.uint8)
    contours, hierarchy = cv2.findContours(cvmask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    contourdata =  np.reshape(contours[0], (-1, 2))
    if contourdata.shape[0] >= 10:
        contourdata[:, 0] = contourdata[:, 0] * OrigPixelSpacing[1] + OrigPosition[1]
        contourdata[:, 1] = contourdata[:, 1] * OrigPixelSpacing[0] + OrigPosition[0]
        maskdata = np.zeros((contourdata.shape[0], 3))
        maskdata[:, 0:2] = contourdata
        maskdata[:, 2] = zp
        contourslice.ContourSequence[sequenceIndex].NumberOfContourPoints = maskdata.shape[0]
        contourslice.ContourSequence[sequenceIndex].ContourData = maskdata.flatten().tolist()

    else:
        contourslice.ContourSequence[sequenceIndex].NumberOfContourPoints = 0
        contourslice.ContourSequence[sequenceIndex].ContourData = []
    if np.array(contours).shape[0]>1:
        for i in range(1, np.array(contours).shape[0]):
            if np.reshape(contours[i], (-1, 2)).shape[0] >= 10:
                contourslice.ContourSequence += [Dataset()]
                contourslice.ContourSequence[-1].ContourImageSequence = [Dataset()]
                contourdata = np.reshape(contours[i], (-1, 2))
                contourdata[:, 0] = contourdata[:, 0] * OrigPixelSpacing[1] + OrigPosition[1]
                contourdata[:, 1] = contourdata[:, 1] * OrigPixelSpacing[0] + OrigPosition[0]
                maskdata = np.zeros((contourdata.shape[0], 3))
                maskdata[:, 0:2] = contourdata
                maskdata[:, 2] = zp
                contourslice.ContourSequence[-1].NumberOfContourPoints = maskdata.shape[0]
                contourslice.ContourSequence[-1].ContourData = maskdata.flatten().tolist()
                contourslice.ContourSequence[-1].ContourGeometricType = 'CLOSED_PLANAR'
                contourslice.ContourSequence[-1].ContourImageSequence[0].ReferencedSOPInstanceUID = UIDCT
                contourslice.ContourSequence[-1].ContourImageSequence[0].ReferencedSOPClassUID = UIDClass

