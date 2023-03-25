from tkinter import Tk, Label, Scale, Button

import matplotlib.pyplot as plt
from PIL import ImageTk, Image, ImageDraw, ImageOps
import numpy as np
import time

from Radon import Radon


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
        self.window.geometry('900x700')

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

        applyParamsButton = Button(self.window, text="zastosuj i resetuj sinogram", command=self.applyParams)

        startRotationSlider.grid(column=0, row=1)
        spanSlider.grid(column=1, row=1)
        countSlider.grid(column=2, row=1)
        rotationDeltaSlider.grid(column=0, row=2)
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

    # def nextIteration(self):
    #     self.radonTransformator.nextIteration()