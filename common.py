import copy
import itertools
import json
import os
import time
from json import JSONEncoder

import labrad
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from typing import Iterable

#import awgdispatcher as ad
#from calibrations import calibrate
#from channels import *
#from pre_experiments.trap_aligner import TrapAligner
#from pre_experiments.uv_aligner import UVAligner
#from servers.C_waveform_calculation_dll import getFileUID

import logging
import warnings
from logging.handlers import RotatingFileHandler

T = labrad.types
parentPath = r'I:/thompsonlab/AMO/Control programs/main_control_program_lite'

# Calibrations____________________________________________________________________________
# specCal = calibrate.Calibrate(parentPath + '/calibrations/blue_spectroscopy_freq_V_MHz.csv')
# specMHzToV = specCal.CalFunction2

# seedCal = calibrate.Calibrate(parentPath + '/calibrations/blue_seedlight_freq_V_MHz.csv')
# seedMHzToV = seedCal.CalFunction2

# detectCal = calibrate.Calibrate(parentPath + '/calibrations/blue_imaging_V_MHz.csv')
# blowoutMHzToV = detectCal.CalFunction2

# motMixerCal = calibrate.Calibrate(parentPath + '/calibrations/motMixer_V_mW.csv')
# MOTPDmWToV = motMixerCal.CalFunction2

# imagingMixerCal = calibrate.Calibrate(parentPath + '/calibrations/imagingMixer_V_mW.csv')
# imagingPDmWToV = imagingMixerCal.CalFunction2

# tweezerMixerCal = calibrate.Calibrate(parentPath + '/calibrations/tweezerPowerCal532_rfsoc_mW_aod_231031.csv')
# tweezerPDmWToRFSoC = tweezerMixerCal.CalFunction2

# tweezerMixerCal_slm = calibrate.Calibrate(parentPath + '/calibrations/tweezerPowerCal486_V_mW_slm.csv')
# tweezerPDmWToV_slm = tweezerMixerCal_slm.CalFunction2

# pushBeamCal = calibrate.Calibrate(parentPath + '/calibrations/pushBeam_V_mW.csv')
# pushBeamPDmWToV = pushBeamCal.CalFunction2

# redTweezerMixerCal = calibrate.Calibrate(parentPath + '/calibrations/redTweezerMixer_V_mW.csv')
# redTweezerPDmWToV = redTweezerMixerCal.CalFunction2

# sisyphusMixerCal = calibrate.Calibrate(parentPath + '/calibrations/sisyphusMixer_V_uW.csv')
# sisyphusPDuWtoV = sisyphusMixerCal.CalFunction2

# specRydbergMixerCal = calibrate.Calibrate(parentPath + '/calibrations/specDetuning_MHz_vs_Mixer_V.csv')
# specRydbergFreqMHztoMixerV = specRydbergMixerCal.CalFunction1


def flatten(items):
    """Yield items from any nested iterable; see Reference."""

    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def jsonize(param):
    return json.dumps(param, cls=NumpyArrayEncoder)


def getSaveName(params, saveParams):
    saveName = ''
    for k in saveParams:
        if type(params[k]) == bool:
            saveName += ",%s=%d" % (k, params[k])
        elif type(params[k]) == int:
            saveName += ",%s=%d" % (k, params[k])
        elif type(params[k]) == str:
            saveName += ",%s=%s" % (k, params[k])
        else:
            saveName += ",%s=%0.9f" % (k, params[k])

    return saveName[1:]  # To get rid of the extra comma at the beginning.




# We want a heirarchy of params, from lowest to highest priority:
# 1. initial params dict (lowest priority)
# 2. "global params" loaded from database (ie, calibration results)
# 3. iterlist (highest priority)
#
# In this approach, a calibration experiment can update the database and the new parameter
# will be used for subsequent experiments in the same and future runs. However, it can be overwritten
# by explicitly scanning that parameter in iterlist, which is how you would perform a new calibration
# experiment.


def update_params(params_in, globals_in, iters_in):
    """ Create a deep copy of params_in, and update it with new_params_in.
    This is so we don't have to make changes to params directly, which would have
    unwanted persistence across multiple runs.

    An alternative way to write this function would be to tell it which global params you want to
    load, and let it go and fetch them from the database server.
    """

    ret = copy.deepcopy(params_in)
    ret.update(globals_in)
    ret.update(iters_in)

    return ret


def iterparams(iterlist, itercond=lambda x: True):
    """ Iterate over all combinations of iterlist, returning a dictionary that can be used to update params and
    a list of actively scanned keys that can be used to make plots and set filenames.

    Returns:
        - idx: index of the iteration, not counting any skipped steps
        - new_params: a params dict containing entries for every key in iterlist
        - keys: a second params dict containing entries for every _scanned_ key in iterlist

    Note that keys.keys() can be used to print which things are being scanned.

    Also, care is taken to ensure that the order of keys in keys is such that the "innermost" (fast)
    scanning items occur _first_. Therefore, if you wanted to automatically generate a plot of the results
    of the experiment, you could guess that the first key in keys should be the x-axis.
    """

    all_keys = list(iterlist.keys())
    # print(iterlist.keys())
    # itertools.product scans over the _last_ argument first
    tuples = itertools.product(*iterlist.values())

    # pull out keys that we are actually iterating over
    iter_keys = [k for k, v in iterlist.items() if len(v) > 1]

    idx = 0

    for t in tuples:

        ret = {}
        ret_keys = {}

        # reversing entries ensures that we scan over the _first_ argument first
        for k, v in zip(reversed(all_keys), reversed(t)):

            ret[k] = v

            if k in iter_keys:
                ret_keys[k] = v

        if itercond(ret):
            # yield makes this into a generator -- when you iterate over the result of this function
            # it will stop here and return the value, then start again at this point the next time you
            # ask.
            yield idx, ret, ret_keys

            idx += 1
