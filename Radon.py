from PIL import Image
import numpy as np
import time


class Radon:

    def __init__(self, baseImage, startRotation=0, numberOfEmitters=10, emittersAngularSpan=1.57075,
                 rotationDelta=0.04363, useFilter=False):

        self.baseImage = baseImage
        self.baseImageL = baseImage.convert('L')
        self.baseImageArray = np.array(self.baseImageL)

        self.configAndReset(startRotation=startRotation, numberOfEmitters=numberOfEmitters,
                            emittersAngularSpan=emittersAngularSpan, rotationDelta=rotationDelta, useFilter=useFilter)

    def configAndReset(self, startRotation=None, numberOfEmitters=None, emittersAngularSpan=None, rotationDelta=None, useFilter=None):
        if startRotation != None:
            self.startRotation = startRotation
        if numberOfEmitters != None:
            self.numberOfEmitters = numberOfEmitters
        if emittersAngularSpan != None:
            self.emittersAngularSpan = emittersAngularSpan
        if rotationDelta != None:
            self.rotationDelta = rotationDelta
        if useFilter != None:
            self.useFilter = useFilter

        self.currentSinogramIteration = 0
        self.currentReconstructionIteration = 0
        self.numberOfIterations = int(np.pi / rotationDelta)
        self.radonmatrix = np.zeros((self.numberOfEmitters, self.numberOfIterations))
        self.radonmatrixNorm = np.zeros((self.numberOfEmitters, self.numberOfIterations))

        imgWidth = self.baseImageArray.shape[0]
        imgHeight = self.baseImageArray.shape[1]

        self.reconstrImage = np.zeros(self.baseImageArray.shape) # reconstrukcja obrazu z sinogramu
        self.reconstrImageNorm = self.reconstrImage.copy() # reconstrukcja obrazu z sinogramu

        self.imageDiagonal = np.sqrt((imgWidth * imgWidth) + (imgHeight * imgHeight))

        self.scannerRadius = int(self.imageDiagonal / 2)

        self.imageCenter = (imgWidth / 2, imgHeight / 2)
        self.halfOfSpan = self.emittersAngularSpan / 2
        self.angleGapBetweenSensors = self.emittersAngularSpan / (self.numberOfEmitters - 1)

    def reset(self):
        self.configAndReset()

    # returns current state of sinogram
    def getSinogram(self):
        return Image.fromarray(self.radonmatrixNorm)

    # calculates sinogram using Radon Transform from 'from_iteration' inclusive to 'to_iteration' exclusive
    def generateSinogram(self, from_iteration=None, to_iteration=None):

        s_time = time.time()

        if from_iteration == None:
            from_iteration = self.currentSinogramIteration
        if to_iteration == None:
            to_iteration = self.numberOfIterations

        if from_iteration >= self.numberOfIterations or to_iteration > self.numberOfIterations:
            return

        # current roation of all emitters (indices from 0 to self.numberOfEmitters - 1) and detectors (indices from self.numberOfEmitters to 2*self.numberOfEmitters - 1) in radians
        rotation = np.arange(self.numberOfEmitters)
        rotation = np.concatenate((rotation, rotation))

        initRotation = self.startRotation + from_iteration * self.rotationDelta - self.halfOfSpan
        rotation = rotation * self.angleGapBetweenSensors + initRotation
        rotation[self.numberOfEmitters:] += np.pi

        for iter in range(from_iteration, to_iteration):
            rotation += self.rotationDelta

            x = self.scannerRadius * np.cos(rotation) + self.imageCenter[0]
            y = self.scannerRadius * np.sin(rotation) + self.imageCenter[1]

            last = len(x) - 1
            # emitters and detectors
            for i in range(self.numberOfEmitters):
                points = self.bresenham(int(x[i]), int(y[i]), int(x[last - i]), int(y[last - i]))
                self.radonmatrix[i, iter] = self.sumPixels(points, self.baseImageArray)
            last = len(x) - 1

            self.currentSinogramIteration += 1

        if self.useFilter:
            tmpRadon = self.filter(self.radonmatrix)
        else:
            tmpRadon = self.radonmatrix.copy()
        self.radonmatrixNorm = tmpRadon / (np.max(tmpRadon) / 255)
        print("sinogram: ", (time.time() - s_time))

    def nextIteration(self, count=1):
        prev = self.currentSinogramIteration
        self.generateSinogram(to_iteration=self.currentSinogramIteration + count)
        return self.currentSinogramIteration - prev
    
    def nextReconstructionIteration(self, count=1):
        prev = self.currentReconstructionIteration
        self.generateReconstruction(to_iteration=self.currentReconstructionIteration + count)
        return self.currentReconstructionIteration - prev

    def bresenham(self, x0, y0, x1, y1):  # wyznaczanie linii
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        # wybieranie znaku dla x i y
        if x0 > x1:
            sx = -1
        else:
            sx = 1
        if y0 > y1:
            sy = -1
        else:
            sy = 1

        err = dx - dy

        w = self.baseImageArray.shape[0]
        h = self.baseImageArray.shape[1]

        x = []
        y = []
        added = False
        while x0 != x1 or y0 != y1:
            if x0 >= 0 and x0 < w and y0 >= 0 and y0 < h:
                x.append(x0)
                y.append(y0)
                added = True
            elif added: # linia 'wyszła' poza obrazek, żaden piksel nie spełni już warunku ifa powyżej, więc można skończyć
                break
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

    def sumPixels(self, points, imageArray):  # sumowanie wartości pikseli w linii
        return np.sum(imageArray[points[0], points[1]])

    def getReconstruction(self):
        return Image.fromarray(self.reconstrImageNorm)
    
    # calculates image reconstruction using Inverse Radon Transform
    def generateReconstruction(self, from_iteration=None, to_iteration=None):

        s_time = time.time()

        if from_iteration == None:
            from_iteration = self.currentReconstructionIteration
        if to_iteration == None:
            to_iteration = self.numberOfIterations

        if from_iteration >= self.numberOfIterations or to_iteration > self.numberOfIterations:
            return

        # current roation of all emitters (indices from 0 to self.numberOfEmitters - 1) and detectors (indices from self.numberOfEmitters to 2*self.numberOfEmitters - 1) in radians
        rotation = np.arange(self.numberOfEmitters)
        rotation = np.concatenate((rotation, rotation))

        initRotation = self.startRotation + from_iteration * self.rotationDelta - self.halfOfSpan
        rotation = rotation * self.angleGapBetweenSensors + initRotation
        rotation[self.numberOfEmitters:] += np.pi

        for iter in range(from_iteration, to_iteration):
            rotation += self.rotationDelta

            x = self.scannerRadius * np.cos(rotation) + self.imageCenter[0]
            y = self.scannerRadius * np.sin(rotation) + self.imageCenter[1]

            last = len(x) - 1
            # emitters and detectors
            for i in range(self.numberOfEmitters):
                points = self.bresenham(int(x[i]), int(y[i]), int(x[last - i]), int(y[last - i]))
                self.reconstrImage[points[0], points[1]] += self.radonmatrixNorm[i, iter]

            self.currentReconstructionIteration += 1

        # normalizacja
        self.reconstrImageNorm = 255 * self.reconstrImage / np.max(self.reconstrImage)

        print("reconstruction: ", (time.time() - s_time))

    def rampFilter(self, size):
        n = np.concatenate((
                np.arange(1, size / 2 + 1, 2, dtype=int),
                np.arange(size / 2 - 1, 0, -2, dtype=int))
        )
        f = np.zeros(size)
        f[0] = 0.25
        f[1::2] = -1 / (np.pi * n) ** 2

        return 2 * np.real(np.fft.fft(f))

    def filter(self, sinogram):
        filtered = sinogram.copy()
        rlf = self.rampFilter(filtered.shape[0])
        for i in range(filtered.shape[1]):
            f = np.fft.fft(filtered[:, i]) * rlf
            filtered[:, i] = np.real(np.fft.ifft(f))

        return filtered
    
    
    def getMSE(self):
        mse = 0

        imgWidth = self.baseImageArray.shape[0]
        imgHeight = self.baseImageArray.shape[1]

        for i in range(imgWidth):
            for j in range(imgHeight):
                mse += (self.reconstrImageNorm[i][j] - self.baseImageArray[i][j])**2
        mse = mse/(imgWidth*imgHeight)
        print("MSE =",mse)