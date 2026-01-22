import sys

from pyvcam import pvc
from pyvcam.camera import Camera
import pyvcam.constants as const
#sys.path.append("C://Users/Cryo_rdyberg/.conda/envs/code3/lib/site-packages/pyvcam-2.1.5-py3.6-win-amd64.egg/pyvcam/")
#import pvcam_constants as const


class PvcamDriver:
    def __init__(self):
        pvc.init_pvcam()  # Initialize PVCAM
        self.cam = next(Camera.detect_camera())  # Use generator to find first camera.
        self.cam.open()

        #set up the mode information. currently hardcoded
        #change trigger to exp mode
        #internal trigger
        #edge trigger
        self.cam.exp_mode = 'Edge Trigger'  # 'Ext Trig Edge Rising'
        #0 sensitivity
        #1 speed
        #2 dynmaic
        self.cam.readout_port = 0#3#0

        self.cam.exp_out_mode = 'First Row'
        self.cam.exp_time = int(10)
        #FRED: DO NOT SET SPEED INDEX
        #Our model seems only have 1 index 0 and and set it to 1 will crash the camera
        #1000MHz also sounds fishy
        #self.cam.speed_table_index = 1  # 100MHz 12 bit
        #self.cam.gain = 2  # CMS mode

        # self.cam.speed_table_index = 0
        # self.cam.gain = 2

        # Turn off all postprocessing functions
        for i in range(self.cam.get_param(const.PARAM_PP_INDEX, const.ATTR_MAX) + 1):
            self.cam.set_param(const.PARAM_PP_INDEX, i)
            pName = self.cam.get_param(const.PARAM_PP_FEAT_NAME)

            self.cam.set_param(const.PARAM_PP_PARAM_INDEX, 0)
            aName = self.cam.get_param(const.PARAM_PP_PARAM_NAME)

            self.cam.set_param(const.PARAM_PP_PARAM, 0)

    def setExposure(self, exposure):
        """ set exposure time """
        self.cam.exp_time = int(exposure['ms'])

    def setROI(self, x0, y0, wx, wy):
        # self.cam.roi = (int(x0 - wx), int(x0 + wx), int(y0 - wy), int(y0 + wy))
        self.cam.reset_rois()
        self.cam.set_roi(int(x0), int(y0), int(wx), int(wy))
        self.imageSizeX = wx
        self.imageSizeY = wy

    def startAcquisition(self, dummyN):
        """
        The dummyN here is to align with the function structure for the startAcquisition function for the nuvuDriver.
        Don't delete it!
        """
        self.cam.start_live()

    def getLiveFrame(self):
        frame, fps, frame_count = self.cam.poll_frame(timeout_ms=20000)
        img = frame['pixel_data']
        return img

    def endAcquisition(self):
        self.cam.finish()
