from camera_base import ThorCam
import sys
#import server libraries
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.internet.task import LoopingCall
from labrad.server import LabradServer, setting, Signal
import time
from labrad.units import WithUnit
import numpy as np


"""
### BEGIN NODE INFO
[info]
name =  ThorCam Server
version = 1.0
description = 

### END NODE INFO
"""
SIGNALID = 331493

class ThorCamServer(LabradServer):
    """ Contains methods that interact with the Thorlab Cameras"""
    
    name = "ThorCam Server"
    onNewCount = Signal(SIGNALID, 'signal: new count', 'v')
    onNewSetting = Signal(SIGNALID+1, 'signal: new setting', '(ss)')

    @inlineCallbacks
    def initServer(self):
        #Set up parameters
        self.camid = None
        self.saveFolder = ['', 'Thorlab Camera']
        self.dataSetName = 'Camera_Data'
        #Connect to datavault
        self.dv = None
        self.openDataSet = None
        yield self.connect_data_vault()
        self.imagedata = None
        #Initialize camera
        self.camera = ThorCam()
        self.camera.start_cam_process()
        #Set up the deferredLock
        self.lock = DeferredLock()
        #Set up recording
        self.recordingInterrupted = False
        self.recording = LoopingCall(self._record)

        #Set up listeners, seems to be used to connect back if something disconnects
        self.listeners = set()
        yield self.setupListeners()


    @inlineCallbacks
    def setupListeners(self):
        yield self.client.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.client.manager.subscribe_to_named_message('Server Disconnect', 9898989+1, True)
        yield self.client.manager.addListener(listener=self.followServerConnect,
                                              source=None, ID=9898989)
        yield self.client.manager.addListener(listener=self.followServerDisconnect,
                                              source=None, ID=9898989+1)
    @inlineCallbacks
    def followServerConnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Data Vault':
            yield self.client.refresh()
            yield self.connect_data_vault()

    @inlineCallbacks
    def followServerDisconnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Data Vault':
            yield self.disconnect_data_vault()


    @inlineCallbacks
    def connect_data_vault(self):
        try:
            # reconnect to data vault and navigate to the directory
            self.dv = yield self.client.data_vault
            yield self.dv.cd(self.saveFolder, True)
            if self.openDataSet is not None:
                self.openDataSet = yield self.makeNewDataSet(self.saveFolder,
                                                             self.dataSetName)
                self.onNewSetting(('dataset', self.openDataSet))
            print('Connected: Data Vault')
        except AttributeError:
            self.dv = None
            print('Not Connected: Data Vault')

    @inlineCallbacks
    def disconnect_data_vault(self):
        print('Not Connected: Data Vault')
        self.dv = None
        yield None

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @inlineCallbacks
    def makeNewDataSet(self, folder, name):
        yield self.dv.cd(folder, True)
        ds = yield self.dv.new(name, [('t', 'num')],
                               [('KiloCounts/sec', 'Differential High', 'num')])
        self.startTime = time.time()
        yield self.addParameters(self.startTime)
        #FOR now do not connect with grapher
        """
        try:
            self.grapher = yield self.client.grapher
            self.grapher.plot(ds, 'pmt', False)
        except AttributeError:
            self.grapher = None
            print("no grapher")"""
        returnValue(name)

    @inlineCallbacks
    def addParameters(self, start):
        yield self.dv.add_parameter("Window", ["PMT Counts"])
        yield self.dv.add_parameter('plotLive', True)
        yield self.dv.add_parameter('startTime', start)
    
    #Used to return camera id using twisted
    def get_cam_id_util(self):
        self.camera.refresh_cameras()
        time.sleep(.5) 
        camid = self.camera.serials
        returnValue(camid)
    
    def get_cam_data(self):
        if self.camera.cam_playing == True:
            imagedata = self.camera.return_img()
        else:
            print("Camera not recording")
            imagedata = []
        returnValue(imagedata)
        
    @inlineCallbacks
    def _record(self):
        try:
            rawdata = yield take_shots()
        except BaseException:
            print('Not Able to Get images')
            rawdata = []
        if len(rawdata) != 0:
            toDataVault = rawdata.reshape(1080,1920)
            # converting to format [time, normal count, 0 , 0]
            try:
                yield None
                yield self.dv.save_image(toDataVault,[1080,1920],1,"test-h5",'/','.h5')
            except BaseException:
                print('Not Able to Save To Data Vault')
                
    #Problem with return value, will try to figure it out later
    @inlineCallbacks
    def dorecordData(self):
        # begins the process of data record
        # sets the collection time and mode, programs the pulser
        # if necessary and opens the dataset if necessasry
        # then starts the recording loop
        newSet = None
        self.recording.start(1)
        returnValue(newSet)
    """Not sure what does the id here means, copy from PMT, if there is a compatability issue, may
    be we should change the id"""


    '''
    Cam Settings
    '''
    @setting(0, "Open Camera", id='s', returns='')
    def openCam(self, c, id='08816'):
        return self.camera.open_camera(id)

    @setting(1, "Get Cam id",returns= '*s')
    def get_cam_id(self,c):
        """return the first id found, if more than two cameras are connected to the same computer
        this could be an issue"""
        yield self.lock.acquire()
        try:
            self.camid = yield deferToThread(self.get_cam_id_util())
        finally:
            self.lock.release()
        returnValue(self.camid)

    @setting(2, "Get Cam status",returns= 'b')
    def get_cam_status(self,c):
        return self.camera.cam_open
        
        
     
    @setting(3, "Play Camera", returns='b')
    def playCam(self, c):
        if self.camera.cam_open:
            self.camera.play_camera()
            setname = yield self.dorecordData()
            otherListeners = self.getOtherListeners(c)
            if setname is not None:
                setname = setname[1]
                self.onNewSetting(('dataset', setname), otherListeners)
            self.onNewSetting(('state', 'on'), otherListeners)
            return True
        else:
            return False

    @setting(4, "Stop Playing Camera", returns='')
    def StopplayingCam(self, c):
        self.camera.stop_playing_camera()

    @setting(5, "Get Cam playing status",returns= 'b')
    def get_cam_play_status(self,c):
        return self.camera.cam_playing
    
    @setting(6, "take shots", number='w',returns="*w")
    def take_shots(self,c,number=1):
        yield self.lock.acquire()
        try:
            self.imagedata = yield deferToThread(self.get_cam_data())
        finally:
            self.lock.release()
        returnValue(self.imagedata)
    """
    @setting(7, "get exporesure time", returns='')
    @setting(8, "set exporesure time", returns='')
    @setting(9, "get trigger mode", returns='')
    @setting(10, "set trigger mode", returns='')
    @setting(11, "get ROI", returns='')
    @setting(12, "set ROI", returns='')"""
    #This is only used to change directory of the h5 file, I am not sure if this is useful or not.
    @setting(13, 'Set Save Folder', folder='*s', returns='')
    def setSaveFolder(self, c, folder):
        yield self.dv.cd(folder, True)
        self.saveFolder = folder

    @setting(14, "Start New Dataset", setName='s', returns='s')
    def start_new_dataset(self,c, setName=None):
        """Starts new dataset, if name not provided, it will be the same."""
        if setName is not None:
            self.dataSetName = setName
        self.openDataSet = yield self.makeNewDataSet(self.saveFolder, self.dataSetName)
        otherListeners = self.getOtherListeners(c)
        self.onNewSetting(('dataset', self.openDataSet), otherListeners)
        returnValue(self.openDataSet)
    

    




if __name__ == "__main__":
    from labrad import util
    util.runServer(ThorCamServer())
