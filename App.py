from tkinter import Tk, Label, Scale, Button, Text

import matplotlib.pyplot as plt
from PIL import ImageTk, Image, ImageDraw, ImageOps
import numpy as np
import time

from Radon import Radon

from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian
import pydicom._storage_sopclass_uids

from skimage.util import img_as_ubyte
from skimage.exposure import rescale_intensity


class App:

    def __init__(self):
        self.startRotation = 0
        self.numberOfEmitters = 10
        self.emittersAngularSpan = 90
        self.rotationDelta = 5

        self.maxImageDisplayWidth = 400
        self.maxImageDisplayHeight = 600

        self.window = Tk()
        self.window.title('computed tomography scan simulator')
        self.window.geometry('1500x1000')

        self.baseImage = Image.open('example_images/Shepp_logan.jpg')

        # save original image size
        self.originalImage = self.baseImage
        self.imgWidth = self.baseImage.width
        self.imgHeight = self.baseImage.height

        self.img = ImageTk.PhotoImage(self.resizeToFitLimits(self.baseImage))
        self.imgLabel = Label(self.window, image=self.img)
        self.imgLabel.grid(column=0, row=0, columnspan=2)

        # place for sinogram
        self.sinogram = Image.open('example_images/blank.png')
        self.sinImg = ImageTk.PhotoImage(self.resizeToFitLimits(self.sinogram))
        self.sinImgLabel = Label(self.window, image=self.sinImg)
        self.sinImgLabel.grid(column=2, row=0, columnspan=2)

        # place for reconstructed image
        self.recImage = Image.open('example_images/blank.png')
        self.recImg = ImageTk.PhotoImage(self.resizeToFitLimits(self.recImage))
        self.recImgLabel = Label(self.window, image=self.recImg)
        self.recImgLabel.grid(column=4, row=0, columnspan=2)

        # Sliders
        startRotationSlider = Scale(self.window, from_=0, to=360, orient='horizontal', label='początkowa rotacja',
                                    command=self.changeRotation)
        startRotationSlider.set(self.startRotation)
        spanSlider = Scale(self.window, from_=0, to=180, orient='horizontal', label='angular span',
                           command=self.changeEmittersAngularSpan)
        spanSlider.set(self.emittersAngularSpan)
        countSlider = Scale(self.window, from_=0, to=400, orient='horizontal', label='ilość emiterów',
                            command=self.changeNumberOfEmitters)
        countSlider.set(self.numberOfEmitters)
        rotationDeltaSlider = Scale(self.window, from_=0, to=90, orient='horizontal', label='Δα',
                                    command=self.changeRotationDelta)
        rotationDeltaSlider.set(self.rotationDelta)

        # Button to create sinogram and reconstr
        applyParamsButton = Button(self.window, text="zastosuj i resetuj sinogram", command=self.applyParams)

        # Textboxes - nie maja sprawdzania poprawnosci ani nic
        namelabel = Label(self.window, text = "Patient Name")
        self.nametxt = Text(self.window,height=1,width=10)

        idlabel = Label(self.window, text="Patient ID")
        self.idtxt = Text(self.window, height=1, width=10)

        datelabel = Label(self.window, text="Study Date") # powinna byc w formacie YYYYMMDD (ze same liczby po prostu), inaczej wywala warning, ale i tak sie zapisuje
        self.datetxt = Text(self.window, height=1, width=10)

        commentlabel = Label(self.window, text="Comments")
        self.commenttxt = Text(self.window, height=2, width=20)

        # przycisk do zapisu dicom - pojawia sie po wygenerowaniu sinogramu (po wywolaniu self.applyParams)
        self.createDicomButton = Button(self.window, text="stwórz dicom", command=self.createDicom)

        startRotationSlider.grid(column=0, row=1)
        spanSlider.grid(column=1, row=1)
        countSlider.grid(column=2, row=1)
        rotationDeltaSlider.grid(column=0, row=2)

        namelabel.grid(column=0,row=4)
        self.nametxt.grid(column=0, row=5)
        idlabel.grid(column=0, row=6)
        self.idtxt.grid(column=0, row=7)
        datelabel.grid(column=0, row=8)
        self.datetxt.grid(column=0, row=9)
        commentlabel.grid(column=0, row=10)
        self.commenttxt.grid(column=0, row=11)



        applyParamsButton.grid(column=1, row=3)

        self.radonTransformator = Radon(self.baseImage)

        self.window.mainloop()

    def resizeToFitLimits(self, image):
        newShape = (0, 0)
        if image.size[0] > image.size[1]:
            newShape = (self.maxImageDisplayHeight, int(self.maxImageDisplayHeight * (image.size[1] / image.size[0])))
        else:
            newShape = (int(self.maxImageDisplayWidth * (image.size[0] / image.size[1])), self.maxImageDisplayWidth)

        return image.resize(newShape, resample=Image.BICUBIC)

    def loadImage(self, filepath):
        self.baseImage = Image.open(filepath)
        self.img = ImageTk.PhotoImage(self.resizeToFitLimits(self.baseImage))
        self.imgLabel.config(image=self.img)

    def setImage(self, image):
        self.img = ImageTk.PhotoImage(self.resizeToFitLimits(image))
        self.imgLabel.config(image=self.img)

    def showSinogram(self, sinogram):
        self.sinImg = ImageTk.PhotoImage(self.resizeToFitLimits(sinogram))
        self.sinImgLabel.config(image=self.sinImg)

    def showReconstruction(self, reconstruction):
        self.recImg = ImageTk.PhotoImage(self.resizeToFitLimits(reconstruction))
        self.recImgLabel.config(image=self.recImg)

    def changeRotation(self, event):
        self.startRotation = int(event)

    def changeNumberOfEmitters(self, event):
        self.numberOfEmitters = int(event)

    def changeEmittersAngularSpan(self, event):
        self.emittersAngularSpan = int(event)

    def changeIteration(self, event):
        self.currentIteration = int(event)

    def changeRotationDelta(self, event):
        self.rotationDelta = int(event)

    def applyParams(self):
        self.radonTransformator.configAndReset(startRotation=np.radians(self.startRotation),
                                               numberOfEmitters=self.numberOfEmitters,
                                               emittersAngularSpan=np.radians(self.emittersAngularSpan),
                                               rotationDelta=np.radians(self.rotationDelta))
        self.radonTransformator.generateSinogram()
        self.showSinogram(self.radonTransformator.getSinogram())
        self.radonTransformator.generateReconstruction(from_iteration=0)  # rekonstrukcja obrazu
        self.showReconstruction(self.radonTransformator.getReconstruction())

        self.createDicomButton.grid(column=0, row=12) # pokaz przycisk do zapisu dicom

    # def nextIteration(self):
    #     self.radonTransformator.nextIteration()

    def createDicom(self):
        patient_data = {}
        patient_data['PatientName'] = self.nametxt.get("1.0", 'end-1c') # czytaj od: 1 - pierwsza linia, 0 - pierwszy znak, -1c usun \n na koncu
        patient_data['PatientID'] = self.idtxt.get("1.0", 'end-1c')
        patient_data['StudyDate'] = self.datetxt.get("1.0", 'end-1c')
        patient_data['ImageComments'] = self.commenttxt.get("1.0", 'end-1c')
        self.save_as_dicom('test.dcm', self.radonTransformator.getReconstruction(),patient_data)

    def read_dicom(self, file_name):
        # load dicom file
        ds = pydicom.dcmread(file_name)

        print("DICOM info")
        print("Patient Name:", ds.PatientName)
        print("Patient ID:", ds.PatientID)
        print("Study date:", ds.StudyDate)
        print("Image comments:", ds.ImageComments)
        print("Modality:", ds.Modality)
        print("Image size:", ds.Rows, "x", ds.Columns)

    def save_as_dicom(self, file_name, img, patient_data): # funkcja z ekursy

        img_converted = np.array(img.convert('L'))

        # Populate required values for file meta information
        meta = Dataset()
        meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
        meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        ds = FileDataset(None, {}, preamble=b"\0" * 128)
        ds.file_meta = meta

        ds.is_little_endian = True
        ds.is_implicit_VR = False

        ds.SOPClassUID = pydicom._storage_sopclass_uids.CTImageStorage
        ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID

        ds.PatientName = patient_data["PatientName"]
        ds.PatientID = patient_data["PatientID"]
        ds.StudyDate = patient_data["StudyDate"]
        ds.ImageComments = patient_data["ImageComments"]

        ds.Modality = "CT"
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.StudyInstanceUID = pydicom.uid.generate_uid()
        ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

        ds.BitsStored = 8
        ds.BitsAllocated = 8
        ds.SamplesPerPixel = 1
        ds.HighBit = 15

        ds.ImagesInAcquisition = 1
        ds.InstanceNumber = 1

        ds.Rows, ds.Columns = img_converted.shape[:2]

        ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelRepresentation = 0

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)

        ds.PixelData = img_converted.tobytes()

        ds.save_as(file_name, write_like_original=False)

        self.read_dicom(file_name)



