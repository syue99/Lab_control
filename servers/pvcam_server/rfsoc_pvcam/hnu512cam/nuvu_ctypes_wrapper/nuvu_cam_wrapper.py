# file: nuvu_cam_wrapper.py
# author: Guillaume Allain
# date: 28/04/18
# desc: Wrapper that englobes every methods we would like to use with the
#       nuvu. Essentially inherit most of the method from nc_camera but
#       wraps them in an easily readable class that add methods for init
#       and use of the camera

from .nc_camera import *
import numpy as np
import time

class Nuvu_wrapper_error(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Nuvu_cam_wrapper(nc_camera):
    def __init__(self, targetDetectorTemp=-35, readoutMode=1, binning=1,
                 exposureTime=0.75, fps=250):
        super().__init__()
        self.__fps = fps
        self.openCam(nbBuff=4)
        self.setReadoutMode(readoutMode)
        self.getCurrentReadoutMode()
        self.setSquareBinning(binning)
        self.camInit()
        self.set_target_detector_temp(targetDetectorTemp)
        self.change_exposure_time(exposureTime)
        self.isrunning = False
        # self.setTimeout(self.exposureTime.value + self.waitingTime.value
        #                 + self.readoutTime.value + 500.0)
        self.setTimeout(1000)
        self.isrunning = False
    #Deactivated disconnect_if_error
    def disconnect_if_error(f):
        """Decorator that disconnect the camera if the method fails"""
        def func(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # args[0].closeCam()
                # print('Successfull emergency disconnect of Nuvu Camera')
                raise e from None
        return func

    @property
    def real_fps(self):
        return self.__real_fps

    @disconnect_if_error
    def millisecond_to_fps(self,arg):
        return 1/(arg/1000)

    @disconnect_if_error
    def fps_to_millisecond(self,arg):
        return (1/arg)*1000

    @disconnect_if_error
    def set_fps(self,fps):
        current_exp_time = self.exposureTime.value
        current_read_time = self.readoutTime.value
        self.setWaitingTime(self.fps_to_millisecond(fps)
                            - current_exp_time
                            - current_read_time)
        self.getWaitingTime()
        self.__real_fps = self.millisecond_to_fps(self.exposureTime.value
                                                  + self.waitingTime.value
                                                  + self.readoutTime.value)

    @disconnect_if_error
    def change_exposure_time(self, new_exposure_time):
        if new_exposure_time >= (self.fps_to_millisecond(self.__fps)
                                -self.readoutTime.value):
            raise Nuvu_wrapper_error("Exposure time too large, change FPS first")
        self.setExposureTime(new_exposure_time)
        self.getExposureTime()
        self.getReadoutTime()
        self.set_fps(self.__fps)

    @disconnect_if_error
    def set_calibrated_em_gain(self, new_em_gain):
        super(Nuvu_cam_wrapper, self).setCalibratedEmGain(new_em_gain)
        super(Nuvu_cam_wrapper, self).getCalibratedEmGain()

    def get_calibrated_em_gain(self):
        return self.calibratedEmGain.value

    @disconnect_if_error
    def change_fps(self, new_fps):
        if self.fps_to_millisecond(new_fps) <= (self.exposureTime.value
                                               + self.readoutTime.value):
            raise Nuvu_wrapper_error("FPS to small, change exposure time first")
        self.set_fps(new_fps)

    @disconnect_if_error
    def get_image64(self):
        #get directly 64bit image
        return self.get_image().astype(np.float64)

    @disconnect_if_error
    def get_image(self):
        #get a uint16 image
        self.flushReadQueue()
        return self.getImg()

    @disconnect_if_error
    def get_bias(self):
        exposure_old = self.exposureTime.value
        self.setExposureTime(0)
        time.sleep(0.1)
        img = self.get_image()
        self.setExposureTime(exposure_old)
        self.getExposureTime()
        return img

    @disconnect_if_error
    def get_bias64(self):
        return self.get_bias().astype(np.float64)

    @disconnect_if_error
    def camStart(self):
        super(Nuvu_cam_wrapper,self).camStart()
        self.isrunning = True

    @disconnect_if_error
    def camStop(self):
        self.camAbort()
        self.isrunning = False

    @disconnect_if_error
    def get_component_temp(self,component):
        """
        Méthode qui récupère la température du composant spécifié et la
        stoque dans la valeur associée
        :param comp: identifiant du composant. 0=CCD, 1=controleur,
        2=powerSupply, 3=FGPA, 4=heatSink
        :return: None
        """
        super(Nuvu_cam_wrapper, self).getComponentTemp(component)
        values = [self.detectorTemp,self.controllerTemp,self.powerSupplyTemp, self.fpgaTemp,self.heatsinkTemp]
        return values[component].value

    @disconnect_if_error
    def get_ccd_temp(self):
        '''Récupère et retourne la valeur de température du CCD'''
        return self.get_component_temp(0)

    @disconnect_if_error
    def set_target_detector_temp(self,target):
        self.setTargetDetectorTemp(target)
        self.getTargetDetectorTemp()

    def get_target_detector_temp(self):
        return self.targetDetectorTemp.value


if __name__ == '__main__':
    pass
