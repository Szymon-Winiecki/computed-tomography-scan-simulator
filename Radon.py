from PIL import Image
import numpy as np
import time

class Radon:

    def __init__(self, baseImage, startRotation=0, numberOfEmitters=10, emittersAngularSpan=1.57075,
                 rotationDelta=0.04363, useFilter=False):

        self.baseImage = baseImage
        self.baseImageArray = np.array(baseImage.convert('L'))

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

        # variables to hold current progress of computation
        self.currentSinogramIteration = 0
        self.currentReconstructionIteration = 0

        self.numberOfIterations = int(np.pi / rotationDelta)

        # original image properties
        imgWidth = self.baseImageArray.shape[0]
        imgHeight = self.baseImageArray.shape[1]
        imgRatio = imgWidth/imgHeight
        self.imageCenter = (imgWidth / 2, imgHeight / 2)

        # arrays to store sinogram
        self.radonmatrix = np.zeros((self.numberOfEmitters, self.numberOfIterations))
        self.radonmatrixNorm = np.zeros((self.numberOfEmitters, self.numberOfIterations))

        # reconstructed image properties
        reconstrWidth = imgWidth
        reconstrHeight = imgHeight
        self.reconstrCenter = (reconstrWidth / 2, reconstrHeight / 2)
        self.reconstrRadius = np.sqrt((reconstrWidth * reconstrWidth) + (reconstrHeight * reconstrHeight)) / 2

        # arrays to store reconstructed image
        self.reconstrImage = np.zeros((reconstrWidth, reconstrHeight))
        self.reconstrImageNorm = self.reconstrImage.copy()

        # helper values for computation
        self.scannerRadius = np.sqrt((imgWidth * imgWidth) + (imgHeight * imgHeight)) / 2   # half of original image diagonal
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
            for i in range(self.numberOfEmitters):
                points = self.bresenham(int(x[i]), int(y[i]), int(x[last - i]), int(y[last - i]), self.baseImageArray.shape[0], self.baseImageArray.shape[1])
                self.radonmatrix[i, iter] = self.sumPixels(points, self.baseImageArray)

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

    # returns coordinates of points that belongs to line from (x0, y0) to (x1, y1) and are on the image with width w and height h
    def bresenham(self, x0, y0, x1, y1, w, h):
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

        x = []
        y = []
        added = False
        while x0 != x1 or y0 != y1:
            if x0 >= 0 and x0 < w and y0 >= 0 and y0 < h:
                x.append(x0)
                y.append(y0)
                added = True
            elif added: # line 'was' on the image and will never return again (any of the following pixels won't meet the condition of the previous if statement)
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

    def sumPixels(self, points, imageArray):
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

            x = self.reconstrRadius * np.cos(rotation) + self.reconstrCenter[0]
            y = self.reconstrRadius * np.sin(rotation) + self.reconstrCenter[1]

            last = len(x) - 1
            # emitters and detectors
            for i in range(self.numberOfEmitters):
                points = self.bresenham(int(x[i]), int(y[i]), int(x[last - i]), int(y[last - i]), self.reconstrImage.shape[0], self.reconstrImage.shape[1])
                self.reconstrImage[points[0], points[1]] += self.radonmatrixNorm[i, iter]

            self.currentReconstructionIteration += 1

        self.reconstrImageNorm = self.reconstrImage / (np.max(self.reconstrImage) / 255)

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
    
    def getRMSE(self):
        rmse = 0

        imgWidth = self.baseImageArray.shape[0]
        imgHeight = self.baseImageArray.shape[1]

        if self.baseImageArray.shape != self.reconstrImageNorm.shape:
            reconstr = np.array(Image.fromarray(self.reconstrImageNorm).resize((imgHeight, imgWidth), resample=Image.NEAREST))
        else:
            reconstr = self.reconstrImageNorm

        for i in range(imgWidth):
            for j in range(imgHeight):
                rmse += (reconstr[i][j] - self.baseImageArray[i][j])**2
        rmse = rmse/(imgWidth*imgHeight)
        rmse = np.sqrt(rmse)
        print("RMSE =",rmse)