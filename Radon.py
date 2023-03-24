from PIL import ImageTk, Image, ImageDraw, ImageOps
import numpy as np
import time

class Radon:

    def __init__(self, baseImage, startRotation = 0, numberOfEmitters = 10, emittersAngularSpan = 1.57075, rotationDelta = 0.04363):
        
        self.baseImage = baseImage
        self.baseImageL = baseImage.convert('L')
        self.baseImageArray = np.array(self.baseImageL)

        self.configAndReset(startRotation=startRotation, numberOfEmitters=numberOfEmitters, emittersAngularSpan=emittersAngularSpan, rotationDelta=rotationDelta)

    def configAndReset(self, startRotation = None, numberOfEmitters = None, emittersAngularSpan = None, rotationDelta = None):
        if startRotation != None:
            self.startRotation = startRotation
        if numberOfEmitters != None:
            self.numberOfEmitters = numberOfEmitters
        if emittersAngularSpan != None:
            self.emittersAngularSpan = emittersAngularSpan
        if rotationDelta != None:
            self.rotationDelta = rotationDelta


        self.currentIteration = 0
        self.numberOfIterations = int(np.pi / rotationDelta)
        self.radonmatrix = np.zeros((self.numberOfEmitters, self.numberOfIterations))
        self.radonmatrixNorm = np.zeros((self.numberOfEmitters, self.numberOfIterations))

        imgWidth = self.baseImage.size[0]
        imgHeight = self.baseImage.size[1]

        self.imageDiagonal = np.sqrt((imgWidth * imgWidth) + (imgHeight * imgHeight))

        self.scannerRadius = int(self.imageDiagonal / 2)

        self.imageCenter = (self.baseImage.size[0] / 2, self.baseImage.size[1] / 2)
        self.angles = np.zeros(self.numberOfEmitters * 2)
        self.halfOfSpan = self.emittersAngularSpan / 2
        self.angleGapBetweenSensors = self.emittersAngularSpan/(self.numberOfEmitters - 1)

    def reset(self):
        self.configAndReset()

    #returns current state of sinogram
    def getSinogram(self):
        return Image.fromarray(self.radonmatrixNorm)

    #calculates sinogram from 'from_iteration' inclusive to 'to_iteration' exclusive
    def generateSinogram(self, from_iteration=None, to_iteration=None):

        s_time = time.time()

        if from_iteration == None:
            from_iteration = self.currentIteration
        if to_iteration == None:
            to_iteration = self.numberOfIterations

        if from_iteration >= self.numberOfIterations or to_iteration > self.numberOfIterations:
            return

        #current roation of all emitters (indices from 0 to self.numberOfEmitters - 1) and detectors (indices from self.numberOfEmitters to 2*self.numberOfEmitters - 1) in radians
        rotation = np.arange(self.numberOfEmitters)
        rotation = np.concatenate((rotation, rotation))

        initRotation = self.startRotation + (from_iteration - 1) * self.rotationDelta - self.halfOfSpan
        rotation = rotation * self.angleGapBetweenSensors + initRotation
        rotation[self.numberOfEmitters : ] += np.pi

        for iter in range(from_iteration, to_iteration):
            rotation += self.rotationDelta

            x = self.scannerRadius * np.cos(rotation) + self.imageCenter[0]
            y = self.scannerRadius * np.sin(rotation) + self.imageCenter[1]

            last = len(x) - 1
            #emitters and detectors
            for i in range(self.numberOfEmitters):
                points = self.bresenham_integer(int(x[i]), int(y[i]), int(x[last - i]), int(y[last - i]))
                self.radonmatrix[i, iter] = self.sumPixels(points, self.baseImageArray)

            self.currentIteration += 1
        
        self.radonmatrixNorm = self.radonmatrix / (np.max(self.radonmatrix) / 255)

        print(time.time() - s_time)

    def nextIteration(self, count=1):
        self.generateSinogram(to_iteration=self.currentIteration + count + 1)

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

        w =  self.baseImage.size[0]
        h =  self.baseImage.size[1]

        x = []
        y = []
        while x0 != x1 or y0 != y1:
            if x0 > 0 and x0 < w and y0 > 0 and y0 < h:
                x.append(x0)
                y.append(y0)
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        if x0 > 0 and x0 < w and y0 > 0 and y0 < h:
            x.append(x0)
            y.append(y0)
        return [x, y]


    def sumPixels(self, points, imageArray): # sumowanie wartości pikseli w linii
        return np.sum(imageArray[points[0], points[1]])