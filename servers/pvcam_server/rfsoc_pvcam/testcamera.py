import sys
sys.path.append("C:/Users/Cryo_rdyberg/Documents/Codebase/Lab_control")
from common import *
import labrad
class imaging():

    def __init__(self, cxn,params):
        self.kw = {}
        self.tstart = 0
        self.dophase(cxn,params)

    def dophase(self, cxn, params):
        #self._setTweezerPower(cxn, params)
        #self._pulseImagingBeam(cxn, params)
        inst_lst = self._parseInstructions()
        self._engageCamera(cxn, 0, self.tstart, 1e-4, inst_lst, "")#params['saveImages_photometrics'])
        #self._engageCamera(cxn, 0, self.tstart + params['exposureDelay'], 1e-4, inst_lst, "")#params['saveImages_photometrics'])
        #self._pauseUVLED(cxn, params)

        #self.print_checkpoint()

    def _parseInstructions(self):
        instructions = {
            'getOccupancy': {'fn': 'getOccupancy',
                             'args': {'type': 'analysis',
                                      'saveRawImage': True,
                                      'saveProcessedImage': True}
                             },
            'getCounts': {'fn': 'getCounts',
                          'args': {'type': 'analysis',
                                   'saveRawImage': True,
                                   'saveProcessedImage': True}
                          },
            'doNothing': {'fn': 'doNothing',
                          'args': {'type': 'analysis',
                                   'saveRawImage': False,
                                   'saveProcessedImage': False}
                          },
            'saveRaw': {'fn': 'doNothing',
                        'args': {'type': 'analysis',
                                 'saveRawImage': True,
                                 'saveProcessedImage': False}
                        }
        }

        if 'cmd' in self.kw:
            inst_lst = []
            if type(self.kw['cmd']) is str:
                if self.kw['cmd'] not in instructions.keys():
                    raise ValueError('Unknown analysis command! Choose from ' + str(instructions.keys()))
                inst_lst.append(instructions[self.kw['cmd']])
            elif type(self.kw['cmd']) is list:
                for this_cmd in self.kw['cmd']:
                    if this_cmd not in instructions.keys():
                        raise ValueError('Unknown analysis command! Choose from ' + str(instructions.keys()))
                    inst_lst.append(instructions[this_cmd])
        else:
            inst_lst = [instructions['doNothing']]
        return inst_lst
#self._engageCamera(cxn, pvCamTrig, self.tstart + params['exposureDelay'], 1e-4, inst_lst, params['saveImages_photometrics'])
    def _engageCamera(self, cxn, cam, t0, dt, instructions, saveImages_photometrics=True):
        cxn.finitedopulses.PulseOn(cam, t0, dt)
        if type(instructions) == dict:
            instructions = [instructions]
        elif type(instructions) is not list:
            raise ValueError('Instructions of imaging phase needs to be a list of dicts')
        #if saveImages_photometrics:
        cxn.pvcamNuvuRfsocServer.acquireImage('pvcam')
        for istr in instructions:
            cxn.pvcamNuvuRfsocServer.process(jsonize(istr))

cxn = labrad.connect()
image = imaging(cxn,"test")
print(image)
#image.dophase()