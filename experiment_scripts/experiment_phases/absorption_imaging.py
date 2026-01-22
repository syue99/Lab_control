from phase import phase
from labrad.units import WithUnit

#THis is the first phase we are trying to implement in an actual experiment
# We want to use this script to do an absorption imaging start from scratch
# we can later change it to a phase without MOT loading


#For this first version camera is only triggered, img data does not flow back
#we can add the camera server later for completing the loop

#Think of a good way to handle parameters with parameter vault
#for parameter vault, we always specify the parameters needed for the exp before the start of the exp,
#we label data in the format of (collection, data), with some data formats supported in labrad
#we want to label the data in the format of (phase, data), with the capability of scan para inside the phase as well

#channel information, will combine to the same file later
camera_trigger = 24
two_d_motAOM = 25
three_d_motAOM = 27
repump_motAOM = 28
imgAOM = 26


#e.g. in this phase, we need the following params:
# delay time for the camera and 3D MOT cooling light?
#imagng delay: camera_delay = -0.034

# for now the camera para are currently configured in the vimba gui
# the exposure time for cam is set to be 5ms, image_time is for the img light
# Note that the imaging_delay depends on exposure time, so keep 5ms as exposure time


# bx0,by0,bz0 in WithUnit (value,V) format




class absorption_imaging(phase):
    parameter_names = ["imaging_delay","image_time"]
   
    def __init__(self,**kw):
        #print(self.required_parameters)
        super().__init__(**kw)

    def dophase(self, cxn, params):

        #we also initialize all the parameters we needed with the required unit here
        self.imaging_delay = params['imaging_delay']['s']
        self.image_time = params['image_time']['s']

        #flush the camera: For this rolling shutter CMOS we do not need it 
        #cxn.finitedopulses.PulseOn(camera_trigger, 0, 1e-5)

        #2D MOT
        cxn.finitedopulses.PulseOn(two_d_motAOM, self.tstart, 1.3999)
        #3D MOT
        
        cxn.finitedopulses.PulseOn(three_d_motAOM, self.tstart, 1.3999)
        #Repump
        cxn.finitedopulses.PulseOn(repump_motAOM, self.tstart, 1.3999)


        #first Camera with signal
        cxn.finitedopulses.PulseOn(camera_trigger, self.tstart + 1.4 + self.imaging_delay, 1e-3)
        #img light 100us 
        cxn.finitedopulses.PulseOn(imgAOM, self.tstart + 1.4, self.image_time)
        #also put rempump on
        cxn.finitedopulses.PulseOn(repump_motAOM, self.tstart + 1.4, self.image_time)

        #second Camera without MOT signal
        cxn.finitedopulses.PulseOn(camera_trigger, self.tstart + 1.5 + self.imaging_delay, 1e-5)
        #img light 100us 
        cxn.finitedopulses.PulseOn(imgAOM, self.tstart + 1.5, self.image_time)
        #also put rempump on
        cxn.finitedopulses.PulseOn(repump_motAOM, self.tstart + 1.5, self.image_time)

        #third camera shot for background
        cxn.finitedopulses.PulseOn(camera_trigger, self.tstart + 1.6 + self.imaging_delay, 1e-5)        



        #cxn.finitedopulses.PulseOn(camera_trigger, self.tstart+params['imaging_delay'], WithUnit(100,"us"))

    def getlength(self, params):
        return (1.6+ self.imaging_delay + self.image_time)
    
        