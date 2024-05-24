import numpy as np

fnLUT = {}


def func_register(func):
    fnLUT[func.__name__] = func
    return func


def scaleImage(image, cameraType='pvcam', scaleFactor=None, cameraBias=None):
    if scaleFactor is None and cameraBias is None:
        if cameraType == 'pvcam':
            scaleFactor = 0.25
            cameraBias = 100
        elif cameraType == 'nuvu':
            scaleFactor = 0.02
            cameraBias = 0
        else:
            raise ValueError('Unknow camera type: {:s}'.format(cameraType))
    photonFraction = scaleFactor
    return (image.astype(int) - cameraBias) * photonFraction


@func_register
def getCounts(args):
    #     rAtom = 2 # for 3x3 pixel binning
    positions, rAtom, weights = args['positions'], args['rAtom'], args['weights']
    if 'cameraType' in args:
        image = scaleImage(args['image'], cameraType=args['cameraType'])
    else:
        image = scaleImage(args['image'], cameraType='pvcam')
    if 'bgExcludeRegion' in args.keys():
        bgExcludeRegion = args['bgExcludeRegion']
        nBgPx = image.shape[0] * image.shape[1] - (bgExcludeRegion[1][0] - bgExcludeRegion[0][0]) * (
                    bgExcludeRegion[1][1] - bgExcludeRegion[0][1])
        bgTotalCounts = np.sum(image) - np.sum(
            image[bgExcludeRegion[0][1]:bgExcludeRegion[1][1], bgExcludeRegion[0][0]:bgExcludeRegion[1][0]])
        image = image - bgTotalCounts / nBgPx
    image = image * weights
    return np.array(
        [image[p[1] - rAtom: p[1] + rAtom + 1, p[0] - rAtom: p[0] + rAtom + 1].sum() for p in
         positions])


@func_register
def getOccupancy(args):
    thresholds = args['thresholds']
    nTweezers = len(thresholds)
    counts = getCounts(args)
    atoms = np.array([counts[i] > thresholds[i] for i in range(nTweezers)]).astype(int)
    return atoms


@func_register
def doNothing(args):
    return 0


def getFn(key):
    try:
        fn = fnLUT[key]
        return fn
    except KeyError:
        print(key + ' does not exist in analysisFunctions.py')


def doFn(fn, args):
    return fn(args)
