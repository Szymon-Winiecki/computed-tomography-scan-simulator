from tkinter import Tk, Label, Scale, Button, Text, Checkbutton, messagebox, Entry, StringVar, filedialog

from PIL import ImageTk, Image, ImageDraw, ImageOps
import numpy as np

from Radon import Radon

from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian
import pydicom._storage_sopclass_uids


class App:

    def __init__(self):

        # variables to hold computations settings
        self.startRotation = 0
        self.numberOfEmitters = 10
        self.emittersAngularSpan = 90
        self.rotationDelta = 5
        self.useFilter = True

        
        self.isRecFinished = False

        #display settings
        self.maxImageDisplayWidth = 400
        self.maxImageDisplayHeight = 600


        # window
        self.window = Tk()
        self.window.title('computed tomography scan simulator')
        self.window.geometry('1600x1000')

        # place for original image 
        self.baseImage = Image.open('example_images/Shepp_logan.jpg')
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

        # file selction
        selectFileTitleLabel = Label(self.window, text="Wybór pliku:", font='Helvetica 18 bold')
        selectFileButton = Button(self.window, text="wybierz obraz wejściowy", command=self.selectFile)
        self.selectedFileNameLabel = Label(self.window, text="nie wybrano pliku")

        # Inputs
        settingsTitleLabel = Label(self.window, text="Opcje:", font='Helvetica 18 bold')

        startRotationLabel = Label(self.window, text='początkowa rotacja')
        self.startRotationVar = StringVar()
        startRotationInput = Entry(self.window, textvariable=self.startRotationVar, validate="key")
        startRotationInput['validatecommand'] = (startRotationInput.register(self.validate_startRotationInput), '%P')
        self.startRotationVar.set(self.startRotation)

        spanLabel = Label(self.window, text='rozpiętość kątowa')
        self.spanVar = StringVar()
        spanInput = Entry(self.window, textvariable=self.spanVar, validate="key")
        spanInput['validatecommand'] = (spanInput.register(self.validate_spanInput), '%P')
        self.spanVar.set(self.emittersAngularSpan)

        countLabel = Label(self.window, text='ilość emiterów')
        self.countVar = StringVar()
        countInput = Entry(self.window, textvariable=self.countVar, validate="key")
        countInput['validatecommand'] = (countInput.register(self.validate_countInput), '%P')
        self.countVar.set(self.numberOfEmitters)

        rotationDeltaLabel = Label(self.window, text='Δα')
        self.rotationDeltaVar = StringVar()
        rotationDeltaInput = Entry(self.window, textvariable=self.rotationDeltaVar, validate="key")
        rotationDeltaInput['validatecommand'] = (rotationDeltaInput.register(self.validate_rotationDeltaInput), '%P')
        self.rotationDeltaVar.set(self.rotationDelta)

        filterCheckBox = Checkbutton(self.window, text='filtruj sinogram', onvalue=1, offvalue=0, command=self.changeFilter)
        filterCheckBox.select()

        # Button to apply settings and reset generated images
        applyParamsButton = Button(self.window, text="zastosuj i resetuj sinogram", width=25, command=self.applyParams)

        # Button to create entire sinogram and reconstruction at once
        generateButton = Button(self.window, text="Wygeneruj", width=25, command=self.generateSinogram)

        # Button to render sinogram and reconstruction iteration by iteration
        nextIterationButton = Button(self.window, text="rysuj iteracyjnie", width=25, command=self.runAnimation)

        # DICOM info inputs
        dicomTitleLabel = Label(self.window, text="Eksport do pliku DICOM:", font='Helvetica 18 bold')

        namelabel = Label(self.window, text = "Imię i nazwisko pacjenta: ")
        self.nametxt = Text(self.window,height=1,width=20)

        idlabel = Label(self.window, text="ID pacjenta")
        self.idtxt = Text(self.window, height=1, width=20)

        datelabel = Label(self.window, text="Data badania") # format: YYYYMMDD
        self.datetxt = Text(self.window, height=1, width=20)

        commentlabel = Label(self.window, text="komentarz")
        self.commenttxt = Text(self.window, height=2, width=20)

        filenamelabel = Label(self.window, text="nazwa pliku")
        self.filenametxt = Text(self.window, height=1, width=20)

        # button to save DICOM
        self.createDicomButton = Button(self.window, text="stwórz dicom", command=self.createDicom)


        # layout
        selectFileTitleLabel.grid(column=0, row = 1, sticky='W')
        selectFileButton.grid(column=1, row = 2)
        self.selectedFileNameLabel.grid(column=2, row=2)

        settingsTitleLabel.grid(column=0, row=3, sticky='W')

        startRotationLabel.grid(column=0, row=4)
        startRotationInput.grid(column=1, row=4)

        spanLabel.grid(column=0, row=5)
        spanInput.grid(column=1, row=5)

        countLabel.grid(column=0, row=6)
        countInput.grid(column=1, row=6)

        rotationDeltaLabel.grid(column=0, row=7)
        rotationDeltaInput.grid(column=1, row=7)

        filterCheckBox.grid(column=1, row=8)

        applyParamsButton.grid(column=3, row=5, sticky='W')
        generateButton.grid(column=3, row=6, sticky='W')
        nextIterationButton.grid(column=3, row=7, sticky='W')

        dicomTitleLabel.grid(column=0,row=9, sticky='W')
        namelabel.grid(column=0,row=10)
        self.nametxt.grid(column=1, row=10)
        idlabel.grid(column=0, row=11)
        self.idtxt.grid(column=1, row=11)
        datelabel.grid(column=0, row=12)
        self.datetxt.grid(column=1, row=12)
        commentlabel.grid(column=0, row=13)
        self.commenttxt.grid(column=1, row=13)
        filenamelabel.grid(column=0, row=14)
        self.filenametxt.grid(column=1, row=14)


        # create object that takes care of all CT computations
        self.radonTransformator = Radon(self.baseImage)

        self.window.mainloop()

    # returns image resized to fit in limits set in maxImageDisplayWidth and maxImageDisplayHeight variables
    def resizeToFitLimits(self, image):
        newShape = (0, 0)
        if image.size[0] > image.size[1]:
            newShape = (self.maxImageDisplayHeight, int(self.maxImageDisplayHeight * (image.size[1] / image.size[0])) + 1)
        else:
            newShape = (int(self.maxImageDisplayWidth * (image.size[0] / image.size[1])) + 1, self.maxImageDisplayWidth)

        return image.resize(newShape, resample=Image.BICUBIC)

    # display original image
    def setImage(self, image):
        self.img = ImageTk.PhotoImage(self.resizeToFitLimits(image))
        self.imgLabel.config(image=self.img)

    # display sinogram
    def showSinogram(self, sinogram):
        self.sinImg = ImageTk.PhotoImage(self.resizeToFitLimits(sinogram))
        self.sinImgLabel.config(image=self.sinImg)

    # display reconstructed image
    def showReconstruction(self, reconstruction):
        self.recImg = ImageTk.PhotoImage(self.resizeToFitLimits(reconstruction))
        self.recImgLabel.config(image=self.recImg)
    

    # event handlers

    def selectFile(self):
        filename = filedialog.askopenfilename()

        if filename != '':
            self.inputImageFile = filename
            self.selectedFileNameLabel.config(text=filename[filename.rindex('/')+1:])
            del self.radonTransformator

            self.baseImage = Image.open(filename)
            self.setImage(self.baseImage)
            self.radonTransformator = Radon(baseImage=self.baseImage)
            self.applyParams()

    def changeRotation(self, event):
        self.startRotation = int(event)

    def changeNumberOfEmitters(self, event):
        self.numberOfEmitters = int(event)

    def changeEmittersAngularSpan(self, event):
        self.emittersAngularSpan = int(event)

    def changeIteration(self, event):
        self.currentIteration = int(event)

    def changeRotationDelta(self, event):
        self.rotationDelta = float(event)

    def changeFilter(self):
        self.useFilter = not self.useFilter

    def applyParams(self):
        self.isRecFinished = False

        self.startRotation = int(self.startRotationVar.get())
        self.startRotationVar.set(self.startRotation)

        self.numberOfEmitters = int(self.countVar.get())
        self.countVar.set(self.numberOfEmitters)

        self.emittersAngularSpan = int(self.spanVar.get())
        self.spanVar.set(self.emittersAngularSpan)

        self.rotationDelta = float(self.rotationDeltaVar.get())
        self.rotationDeltaVar.set(self.rotationDelta)

        self.radonTransformator.configAndReset(startRotation=np.radians(self.startRotation),
                                               numberOfEmitters=self.numberOfEmitters,
                                               emittersAngularSpan=np.radians(self.emittersAngularSpan),
                                               rotationDelta=np.radians(self.rotationDelta),
                                               useFilter=self.useFilter)
        self.showSinogram(self.radonTransformator.getSinogram())
        self.showReconstruction(self.radonTransformator.getReconstruction())

    def generateSinogram(self):
        self.isRecFinished = False
        self.radonTransformator.generateSinogram()
        self.showSinogram(self.radonTransformator.getSinogram())
        self.radonTransformator.generateReconstruction(from_iteration=0)  # rekonstrukcja obrazu
        self.showReconstruction(self.radonTransformator.getReconstruction())
        self.radonTransformator.getRMSE()  # oblicz blad sredniokwadratowy

        self.isRecFinished = True

        self.createDicomButton.grid(column=2, row=14) # pokaz przycisk do zapisu dicom

    def runAnimation(self):
        self.isRecFinished = False
        while self.radonTransformator.nextIteration() > 0:
            self.showSinogram(self.radonTransformator.getSinogram())
            self.window.update()

        while self.radonTransformator.nextReconstructionIteration() > 0:
            self.showReconstruction(self.radonTransformator.getReconstruction())
            self.window.update()
        self.radonTransformator.getRMSE()  # oblicz blad sredniokwadratowy

        self.isRecFinished = True

        self.createDicomButton.grid(column=2, row=14) # pokaz przycisk do zapisu dicom

    # DICOM handling

    def createDicom(self):
        if self.isRecFinished==False:
            messagebox.showinfo(title="Error creating DICOM", message="Image reconstruction isn't finished yet!")
            return

        patient_data = {}
        patient_data['PatientName'] = self.nametxt.get("1.0", 'end-1c') # czytaj od: 1 - pierwsza linia, 0 - pierwszy znak, -1c usun \n na koncu
        patient_data['PatientID'] = self.idtxt.get("1.0", 'end-1c')
        patient_data['StudyDate'] = self.datetxt.get("1.0", 'end-1c')
        patient_data['ImageComments'] = self.commenttxt.get("1.0", 'end-1c')

        if patient_data['PatientName'] == "" or patient_data['PatientID'] == "":
            messagebox.showinfo(title="Input error", message="Enter patient name and id")
        elif not patient_data['StudyDate'].isdigit():
            messagebox.showinfo(title="Input error", message="Date should be in the format YYYYMMDD")
        else:
            filename = self.filenametxt.get("1.0", 'end-1c')
            self.save_as_dicom(filename + '.dcm', self.radonTransformator.getReconstruction(),patient_data)

            messagebox.showinfo(title="Success", message="DICOM file created")

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

    def validate_rotationDeltaInput(self, val):
        if val.isdigit() and int(val)>0 and int(val)<180:
            return True
        return False
    def validate_startRotationInput(self, val):
        if val.isdigit() and int(val)>=0 and int(val)<=360:
            return True
        return False
    def validate_spanInput(self, val):
        if val.isdigit() and int(val)>=1 and int(val)<=100:
            return True
        return False
    def validate_countInput(self, val):
        if val.isdigit() and int(val)>=1 and int(val)<1000:
            return True
        return False


