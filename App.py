from tkinter import Tk, Label, Scale
from PIL import ImageTk, Image, ImageDraw
import numpy as np

class App:
    
    def __init__(self):

        self.currentRotation = 0
        self.numberOfEmitters = 5
        self.emittersAngularSpan = 45
        self.scannerRadius = 160


        self.window = Tk()
        self.window.title('computed tomography scan simulator')
        self.window.geometry('600x800')

        self.baseImage = Image.open('example_images/Kwadraty2.jpg')
        self.img = ImageTk.PhotoImage(self.baseImage)
        self.imgLabel = Label(self.window, image=self.img)
        self.imgLabel.pack()

        rotationSlider = Scale(self.window, from_=0, to=360, orient='horizontal', label='rotation', command=self.changeRotation)
        rotationSlider.set(self.currentRotation)
        radiusSlider = Scale(self.window, from_=0, to=300, orient='horizontal', label='radius', command=self.changeScannerRadius)
        radiusSlider.set(self.scannerRadius)
        spanSlider = Scale(self.window, from_=0, to=180, orient='horizontal', label='angular span', command=self.changeEmittersAngularSpan)
        spanSlider.set(self.emittersAngularSpan)
        countSlider = Scale(self.window, from_=0, to=30, orient='horizontal', label='number of emitters', command=self.changeNumberOfEmitters)
        countSlider.set(self.numberOfEmitters)

        rotationSlider.pack()
        radiusSlider.pack()
        spanSlider.pack()
        countSlider.pack()

        self.updateSensorsDraw()

        self.window.mainloop()

    def loadImage(self, filepath):
        self.baseImage = Image.open(filepath)
        self.img = ImageTk.PhotoImage(self.baseImage)
        self.imgLabel.config(image=self.img)

    def setImage(self, image):
        self.img = ImageTk.PhotoImage(image)
        self.imgLabel.config(image=self.img)

    def processImage(self, image):
        marray = np.array(image)
        print(marray.shape)

        for row in marray:
            for px in row:
                px[0] = 255
                px[1] = 0
                px[2] = 0

        return Image.fromarray(marray)

    def drawSensors(self, radius, rotation, sensorsCount, sensorsRange):
        drawable = ImageDraw.Draw(self.baseImage.copy())

        sensorsRangeRad = np.radians(sensorsRange)
        rotationRad = np.radians(rotation)
        rotationRadSym = rotationRad + np.pi
        center = (drawable._image.size[0] / 2, drawable._image.size[1] / 2)
        
        # draw circle
        upperleftcorner = (center[0] - radius, center[1] - radius)
        lowerrightcorner = (center[0] + radius, center[1] + radius)

        drawable.ellipse((upperleftcorner, lowerrightcorner), outline=(255,0,0))
        
        #draw emitters and detectors

        angles = np.zeros(sensorsCount * 2)
        halfofrange = sensorsRangeRad/2
        gapangle = sensorsRangeRad/(sensorsCount - 1)

        #emitters
        for i in range(sensorsCount):
            angles[i] = rotationRad - halfofrange + i * gapangle

        #detectors
        for i in range(sensorsCount):
            angles[i + sensorsCount] = rotationRadSym - halfofrange + i * gapangle

        cos = np.cos(angles)
        sin = np.sin(angles)

        x = radius * cos + center[0]
        y = radius * sin + center[1]

        pointSize = 3

        #emitters
        for i in range(sensorsCount):
            drawable.ellipse((x[i]-pointSize, y[i]-pointSize, x[i] + pointSize, y[i] + pointSize), fill=(0,0,255))

        #detectors
        for i in range(sensorsCount, len(x)):
            drawable.ellipse((x[i]-pointSize, y[i]-pointSize, x[i] + pointSize, y[i] + pointSize), fill=(255,100,20))

        self.setImage(drawable._image)
        

    def updateSensorsDraw(self):
        self.drawSensors(self.scannerRadius, self.currentRotation, self.numberOfEmitters, self.emittersAngularSpan)

    def changeRotation(self, event):
        self.currentRotation = int(event)
        self.updateSensorsDraw()

    def changeScannerRadius(self, event):
        self.scannerRadius = int(event)
        self.updateSensorsDraw()

    def changeNumberOfEmitters(self, event):
        self.numberOfEmitters = int(event)
        self.updateSensorsDraw()

    def changeEmittersAngularSpan(self, event):
        self.emittersAngularSpan = int(event)
        self.updateSensorsDraw()