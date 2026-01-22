from phase import phase
from labrad.units import WithUnit
import sys
sys.path.append("C:/Users/Cryo_rdyberg/Documents/Codebase/Lab_control")
from common import *
#Think of a good way to handle parameters with parameter vault
#for parameter vault, we always specify the parameters needed for the exp before the start of the exp,
#we label data in the format of (collection, data), with some data formats supported in labrad
#we want to label the data in the format of (phase, data), with the capability of scan para inside the phase as well


class imaging(phase):

    parameter_names = ['exposureDelay','imagingBeamDelay', 'exposureTime','pvCamROI','save_dir','save_params']
    external_parameter_names = [("general","nLoops")]
    

    def dophase(self, cxn, params):
        #self._setTweezerPower(cxn, params)
        #self._pulseImagingBeam(cxn, params)
        inst_lst = self._parseInstructions()
        #self._engageCamera(cxn, 0, self.tstart, 1e-4, inst_lst, "")#params['saveImages_photometrics'])
        self._engageCamera(cxn, 0, self.tstart + params['exposureDelay'], 1e-4, inst_lst, "")#params['saveImages_photometrics'])
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

 
    def getlength(self, params):
        print("getlengh")
        return (params['exposureDelay'] + params['imagingBeamDelay'] + params['exposureTime'] + params[
            'imagingBeamDelay'])*1e-3 
        

    def _initialize(self, params, cxn=None):
        for i in self.external_parameter_names:
            params[i[1]] = cxn.parametervault.get_parameter(i)
        self._waitPvcam(cxn)
        self._initCamera(params,cxn)

#run before
    def _initCamera(self, params, cxn, verbose=False):

        cxn.pvcamNuvuRfsocServer.initPvCam(params['pvCamROI'],
                                                   WithUnit(params['exposureTime'], 'ms'))
        if verbose:
            print("PvCamera configured!")
        cxn.pvcamNuvuRfsocServer.clearSequence()

#run before
    def _waitPvcam(self, cxn, verbose=False):
        imageStatus = cxn.pvcamNuvuRfsocServer.isSequenceFinished()
        imageWaitIndex = 0
        while (imageStatus == 0 or imageWaitIndex > 60):
            time.sleep(1)
            imageStatus = cxn.pvcamNuvuRfsocServer.isSequenceFinished()
            imageWaitIndex += 1
            print('wait {:.1f}s for image to finish'.format(imageWaitIndex))
        if imageStatus == False:
            raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server')
        if verbose:
            print("pvcamNuvuRfsocServer initiated and ready to rock!")

#run after
    def _setUpCameras(self,params, cxn, verbose=False):
        
        cxn.pvcamNuvuRfsocServer.acquireFastSequence(params['save_dir'],params["save_params"],int(params['nLoops']))
        #    self.prefix,
        #    getSaveName(self.params, self.params['saveParams']),
        #    self.params['nLoops'])
        #PREFIX: directory to save results

        acquistionStatus = cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
        acquistionWaitIndex = 0
        while (acquistionStatus == False or acquistionWaitIndex > 60):
            time.sleep(1)
            acquistionStatus = cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
            acquistionWaitIndex += 1
            print('wait {:.1f}s for acquistion to get ready'.format(acquistionWaitIndex))
        if acquistionStatus == False:
            raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server (acquisition)')
        if verbose:
            print("pvcamNuvuRfsocServer initiated and ready to rock!")