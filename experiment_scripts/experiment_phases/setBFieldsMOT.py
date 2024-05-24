from phase import phase
from labrad.units import WithUnit

#Think of a good way to handle parameters with parameter vault
#for parameter vault, we always specify the parameters needed for the exp before the start of the exp,
#we label data in the format of (collection, data), with some data formats supported in labrad
#we want to label the data in the format of (phase, data), with the capability of scan para inside the phase as well


#e.g. in this phase, we need the following params:
#bx0,by0,bz0 in WithUnit (value,V) format

class setBFieldsMOT(phase):
    parameter_names = ['bx0','by0', 'bz0']
    
    def __init__(self,**kw):
        #print(self.required_parameters)
        super().__init__(**kw)


    def dophase(self, cxn, params):
        '''
        set Biased B fields
        '''
        cxn.aoserver.setConstantVoltage(0,  WithUnit(params["bx0"],"V"))
        cxn.aoserver.setConstantVoltage(1,  WithUnit(params["by0"],"V"))
        cxn.aoserver.setConstantVoltage(2,  WithUnit(params["bz0"],"V"))

    def getlength(self, params):
        return 0.0
    
        