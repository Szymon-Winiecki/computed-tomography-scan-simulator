from PIL import ImageTk, Image, ImageDraw, ImageOps
import numpy as np

class Radon:

    def __init__(self, baseImage, startRotation = 0, numberOfEmitters = 10, emittersAngularSpan = 1.57075, rotationDelta = 0.04363):
        
        self.baseImage = baseImage

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
        if from_iteration == None:
            from_iteration = self.currentIteration
        if to_iteration == None:
            to_iteration = self.numberOfIterations

        if from_iteration >= self.numberOfIterations or to_iteration > self.numberOfIterations:
            return

        for iter in range(from_iteration, to_iteration):
            rotation = self.startRotation + iter * self.rotationDelta
            rotationSym = rotation + np.pi
            #emitters
            for i in range(self.numberOfEmitters):
                self.angles[i] = rotation - self.halfOfSpan + i * self.angleGapBetweenSensors

            #detectors
            for i in range(self.numberOfEmitters):
                self.angles[i + self.numberOfEmitters] = rotationSym - self.halfOfSpan + i * self.angleGapBetweenSensors

            cos = np.cos(self.angles)
            sin = np.sin(self.angles)

            x = self.scannerRadius * cos + self.imageCenter[0]
            y = self.scannerRadius * sin + self.imageCenter[1]

            pairs=[]
            #emitters
            for i in range(self.numberOfEmitters):
                pairs.append([int(x[i]),int(y[i])])
            #detectors
            temp=0
            for i in range(len(x) - 1, self.numberOfEmitters - 1, -1):
                pairs[temp].append(int(x[i]))
                pairs[temp].append(int(y[i]))
                temp+=1

            row = 0
            for i in pairs:
                points = self.bresenham_integer(*i)
                self.radonmatrix[row, iter] = self.sumPixels(points, self.baseImage)
                row += 1
            self.currentIteration += 1
        
        self.radonmatrixNorm = 255 * self.radonmatrix / np.max(self.radonmatrix)

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
        imgWidth = image.size[0]
        imgHeight = image.size[1]
        image = np.array(image.convert('L'))
        res = 0
        for point in points:
            if point[0] > 0 and point[0] < imgWidth and point[1] > 0 and point[1] < imgHeight:
                res+=image[point[1], point[0]]
        return res