from tkinter import Tk, Label, Scale, Button

import matplotlib.pyplot as plt
from PIL import ImageTk, Image, ImageDraw, ImageOps
import numpy as np
import time



class App:
    
    def __init__(self):

        self.currentIteration = 0

        self.startRotation = 0
        self.numberOfEmitters = 10
        self.emittersAngularSpan = 90
        self.rotationDelta = 5

        self.maxDisplayWidth = 400
        self.maxDisplayHeight = 600


        self.window = Tk()
        self.window.title('computed tomography scan simulator')
        self.window.geometry('1024x1024')

        self.baseImage = Image.open('example_images/Kolo.jpg')

        # save original image size
        self.originalImage = self.baseImage
        self.imgWidth = self.baseImage.width
        self.imgHeight = self.baseImage.height

        # add black frames to the image that is displayed
        self.baseImage = ImageOps.expand(self.baseImage, border=(100, 100, 100, 100), fill='black')


        self.img = ImageTk.PhotoImage(self.resizeToFitLimits(self.baseImage))
        self.imgLabel = Label(self.window, image=self.img)
        self.imgLabel.grid(column=0, row = 0, columnspan=2)

        #place for sinogram
        self.sinogram = Image.open('example_images/Kolo.jpg')
        self.sinImg = ImageTk.PhotoImage(self.resizeToFitLimits(self.sinogram))
        self.sinImgLabel = Label(self.window, image=self.sinImg)
        self.sinImgLabel.grid(column=2, row = 0, columnspan=2)

        self.diagonal=np.sqrt((self.imgHeight*self.imgHeight)+(self.imgWidth*self.imgWidth))/2
        self.scannerRadius = self.diagonal

        startRotationSlider = Scale(self.window, from_=0, to=360, orient='horizontal', label='initial rotation', command=self.changeRotation)
        startRotationSlider.set(self.startRotation)
        spanSlider = Scale(self.window, from_=0, to=180, orient='horizontal', label='angular span', command=self.changeEmittersAngularSpan)
        spanSlider.set(self.emittersAngularSpan)
        countSlider = Scale(self.window, from_=0, to=100, orient='horizontal', label='number of emitters', command=self.changeNumberOfEmitters)
        countSlider.set(self.numberOfEmitters)
        rotationDeltaSlider = Scale(self.window, from_=0, to=90, orient='horizontal', label='delta of rotation', command=self.changeRotationDelta)
        rotationDeltaSlider.set(self.rotationDelta)

        iterationSlider = Scale(self.window, from_=0, to=180, orient='horizontal', label='iteration', command=self.changeIteration)
        iterationSlider.set(self.currentIteration)

        applyParamsButton = Button(self.window, text="zastosuj i resetuj sinogram" ,command=self.applyParams)
        nextButton= Button(self.window, text="następna iteracja", command=self.nextIteration)

        startRotationSlider.grid(column=0, row=1)
        spanSlider.grid(column=2, row=1)
        countSlider.grid(column=3, row=1)
        rotationDeltaSlider.grid(column=0, row=2)
        applyParamsButton.grid(column=1, row=3, columnspan=2)
        nextButton.grid(column=1, row=4, columnspan=2)

        '''from skimage.transform import radon # gotowa funkcja radona z bibilioteki skimage
        sinogram = radon(np.array(self.originalImage.convert('L')), circle=True)
        plt.imshow(sinogram, cmap='gray')
        plt.show()'''

        self.resetSinogram()
        self.updateSensorsDraw()

        

        self.window.mainloop()

    def resizeToFitLimits(self, image):
        newShape = (0 , 0)
        if image.size[0] > image.size[1]:
            newShape = (self.maxDisplayWidth, int(self.maxDisplayWidth * (image.size[1] / image.size[0])))
        else:
            newShape = (int(self.maxDisplayHeight * (image.size[0] / image.size[1])), self.maxDisplayHeight)

        return image.resize(newShape, resample=Image.BILINEAR)

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

    def processImage(self, image):
        marray = np.array(image)
        #print(marray.shape)

        for row in marray:
            for px in row:
                px[0] = 255
                px[1] = 0
                px[2] = 0

        return Image.fromarray(marray)

    def drawSensors(self, radius, rotation, sensorsCount, sensorsRange):
        drawable = ImageDraw.Draw(self.baseImage.copy())

        sensorsRangeRad = np.radians(sensorsRange)
        #rotationRad = np.radians(rotation) # przeniesione do pętli
        #rotationRadSym = rotationRad + np.pi # przeniesione do pętli
        center = (drawable._image.size[0] / 2, drawable._image.size[1] / 2)
        alpha = 10 # should be parameter
        
        # draw circle
        upperleftcorner = (center[0] - radius, center[1] - radius)
        lowerrightcorner = (center[0] + radius, center[1] + radius)

        drawable.ellipse((upperleftcorner, lowerrightcorner), outline=(255,0,0))
        
        #draw emitters and detectors

        angles = np.zeros(sensorsCount * 2)
        halfofrange = sensorsRangeRad/2
        gapangle = sensorsRangeRad/(sensorsCount - 1)

        radonmatrix = np.zeros((sensorsCount, int(180/self.rotationDelta)))


        # col = 0
        # for j in range(rotation,rotation+180,alpha): # powielanie emiterow(detektorow) co alpha do polowy kola
        #     rotationRad = np.radians(j)
        #     rotationRadSym = rotationRad + np.pi
        #     #emitters
        #     for i in range(sensorsCount):
        #         angles[i] = rotationRad - halfofrange + i * gapangle

        #     #detectors
        #     for i in range(sensorsCount):
        #         angles[i + sensorsCount] = rotationRadSym - halfofrange + i * gapangle

        #     cos = np.cos(angles)
        #     sin = np.sin(angles)

        #     x = radius * cos + center[0]
        #     y = radius * sin + center[1]

        #     pointSize = 3
        #     pairs=[]
        #     #emitters - BLUE
        #     for i in range(sensorsCount):
        #         drawable.ellipse((x[i]-pointSize, y[i]-pointSize, x[i] + pointSize, y[i] + pointSize), fill=(0,0,255))
        #         pairs.append([int(x[i]),int(y[i])])
        #     #detectors
        #     temp=0
        #     for i in range(len(x)-1, sensorsCount-1,-1):
        #         pairs[temp].append(int(x[i]))
        #         pairs[temp].append(int(y[i]))
        #         temp+=1
        #         drawable.ellipse((x[i]-pointSize, y[i]-pointSize, x[i] + pointSize, y[i] + pointSize), fill=(255,100,20))

        #     row = 0
        #     for i in pairs:
        #         points = self.bresenham_integer(*i)
        #         for point in points:
        #             drawable.ellipse((point[0]-1 , point[1]-1 , point[0]+1 , point[1]+1),
        #                              fill=(100, 200, 100))
        #         self.radonmatrix[row, col] = self.sumPixels(points,self.baseImage.copy())
        #         row += 1
        #     col += 1

        rotationRad = np.radians((rotation + self.currentIteration * int(180/self.rotationDelta)))
        rotationRadSym = rotationRad + np.pi
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
        pairs=[]
        #emitters - BLUE
        for i in range(sensorsCount):
            drawable.ellipse((x[i]-pointSize, y[i]-pointSize, x[i] + pointSize, y[i] + pointSize), fill=(0,0,255))
            pairs.append([int(x[i]),int(y[i])])
        #detectors
        temp=0
        for i in range(len(x)-1, sensorsCount-1,-1):
            pairs[temp].append(int(x[i]))
            pairs[temp].append(int(y[i]))
            temp+=1
            drawable.ellipse((x[i]-pointSize, y[i]-pointSize, x[i] + pointSize, y[i] + pointSize), fill=(255,100,20))

        row = 0
        for i in pairs:
            points = self.bresenham_integer(*i)
            for point in points:
                drawable.ellipse((point[0]-1 , point[1]-1 , point[0]+1 , point[1]+1),
                                    fill=(100, 200, 100))
            self.radonmatrix[row, self.currentIteration] = self.sumPixels(points,self.baseImage.copy())
            row += 1
        
        self.showSinogram(Image.fromarray(self.radonmatrix))
        self.setImage(drawable._image)



    def updateSensorsDraw(self):
        self.drawSensors(self.scannerRadius, self.startRotation, self.numberOfEmitters, self.emittersAngularSpan)

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
        self.resetSinogram();


    def resetSinogram(self):
        self.currentIteration = 0
        self.radonmatrix = np.zeros((self.numberOfEmitters, int(180/self.rotationDelta))) # macierz do której stopniowo zapisywany jet sinogram  pod indeksem [indeks emitera, iteracja obrotu] znajduje się znormalizowana suma wartości pikseli na linii emiter-detektor
        self.updateSensorsDraw()
        self.showSinogram(Image.fromarray(self.radonmatrix))

    def nextIteration(self):
        self.currentIteration += 1
        self.updateSensorsDraw()

    def bresenham_integer(self, x0, y0, x1, y1): # wyznaczanie linii
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        if x0 > x1:
            sx = -1
        else:
            sx = 1
        if y0 > y1:
            sy = -1
        else:
            sy = 1

        err = dx - dy

        points = []
        while x0 != x1 or y0 != y1:
            points.append((x0, y0))
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        points.append((x0, y0))
        return points


    def sumPixels(self, points, image): # sumowanie wartości pikseli w linii
        image = np.array(image.convert('L')).tolist()
        res = 0
        for point in points:
            res+=image[point[0]][point[1]]
        return self.normalize(res)

    def normalize(self, value): # normalizowanie od 0 do 255
        return int(value/(self.diagonal))

    def radon(self, sensorsCount, rotation, alpha, sensorsRange, radius):

        sensorsRangeRad = np.radians(sensorsRange)


        angles = np.zeros(sensorsCount * 2)
        halfofrange = sensorsRangeRad / 2
        gapangle = sensorsRangeRad / (sensorsCount - 1)

        center = (self.originalImage.size[0] / 2, self.originalImage.size[1] / 2)


        radonmatrix = []  # tablica zawierająca listy (lines) sum każdej linii w danej iteracji (rozmiar = liczba iteracji)

        for j in range(rotation, rotation + 180, alpha):  # powielanie emiterow(detektorow) co alpha do polowy kola
            lines = []  # tablica zawierająca znormalizowane sumy każdej linii w danej iteracji (rozmiar = sensorsCount)
            rotationRad = np.radians(j)
            rotationRadSym = rotationRad + np.pi

            # emitters
            for i in range(sensorsCount):
                angles[i] = rotationRad - halfofrange + i * gapangle

            # detectors
            for i in range(sensorsCount):
                angles[i + sensorsCount] = rotationRadSym - halfofrange + i * gapangle

            cos = np.cos(angles)
            sin = np.sin(angles)

            x = radius * cos + center[0]
            y = radius * sin + center[1]

            pointSize = 3
            pairs = []
            # emitters - BLUE
            for i in range(sensorsCount):

                pairs.append([int(x[i]), int(y[i])])
            # detectors
            temp = 0
            for i in range(len(x) - 1, sensorsCount - 1, -1):
                pairs[temp].append(int(x[i]))
                pairs[temp].append(int(y[i]))
                temp += 1

            for i in pairs:
                points = self.bresenham_integer(*i)
                lines.append(self.sumPixels(points, self.baseImage.copy()))

            radonmatrix.append(lines)

        # DO ZMIANY
        import matplotlib.pyplot as plt

        # Plot the sinogram
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4.5))
        ax1.set_title("Original")
        ax1.imshow(self.baseImage, cmap=plt.cm.Greys_r)

        ax2.set_title("Sinogram")
        ax2.set_xlabel("Projection angle (degrees)")
        ax2.set_ylabel("Projection position (pixels)")
        ax2.imshow(radonmatrix, cmap=plt.cm.Greys_r,
                   extent=(0, 180, 0, np.array(radonmatrix).shape[0]), aspect='auto')

        plt.show()
