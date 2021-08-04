"""
### BEGIN NODE INFO
[info]
name = Keysight AWG Server
version = 1.0
description = AWG server 
instancename = keysight_awg

[startup]
cmdline = %PYTHON% %FILE%
timeout = 40

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from labrad.server import LabradServer
from labrad.server import setting
import labrad.units as _u
import numpy as _np

import sys 
try:
    sys.path.append('C:\Program Files\Keysight\SD1\Libraries\Python') 
    import keysightSD1
except:
    print("No keysight API found, plz install SD1 software or check the directory")

sys.path.append('../../../config/awg/')

from awgConfiguration import hardwareConfiguration


SERVERNAME = 'keysight_awg'



class keysightAWGServer(LabradServer):
    """Server for arbitrary function generator using the keysight awg."""
    name = SERVERNAME

    def initServer(self):
        model = hardwareConfiguration.model
        chassis = hardwareConfiguration.chassis
        slot = hardwareConfiguration.slot
        self.awg=keysightSD1.SD_AOU()
        moduleID = self.awg.openWithSlot(model, chassis, slot)
        if moduleID >0:
            print("connected to AWG with module ID: "+str(moduleID))
        else:
            print("could not connect to AWG, check the Error code: "+ str(moduleID))

    @setting(1, "Amplitude", channel='w', amplitude='v[V]', returns='')
    def amplitude(self, c, channel=None, amplitude=None):
        """Gets or sets the amplitude of the named channel or the selected channel."""
        if abs(amplitude["V"]) < hardwareConfiguration.channel_amp_thres[channel-1]:
            self.awg.channelAmplitude(channel, amplitude["V"])
        else:
            print("the amp is bigger than the set threshold")

    @setting(2, "Frequency", channel='w', freq='v[MHz]', returns='')
    def frequency(self, c, channel=None, freq=None):
        """Gets or sets the frequency of the named channel or the selected channel."""
        self.awg.channelFrequency(channel, freq["Hz"])
    
    @setting(3, "Phase", channel='w', phase='v[deg]', returns='')
    def phase(self, c, channel=None, phase=None):
        """Gets or sets the phase of the named channel or the selected channel."""
        self.awg.channelPhase(channel, phase["deg"])

    @setting(4, "AWG Play from File", channel='w', file='s', returns='')
    def awg_play_from_file(self, c, channel=None, file=None):
        """Play the named channel or the selected channel with AWG file input."""
        self.awg.channelWaveShape(channel, 6)
        file = 'waveform/'+file
        self.awg.AWGFromFile(channel, file, triggerMode=0, startDelay=0, cycles=0, prescaler=None, paddingMode = 0)
        
    @setting(5, "AWG stop", channel='w', returns='')
    def awg_stop(self, c, channel=None):
        """Stop playing the AWG sequence."""
        self.awg.AWGstop(channel)  
        self.awg.channelWaveShape(channel, 1)
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(keysightAWGServer())
