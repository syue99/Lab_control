import numpy as np


class nuvuDriver():
    def __init__(self):
        pass

    def setExposure(self, exposureTime):
        pass

    def setROI(self, x0, y0, wx, wy):
        self.xDim = 2 * wx
        self.yDim = 2 * wy

    def getLiveFrame(self):
        return np.zeros((self.yDim, self.xDim))

    def startAcquisition(self):
        pass

    def endAcquisition(self):
        pass
