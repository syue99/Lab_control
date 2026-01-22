import ctypes
import time
import numpy as np
import pandas as pd


import csv, math, os, sys, copy, random, json
from numpy import asarray, savetxt
from scipy.optimize import curve_fit
from scipy.integrate import quad
from scipy.io import loadmat



from numba import njit
from line_profiler import LineProfiler

####### image single tweezer with camera
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import imageio


import labrad
from labrad.units import WithUnit
from json import JSONEncoder

def _parseInstructions():
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
    inst_lst = [instructions['saveRaw']]
    return inst_lst

#self._engageCamera(cxn, pvCamTrig, self.tstart + params['exposureDelay'], 1e-4, inst_lst, params['saveImages_photometrics'])
def _engageCamera(cxn, cam, t0, dt, instructions, saveImages_photometrics=True):
    cxn.finitedopulses.PulseOn(cam, t0, dt)
    if type(instructions) == dict:
        instructions = [instructions]
    elif type(instructions) is not list:
        raise ValueError('Instructions of imaging phase needs to be a list of dicts')
    #if saveImages_photometrics:
    cxn.pvcamNuvuRfsocServer.acquireImage('pvcam')
    for istr in instructions:
        cxn.pvcamNuvuRfsocServer.process(jsonize(istr))

    


#run before
# def _initCamera(params, cxn, verbose=False):

#     cxn.pvcamNuvuRfsocServer.initPvCam(params['pvCamROI'],
#                                                 WithUnit(params['exposureTime'], 'ms'))
#     if verbose:
#         print("PvCamera configured!")
#     cxn.pvcamNuvuRfsocServer.clearSequence()

# #run before
# def _waitPvcam(cxn, verbose=False):
#     imageStatus = cxn.pvcamNuvuRfsocServer.isSequenceFinished()
#     imageWaitIndex = 0
#     #while (imageStatus == 0 or imageWaitIndex > 60):
#     while (imageStatus == 0 and imageWaitIndex < 60):
#         time.sleep(1)
#         imageStatus = cxn.pvcamNuvuRfsocServer.isSequenceFinished()
#         imageWaitIndex += 1
#         print('wait {:.1f}s for image to finish'.format(imageWaitIndex))
#     if imageStatus == False:
#         raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server')
#     if verbose:
#         print("pvcamNuvuRfsocServer initiated and ready to rock!")

#run after
# def _setUpCameras(params, cxn, verbose=False):
    
#     cxn.pvcamNuvuRfsocServer.acquireFastSequence(params['save_dir'],params["save_params"],int(params['nLoops']))
#     #    self.prefix,
#     #    getSaveName(self.params, self.params['saveParams']),
#     #    self.params['nLoops'])
#     #PREFIX: directory to save results

#     acquistionStatus = cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
#     acquistionWaitIndex = 0
#     while (acquistionStatus == False or acquistionWaitIndex > 60):
#         time.sleep(1)
#         acquistionStatus = cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
#         acquistionWaitIndex += 1
#         print('wait {:.1f}s for acquistion to get ready'.format(acquistionWaitIndex))
#     if acquistionStatus == False:
#         raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server (acquisition)')
#     if verbose:
#         print("pvcamNuvuRfsocServer initiated and ready to rock!")


#     #cxn.finitedopulses.PulseOn(cam, t0, dt)
#     if type(instructions) == dict:
#         instructions = [instructions]
#     elif type(instructions) is not list:
#         raise ValueError('Instructions of imaging phase needs to be a list of dicts')
#     #if saveImages_photometrics:
#     cxn.pvcamNuvuRfsocServer.acquireImage('pvcam')
#     for istr in instructions:
#         cxn.pvcamNuvuRfsocServer.process(jsonize(istr))

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def jsonize(param):
    return json.dumps(param, cls=NumpyArrayEncoder)

