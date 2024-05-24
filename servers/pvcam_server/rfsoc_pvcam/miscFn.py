import glob
import json
import os
from json import JSONEncoder

import numpy as np


def flatten(addressList):
    output = []
    for addr in addressList:
        output += list(addr)
    return output


def loadFn(fnKey, fnType):
    if fnType == 'analysis':
        exec(open('analysisFunctions.py').read(), globals())
        return getFn(fnKey)
    elif fnType == 'realTimeAOD':
        exec(open('realTimeAODFunctions.py').read(), globals())
        return getFn(fnKey)
    elif fnType == 'fixedAOD':
        exec(open('fixedAODFunctions.py').read(), globals())
        return getFn(fnKey)


def runFn(fn, args):
    print(args['type'])
    if args['type'] == 'analysis':
        res = fn(args)
        return res
    elif args['type'] == 'realTimeAOD':
        fn(args)
        return [0]
    elif args['type'] == 'fixedAOD':
        res = fn(args)
        return res


def getDurations(fn, args):
    duration = fn(args)
    return duration


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def updateDetectionParameters(cameraType):
    if cameraType == 'pvcam':
        """
        list_of_files = glob.glob(
            r'I:/thompsonlab/AMO/Control programs/calibrationData/556ImagingThresholds/*')
        # "*" means all, if one needs specific format then use "*.csv".
        latest_file = max(list_of_files, key=os.path.getctime)
        dat = np.load(latest_file)
        print('Loading new pvcam tweezer threshold: ' + latest_file.split('\\')[-1])"""
        dat = {'positions': [[((i*2)%10)*3, ((i*2)//10)*3] for i in range(88)], 'thresholds': [10]*88, 'bgExcludeRegion': [[((i*2)%10)*3, ((i*2)//10)*3] for i in range(88)]} #Change by Fred by letting it running

    elif cameraType == 'nuvu':
        dat = {'positions': [[((i*2)%10)*3, ((i*2)//10)*3] for i in range(88)], 'thresholds': [10]*88}  # FIXME: add analysis parameters for the NUVU camera
    else:
        raise ValueError('Unknown camera type: ' + str(cameraType))
    return dict(dat)


def jsonize(param):
    return json.dumps(param, cls=NumpyArrayEncoder)
