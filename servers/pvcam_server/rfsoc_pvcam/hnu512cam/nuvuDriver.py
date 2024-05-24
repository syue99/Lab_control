import warnings
from ctypes import *

import numpy as np

from servers.drivers.hnu512cam.nuvu_ctypes_wrapper import NC_api
from servers.drivers.hnu512cam.nuvu_ctypes_wrapper import nc_camera
from servers.drivers.hnu512cam.nuvu_ctypes_wrapper.structures import NCIMAGE


class NuvuDriver:
    def __init__(self):
        self.myCam = nc_camera.nc_camera()
        self.camROISize = [512, 512]  # width, height
        self.camROIx0y0 = [[256], [256]]  # x0, y0
        self.imageSizeY = 512  # size of all ROIs stacked vertically
        self.imageSizeX = 512
        self.binning = [1, 1]

        self._initCamera()

    def _pCheckError(self, error):
        """
        Function to check and raise Nuvu code error
        """
        if error:
            if error == 214:
                warnings.warn('Nuvu camera error with code %d' % error)
            else:
                raise RuntimeError('Nuvu camera error with code %d' % error)
        else:
            pass

    def _initCamera(self):
        print('Connecting to NUVU camera')
        self.myCam.openCam()
        print('Connected to NUVU camera')
        ''' basic setting '''
        error = NC_api.ncCamSetReadoutMode(self.myCam.ncCam, c_int(1))  # use readout mode # 1
        self._pCheckError(error)
        print('Set NUVU readout mode')
        error = NC_api.ncCamAbort(self.myCam.ncCam)
        self._pCheckError(error)
        self.setMROI(self.camROIx0y0[0], self.camROIx0y0[1], self.camROISize[0], self.camROISize[1])
        error = NC_api.ncCamSetShutterMode(self.myCam.ncCam, c_int(1))  # open shutter
        self._pCheckError(error)
        error = NC_api.ncCamSetTimeout(self.myCam.ncCam, c_int(20000))  # set timeout to 20 S
        self._pCheckError(error)
        self.setTriggerMode(mode=1)  # set the trigger mode to 'EXT_LOW_HIGH'
        print('Initialized NUVU camera')

    def _addCamROI(self, X0, Y0):
        """ add camera ROI """
        if self._getMRoiCountMax == 1:
            raise RuntimeError('Only one ROI allowed!')
        wX = self.camROISize[0]
        wY = self.camROISize[1]
        error = NC_api.ncCamAddMRoi(self.myCam.ncCam, c_int(X0), c_int(Y0), c_int(wX), c_int(wY))
        self._pCheckError(error)
        error = NC_api.ncCamMRoiApply(self.myCam.ncCam)
        self._pCheckError(error)
        print('Adding camera ROI to x0 = {:d}, '
              'y0 = {:d}, wx = {:d}, wy = {:d}'.format(X0, Y0, wX, wY))

    def setCamROISize(self, wX, wY):
        """ set camera ROI size"""
        if wX == self.camROISize[0] and wY == self.camROISize[1]:
            pass
        else:
            ROIcount = self.getMRoiCount()
            for index in range(ROIcount):
                error = NC_api.ncCamSetMRoiSize(self.myCam.ncCam, c_int(index), c_int(wX), c_int(wY))
                self._pCheckError(error)
            error = NC_api.ncCamMRoiApply(self.myCam.ncCam)
            self._pCheckError(error)
            self.camROISize = [wX, wY]
        print('Setting camera ROI size to wx = {:d}, wy = {:d}'.format(wX, wY))

    def setTriggerMode(self, mode, nPerTrig=1):
        """ set trigger mode (mode, integer from -3 to 3) and number of images per trigger (nPerTrig) """
        triggerModeList = ['CONT_HIGH_LOW',
                           'EXT_HIGH_LOW_EXP',  # exp: exposure duration is set by trigger voltage
                           'EXT_HIGH_LOW',
                           'INTERNAL',
                           'EXT_LOW_HIGH',
                           'EXT_LOW_HIGH_EXP',
                           'CONT_LOW_HIGH']
        print('Setting trigger to: %s' % triggerModeList[mode + 3])  # notice triggerMode ranges from -3 to +3
        print('Setting number of images per trigger to: %d' % nPerTrig)
        error = NC_api.ncCamSetTriggerMode(self.myCam.ncCam, c_int(mode), c_int(nPerTrig))
        self._pCheckError(error)

    def getTriggerMode(self):
        triggerMode = c_long(1)
        nPerTrig = c_long(1)
        error = NC_api.ncCamGetTriggerMode(self.myCam.ncCam, c_int(1), byref(triggerMode), byref(nPerTrig))
        self._pCheckError(error)
        return triggerMode.value, nPerTrig.value

    def setExposure(self, exposureTime):
        """ set exposure time in unit of S """
        error = NC_api.ncCamSetExposureTime(self.myCam.ncCam,
                                            c_double(exposureTime['ms']))  # nuvu takes time unit of msec
        print('Setting exposure time to %f ms' % exposureTime['ms'])
        self._pCheckError(error)

    def getExposureTime(self):
        """ get exposure time in unit of S  """
        exposureTime = c_double(1)
        error = NC_api.ncCamGetExposureTime(self.myCam.ncCam, c_int(1),
                                            byref(exposureTime))  # nuvu takes time unit of mS
        self._pCheckError(error)
        return exposureTime.value * 1e-3

    def setMROI(self, X0list, Y0list, wX, wY):
        if len(X0list) != len(Y0list):
            raise ValueError('CenterX and CenterY have different length!')
        X0list = list(X0list)
        Y0list = list(Y0list)
        if self.camROIx0y0[0] == X0list and self.camROIx0y0[1] == Y0list \
                and self.camROISize[0] == wX and self.camROISize[1] == wY:
            return None

        ROIcount = self.getMRoiCount()
        # Delete previous ROIs
        for i in range(1, ROIcount):
            error = NC_api.ncCamDeleteMRoi(self.myCam.ncCam, c_int(1))
            self._pCheckError(error)
        error = NC_api.ncCamMRoiApply(self.myCam.ncCam)
        self._pCheckError(error)

        # set up new ROIs
        self.setCamROISize(wX, wY)
        error = NC_api.ncCamSetMRoiPosition(self.myCam.ncCam, c_int(0), c_int(X0list[0]), c_int(Y0list[0]))
        self._pCheckError(error)
        print('Adding camera ROI to x0 = {:d}, y0 = {:d}, '
              'wx = {:d}, wy = {:d}'.format(X0list[0], Y0list[0], wX, wY))
        for i in range(1, len(X0list)):
            self._addCamROI(X0list[i], Y0list[i])
        error = NC_api.ncCamMRoiApply(self.myCam.ncCam)
        self._pCheckError(error)
        self.imageSizeX, self.imageSizeY = [wX, len(X0list) * wY]
        self.camROIx0y0 = [X0list, Y0list]
        self.camROISize = [wX, wY]

    def getCamROI(self, index):
        """ get one index_th ROI position and size """
        x0 = c_long(1)
        y0 = c_long(1)
        error = NC_api.ncCamGetMRoiPosition(self.myCam.ncCam, c_int(index), byref(x0), byref(y0))
        self._pCheckError(error)
        wX = c_long(1)
        wY = c_long(1)
        error = NC_api.ncCamGetMRoiSize(self.myCam.ncCam, c_int(index), byref(wX), byref(wY))
        self._pCheckError(error)
        return [x0.value, y0.value, wX.value, wY.value]

    def setBinningMode(self, binX, binY):
        """ set camera binning """
        if binX == self.binning[0] and binY == self.binning[1]:
            return
        error = NC_api.ncCamSetBinningMode(self.myCam.ncCam, binX, binY)
        self._pCheckError(error)
        print('Setting camera binning mode to binX = {:d}, binY = {:d}'.format(binX, binY))
        self.binning = [binX, binY]

    def getReadoutTime(self):
        """ get readout time in unit of S  """
        readoutTime = c_double(1)
        error = NC_api.ncCamGetReadoutTime(self.myCam.ncCam, byref(readoutTime))  # nuvu takes time unit of mS
        self._pCheckError(error)
        return readoutTime.value * 1e-3

    def setEmGain(self, emGain):
        """ set EM gain """
        error = NC_api.ncCamSetCalibratedEmGain(self.myCam.ncCam, c_long(emGain))
        self._pCheckError(error)

    def getEmGain(self):
        """ get EM gain """
        emGain = c_long(1)
        error = NC_api.ncCamGetCalibratedEmGain(self.myCam.ncCam, c_int(1), byref(emGain))
        self._pCheckError(error)
        return emGain.value

    def setWaitingTime(self, waitingTimeSet):
        """ set waiting time """
        error = NC_api.ncCamSetWaitingTime(self.myCam.ncCam, c_double(waitingTimeSet['ms']))
        self._pCheckError(error)
        print('Setting waiting time to %f ms' % waitingTimeSet['ms'])

    def getWaitingTime(self):
        """ get waiting time in unit of s """
        waitingTime = c_double(1)
        error = NC_api.ncCamGetWaitingTime(self.myCam.ncCam, c_int(1), byref(waitingTime))
        self._pCheckError(error)
        return waitingTime.value * 1e-3

    def setTargetDetectorTemp(self, targetDetectorTemp):
        """ set target detector temperature """
        error = NC_api.ncCamSetTargetDetectorTemp(self.myCam.ncCam, c_double(targetDetectorTemp))
        self._pCheckError(error)

    def getTargetDetectorTemp(self):
        """ get target detector temperature """
        targetDetectorTemp = c_double(1)
        error = NC_api.ncCamGetTargetDetectorTemp(self.myCam.ncCam, c_int(1), byref(targetDetectorTemp))
        self._pCheckError(error)
        return targetDetectorTemp.value

    def getDetectorTemp(self):
        """ get detector temperature """
        detectorTemp = c_double(1)
        error = NC_api.ncCamGetDetectorTemp(self.myCam.ncCam, byref(detectorTemp))
        self._pCheckError(error)
        return detectorTemp.value

    def getMRoiCount(self):
        """ get ROI count from camera"""
        MRoiCount = c_long(1)
        error = NC_api.ncCamGetMRoiCount(self.myCam.ncCam, byref(MRoiCount))
        self._pCheckError(error)
        return MRoiCount.value

    def getLiveFrame(self):
        nuvuImage = NCIMAGE()  # allocate memory to store a single image
        pNuvuImage = pointer(nuvuImage)
        error = NC_api.ncCamRead(self.myCam.ncCam, pNuvuImage)
        self._pCheckError(error)

        nuvuImage2 = cast(nuvuImage, POINTER(c_uint16))
        xdim, ydim = self.imageSizeX, self.imageSizeY
        # with mroi, the recorded image size of each roi is wx * (wy + 1). Here we get rid of the additional row.
        nRoi = len(self.camROIx0y0[0])
        imageArray = np.ctypeslib.as_array(nuvuImage2, shape=(xdim * (ydim + nRoi),)).copy()
        imageArray = np.reshape(imageArray, newshape=(nRoi, ydim // nRoi + 1, xdim))
        imageArray = imageArray[:, :-1, :]
        imageArray = imageArray.reshape(ydim, xdim)
        return imageArray

    def startAcquisition(self, n):
        """start acquisition with n images"""
        error = NC_api.ncCamStart(self.myCam.ncCam, c_int(n))
        self._pCheckError(error)

    def endAcquisition(self):
        error = NC_api.ncCamAbort(self.myCam.ncCam)
        self._pCheckError(error)
