from phase import phase
from labrad.units import WithUnit

#channel information, will combine to the same file later
#we also have the clibrate class and calibrate functions that we can integrate later
motAOM = 1
motEOM = 2
motMixer = 2
pbAOM = 3
pushBeamIntegratorHold = 4
pushBeamAmp = 2
motBeamShutter = 5

class loadMOT(phase):
    parameter_names = ["MOTLoadTime","MOTLoadTime_scan","MOTLoadPower_mW",'ispushBeamOn','pushBeamPower_mW','pushBeamPower_mW_scan']

    def dophase(self, cxn, params):
        print("load MOT")
        cxn.finitedopulses.PulseOn(motAOM, self.tstart, params['MOTLoadTime'])
        cxn.finitedopulses.PulseOn(motEOM, self.tstart, params['MOTLoadTime'])
        # cxn.finitedopulses.PulseOff(motProfile, self.tstart, params['MOTLoadTime'])
        # Q: What is motProflie? A: when motProfile == 1, ramp to compressed freq eg -4.8 MHz  --> -0.9 MHz
        cxn.aoserver.setConstantVoltageTime(motMixer, WithUnit(params['MOTLoadPower_mW'], 'V'), self.tstart,
                                            self.tstart + params['MOTLoadTime'])
        
        if params['ispushBeamOn']:
            cxn.finitedopulses.PulseOn(pbAOM, self.tstart, params['MOTLoadTime'])
            cxn.finitedopulses.PulseOn(pushBeamIntegratorHold, self.tstart, params['MOTLoadTime'])
            cxn.aoserver.setConstantVoltageTime(pushBeamAmp, WithUnit(params['pushBeamPower_mW'], 'V'),
                                                self.tstart, self.tstart + params['MOTLoadTime'])

        cxn.finitedopulses.PulseOn(motBeamShutter, self.tstart, params['MOTLoadTime'])
        # cxn.finitedopulses.PulseOff(tweezerAODIntegratorHold, self.tstart, params['MOTLoadTime'] / 2.)
        # cxn.finitedopulses.PulseOn(tweezerAOMAOD, self.tstart, params['MOTLoadTime'] / 2.)

        # cxn.finitedopulses.PulseOnAndHold(tweezerAODIntegratorHold, self.tstart + params['MOTLoadTime'] / 2.)
        # cxn.finitedopulses.PulseOffAndHold(tweezerAOMAOD, self.tstart + params['MOTLoadTime'] / 2.)

    def getlength(self, params):
        return params['MOTLoadTime']
