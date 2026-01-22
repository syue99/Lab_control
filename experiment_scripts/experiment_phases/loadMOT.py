from phase import phase
from labrad.units import WithUnit

#channel information, will combine to the same file later
#we also have the clibrate class and calibrate functions that we can integrate later
camera_trigger = 24
two_d_motAOM = 25
three_d_motAOM = 27
imgAOM = 26

class loadMOT(phase):
    parameter_names = ["MOTLoadTime","2DMOTLoadTime","MOTLoadTime_scan","MOTLoadPower_mW",'ispushBeamOn','pushBeamPower_mW','pushBeamPower_mW_scan']

    def dophase(self, cxn, params):
        print("load MOT")
        cxn.finitedopulses.PulseOn(two_d_motAOM, self.tstart, params['2DMOTLoadTime'])
        cxn.finitedopulses.PulseOn(three_d_motAOM, self.tstart+params['2DMOTLoadTime']-params['MOTLoadTime'], params['MOTLoadTime'])
        # cxn.finitedopulses.PulseOff(motProfile, self.tstart, params['MOTLoadTime'])
        # Q: What is motProflie? A: when motProfile == 1, ramp to compressed freq eg -4.8 MHz  --> -0.9 MHz
        #cxn.aoserver.setConstantVoltageTime(motMixer, WithUnit(params['MOTLoadPower_mW'], 'V'), self.tstart,
        #                                    self.tstart + params['MOTLoadTime'])
        
        #if params['ispushBeamOn']:
        #    cxn.finitedopulses.PulseOn(pbAOM, self.tstart, params['MOTLoadTime'])
        #    cxn.finitedopulses.PulseOn(pushBeamIntegratorHold, self.tstart, params['MOTLoadTime'])
        #    cxn.aoserver.setConstantVoltageTime(pushBeamAmp, WithUnit(params['pushBeamPower_mW'], 'V'),
        #                                        self.tstart, self.tstart + params['MOTLoadTime'])

        #cxn.finitedopulses.PulseOn(motBeamShutter, self.tstart, params['MOTLoadTime'])
        # cxn.finitedopulses.PulseOff(tweezerAODIntegratorHold, self.tstart, params['MOTLoadTime'] / 2.)
        # cxn.finitedopulses.PulseOn(tweezerAOMAOD, self.tstart, params['MOTLoadTime'] / 2.)

        # cxn.finitedopulses.PulseOnAndHold(tweezerAODIntegratorHold, self.tstart + params['MOTLoadTime'] / 2.)
        # cxn.finitedopulses.PulseOffAndHold(tweezerAOMAOD, self.tstart + params['MOTLoadTime'] / 2.)

    def getlength(self, params):
        return params['2DMOTLoadTime']*1e-3
