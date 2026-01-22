import json
import os
import sys
import threading
from multiprocessing import Value, Process, Manager
import time
from PyQt5 import QtWidgets
from labrad import util
from labrad.server import LabradServer, setting
from scipy.io import savemat

import sys
sys.path.append("../")#"C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/pvcam_server/rfsoc_pvcam")
from PvcamDriver import PvcamDriver
#sys.path.append("../hnu512cam")#"C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/pvcam_server/rfsoc_pvcam/hnu512cam")
#from nuvuDriver import NuvuDriver
import miscFn
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/pvcam_server/rfsoc_pvcam/GUI")
import camGUI
from tweezer_controller import *


def _startCamGUIThread(detectionParam, imgdata, newdatain, results):
    app = QtWidgets.QApplication(sys.argv)
    myGUI = camGUI.ImageGUI(detectionParam, imgdata, newdatain, results)
    sys.exit(app.exec_())


class PvcamNuvuRfsocServer(LabradServer):
    name = 'pvcamNuvuRfsocServer'

    def initServer(self):
        self.camList = ['pvcam']  # list of all cameras we have
        # We don't init cameras here as they may take a long time, but only init when needed (_initXXCamera):
        self.camDriver = {cam: None for cam in self.camList}

        self.tweezer = TweezerController()
        self.resDict = {}
        self.socket_open = 0
        self.sequenceStatus = 1
        self.acquisitionReady = 1

        # GUI parameters
        manager = Manager()
        self.globalImageData = manager.dict()
        self.newdatain = Value('i', 0)
        self.globalResults = manager.dict()
        self.detectionParam = {cam: miscFn.updateDetectionParameters(cam) for cam in self.camList}

    def _clearSequence(self):
        # Initialize the image queue and counter:
        self.imageQueue = []
        self.imageCounts = {'pvcam': 0, 'nuvu': 0}
        self.sequenceStatus = 1
        self.acquisitionReady = 1
        self.instructionDict = {'pvcam': [], 'nuvu': []}
        return None

    def _initPvCamera(self, roi, exposureTime):
        if self.camDriver['pvcam'] is None:
            self.camDriver['pvcam'] = PvcamDriver()


        self.camDriver['pvcam'].setROI(roi[0], roi[1], roi[2], roi[3])
        self.camDriver['pvcam'].setExposure(exposureTime)
        self.detectionParam['pvcam'] = miscFn.updateDetectionParameters('pvcam')

    def _initNuvuCamera(self, roiCenterList, roiSize, exposureTime, emGain, binning=None, waitingTime=0):
        """
        roiCenterList: [list of center X, list of center Y]
        roiSize: [integer wX, integer wY]
        exposureTime: float in unit of s
        emGain: integer <= 5000
        binning: [binX, binY]
        waitingTime: float in unit of s
        """
        if self.camDriver['nuvu'] is None:
            self.camDriver['nuvu'] = NuvuDriver()
        self.camDriver['nuvu'].setMROI(roiCenterList[0], roiCenterList[1], roiSize[0], roiSize[1])
        self.camDriver['nuvu'].setExposure(exposureTime)
        self.camDriver['nuvu'].setWaitingTime(waitingTime)
        self.camDriver['nuvu'].setEmGain(emGain)
        self.camDriver['nuvu'].setBinningMode(*binning)
        self.detectionParam['nuvu'] = miscFn.updateDetectionParameters('nuvu')

    @setting(10000, 'setExposure', t='v[s]')
    def setExposure(self, c, t):
        self.camDriver['nuvu'].setExposure(t)

    @setting(1, 'echo', msg='?', returns='?')
    def echo(self, c, msg):
        print(msg)
        return msg

    @setting(2, 'init_tweezer_ctrl', n_moves='i', n_row='i', n_col='i')
    def initTweezerCtrl(self, c, n_moves, n_row, n_col):
        self.tweezer.init_buffers(n_moves, n_row, n_col)

    @setting(3, 'compileMoves', returns='?')
    def compileMoves(self, c):
        self.state_data = self.tweezer.generate_tproc_states()
        return self.state_data

    @setting(4, 'uploadBuffer')
    def uploadBuffer(self, c):
        print('-' * 20)
        print('open the client socket')
        # NOTE: assumes a start_socket_server labrad call was made before this call (which resets all socket connections)
        self.tweezer.open_socket()
        # upload all buffer data via socket interface
        for state_idx, state in list(enumerate(self.tweezer.state_list))[::-1]:
            # Here we revered the state_list, because the rfsoc will automatically point at the last state uploaded to
            # it. In this way, the rfsoc will be ready to play the first at the first trigger.
            n_moves = len(state)
            self.tweezer.send_data_socket(state_idx, n_moves)
        print('buffers are uploaded')
        print('-' * 20)

    @setting(9, 'initPvCam', roi='*i', exposureTime='v[s]')
    def initPvCam(self, c, roi, exposureTime):
        self._initPvCamera(roi, exposureTime)

    @setting(10, 'initNuvuCam', roiCenterList='*2i', roiSize='*i', exposureTime='v[s]',
             emGain='i', binning='*i', waitingTime='v[s]')
    def initNuvuCam(self, c, roiCenterList, roiSize, exposureTime, emGain, binning=None, waitingTime=0):
        self._initNuvuCamera(roiCenterList, roiSize, exposureTime, emGain, binning, waitingTime)

    @setting(11, 'clearSequence')
    def clearSequence(self, c):
        self._clearSequence()

    @setting(12, 'acquireFastSequence', fileDirectory='s', fileName='s', nLoops='i')
    def acquireFastSequence(self, c, fileDirectory, fileName, nLoops):
        self.acquireThread = threading.Thread(target=self._runThread,
                                              kwargs={
                                                  'fileDirectory': fileDirectory,
                                                  'fileName': fileName,
                                                  'nLoops': nLoops,
                                              }
                                              )
        self.sequenceStatus = 0
        self.acquisitionReady = 0

        self.acquireThread.start()

    @setting(14, 'acquireImage', cameraType='s')
    def acquireImage(self, c, cameraType):
        """
        The function is called acquireImage, but it only appends an image in the queue and keep track of how many images
        the experiment is expected to acquire.

        cameraType: 'pvcam' or 'nuvu'.
        """
        self.imageQueue.append(cameraType)
        self.imageCounts[cameraType] += 1

    @setting(15, 'process', parametersStr='s')
    def process(self, c, parametersStr):
        """
        This function is the only portal for the control program to communicate with the pvcam server (Jeff's idea),
        which has the role of doing everything including trap movement, real time image processing, or even just idling.
        There are currently three types of functions (upto Oct 27, 2023): 'fixedAOD', 'realTimeAOD', 'analysis'.
        """
        instruction = json.loads(parametersStr)
        args = instruction['args']
        fnName = instruction['fn']
        fn = miscFn.loadFn(fnName, args['type'])
        args.update({'tweezer_ctrl': self.tweezer})

        if args['type'] == 'fixedAOD':
            fn(args)

        elif args['type'] in ['realTimeAOD', 'analysis']:
            cameraType = self.imageQueue[-1]  # The last image in the queue, either 'pvcam' or 'nuvu'.
            imageIndex = self.imageCounts[cameraType] - 1  # Specify when this function gets executed.
            args.update(self.detectionParam[cameraType])
            if args['type'] == 'realTimeAOD':
                args.update({'tweezer_ctrl': self.tweezer})
                state_idx, move_indices = self.tweezer.allocate_blank_moves(args['nMovesRequired'])
                args.update({
                    'move_start_idx': move_indices[0],
                    'state_idx': state_idx,
                })
            if imageIndex == len(self.instructionDict[cameraType]):
                self.instructionDict[cameraType].append([])
            self.instructionDict[cameraType][imageIndex].append([fn, args, fnName])
        else:
            raise KeyError('Unknown type of function: ' + str(args['type']))

    @setting(21, 'isSequenceFinished')
    def isSequenceFinished(self, c):
        return self.sequenceStatus

    @setting(33, 'isAcquisitionReady')
    def isAcquisitionReady(self, c):
        return self.acquisitionReady

    def _runThread(self, nLoops, fileDirectory, fileName):
        print('Start image acquisition.')
        # self.sequenceStatus = 0
        # self.acquisitionReady = 0

        self.processedImageData = {}
        self.rawImageData = {}

        camRequired = np.unique(self.imageQueue)  # A list of cameras used in this experiment
        imagesPerLoop = len(self.imageQueue)
        totalImagesCamWise = {cam: self.imageCounts[cam] * nLoops for cam in camRequired}

        stack = {}
        for cam in camRequired:
            self.camDriver[cam].startAcquisition(totalImagesCamWise[cam])
            stack[cam] = np.zeros((totalImagesCamWise[cam],
                                   self.camDriver[cam].imageSizeY, self.camDriver[cam].imageSizeX), dtype=np.uint16)

        self.resDict = {'pvcam': {}, 'nuvu': {}}
        print('Ready to acquire images.')
        self.acquisitionReady = 1
        #print(self.imageQueue)
        for numLoop in range(nLoops):

            imageCounterCamWise = {cam: 0 for cam in camRequired}
            for imageIndex, cameraType in enumerate(self.imageQueue):
                print('Getting image from '+ cameraType)
                print(self.instructionDict[cameraType])
                imageIndexCam = imageCounterCamWise[cameraType]
                self.resDict[cameraType][imageIndexCam] = {}
                instructions = self.instructionDict[cameraType][imageIndexCam]
                # t0 = time.time()
                rawImage = self.camDriver[cameraType].getLiveFrame()
                # print('get a frame from {:s}'.format(cameraType))
                args_cmb = {}  # In case the first image doesn't have instructions.
                saveRawImageFlag = False
                for j, inst in enumerate(instructions):
                    fn, args, fnName = inst
                    args_cmb = args.copy()
                    args_cmb.update({'image': rawImage, 'currentResultDict': self.resDict})
                    res = {fnName: fn(args_cmb)}
                    self.resDict[cameraType][imageIndexCam].update(res)
                    if 'saveRawImage' in args_cmb and args_cmb['saveRawImage']:
                        saveRawImageFlag = True
                # print('time: {:.2f} ms'.format((time.time()-t0)*1e3))
                if saveRawImageFlag:
                    stack[cameraType][numLoop * self.imageCounts[cameraType] + imageIndexCam] = rawImage
                imageCounterCamWise[cameraType] += 1
            ###@@@commented by FRED for saving time    
            # tTrans1 = time.time()
            # self.globalImageData.clear()
            # self.globalImageData.update({cam: stack[cam][(numLoop * self.imageCounts[cam]):(
            #                 numLoop * self.imageCounts[cam] + self.imageCounts[cam])] for cam in camRequired})
            # self.globalResults.clear()
            # self.globalResults.update(self.resDict)
            # self.globalResults.update({'runNumber': os.path.normpath(fileDirectory).split(os.path.sep)[-1]})
            # self.globalResults.update({'fileName': fileName})
            # self.globalResults.update({'imageQueue': self.imageQueue})
            # self.newdatain.value = 1
            # print('Tranfer data to GUI takes {:.5f} s'.format(time.time()-tTrans1))
            print('Executed ' + str(os.path.normpath(fileDirectory).split(os.path.sep)[-1]) +
                  ', Loop #' + str(numLoop) + '...')

        for cam in camRequired:
            #print(stack[cam])
            print(os.path.join(fileDirectory, cam, fileName + '.mat'))
            savemat(os.path.join(fileDirectory, cam, fileName + '.mat'), {'stack': stack[cam]}, do_compression=True)

        # for cam in camRequired:
        #     print(stack[cam])
        #     print(os.path.join(fileDirectory, cam, fileName + '.npz'))
            
        #     np.savez_compressed(
        #         os.path.join(fileDirectory, cam, fileName + '.npz'),
        #         stack=stack[cam]
        #     )

        print('Done saving.')
        self.sequenceStatus = 1
        for cam in camRequired:
            self.camDriver[cam].endAcquisition()

    @setting(31, 'startCamGUI')
    def startCamGUI(self, c):
        p = Process(target=_startCamGUIThread, args=(self.detectionParam,
                                                     self.globalImageData, self.newdatain,
                                                     self.globalResults))
        p.start()

    @setting(32, 'driverExec', cam='s', fn='s', args='s')
    def driverExec(self, c, cam, fn, args='null'):
        camDriver = self.camDriver[cam]
        args = json.loads(args)
        if args is None:
            args = {}
        myFn = getattr(camDriver, fn, None)
        return myFn(**args)


__server__ = PvcamNuvuRfsocServer()

if __name__ == '__main__':
    util.runServer(__server__)
