"""
### BEGIN NODE INFO
[info]
name = picoscope
version = 1.1
description = 
instancename = %LABRADNODE%_picoscope

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 947659321
timeout = 20
### END NODE INFO
"""
import h5py
import json
import numpy as np 
from labrad.units import WithUnit
from labrad.server import LabradServer
from labrad.server import setting
import os
from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import  returnValue

#from picoscope import ps3000a, ps5000a
from picoscope import ps3000a

from hardware_interface_server import HardwareInterfaceServer

from twisted.internet.defer import Deferred
from twisted.internet.reactor import callLater

def async_sleep(secs):
    d = Deferred()
    callLater(secs, d.callback, None)
    return d

class PicoscopeServer(HardwareInterfaceServer):
    """Provides access to picoscopes """
    name = 'picoscope'
    
    def refresh_available_interfaces(self):
        ps = ps3000a.PS3000a(connect=False)
        #revised by Fred as the our scopes 3020D cannot run ps.enumerateUnits()
        """try:
            serial_numbers = ps.enumerateUnits()
        except:
            serial_numbers = []"""
        #need to change here if we change devices
        serial_numbers = [b'HT423/0129']
#        try:
#            serial_numbers2 = serial_numbers + ps2.enumerateUnits()
#        except:
#            serial_numbers2 = []
        
        additions = set(serial_numbers) - set(self.interfaces.keys())
        i = 0
        for sn in additions:    
            inst = ps3000a.PS3000a(sn)
            self.interfaces[i] = inst
            i+=1
        ps.close()
#        ps2.close()

    @setting(3, channel='s', coupling='s', voltage_range='v', attenuation='i', enabled='b')
    def set_channel(self, c, channel, coupling, voltage_range, attenuation, enabled):
    #will always choose the first scope in the list by default
        ps = self.interfaces[0]
        ps.setChannel(channel, coupling=coupling, VRange=voltage_range,
            probeAttenuation=attenuation, enabled=enabled)

    @setting(4, duration='v', frequency='v')
    def set_sampling_frequency(self, c, duration, frequency):
        X = frequency
        Y = duration * frequency
        ps = self.interfaces[0]
        ans = ps.setSamplingFrequency(X, int(Y))
        print ('sampling @ {} MHz, {} damples'.format(ans[0] / Y, ans[1]))

    @setting(5, source='s', threshold='v', timeout='i')
    def set_simple_trigger(self, c, source, threshold, timeout):
        """ 
        ARGS:
            source: 'External' for external trigger
            threshold: voltage for trigger threshold
            timeout: time in ms for timeout. use negative number for infinite wait.
        """
        ps = self.interfaces[0]
        ps.setSimpleTrigger(trigSrc=source, threshold_V=threshold, timeout_ms=timeout)

    @setting(6, n_segments='i', returns='i')
    def memory_segments(self, c, n_segments):
        ps = self.interfaces[0]
        samples_per_segment = ps.memorySegments(n_segments)
        return samples_per_segment

    @setting(7, n_captures='i')
    def set_no_of_captures(self, c, n_captures):
        ps = self.interfaces[0]
        ps.setNoOfCaptures(n_captures)

    @setting(8)
    def run_block(self, c):
        ps = self.interfaces[0]
        ps.runBlock()
    
#    @setting(9, data_path='s', data_format_json='s')
#    def save_data(self, c, data_path, data_format_json):
#        """
#        ARGS:
#            data_path: (string) location of data to be saved, relative to data_dir.
#            data_format: json dumped dict
#                data_format = {
#                    channel: {
#                        segment_name: 
#                            segment_number
#                        }
#                    }
#        RETURNS:
#            None
#        """
#        ps = self.interfaces[0]
#        data_format = json.loads(data_format_json)
#        callInThread(self.do_save_data, ps, data_path, data_format)

    def do_save_data(self, ps, data_path, data_format):
        while not ps.isReady():
            sleep(0.05)
        response = {}
        data = {}
        for channel, segments in data_format.items():
            data[channel] = {name: ps.getDataV(channel, 50000, segmentIndex=num)
                for name, num in segments.items()}

#        json.dump(response, data_path, default=lambda x: x.tolist())

        data_directory = DATADIR + os.path.dirname(data_path) 
        if not os.path.exists(directory):
            os.makedirs(directory)

        with h5py.File(DATADIR + data_path) as h5f:
            for channel, segments in data.items():
                grp = h5f.create_group(channel)
                for name, data in segments.items():
                    grp.create_dataset(name, data=data, compression='gzip')

    @setting(10, data_format='s', do_wait='b')
    def get_data(self, c, data_format, do_wait=False):
        ps = self.interfaces[0]
        while not ps.isReady():
            if not do_wait:
                message = 'picoscope is not ready'
                raise Exception(message)
            else:
                yield async_sleep(0.1)

        data_format = json.loads(data_format)
        response = {}
        for channel, segments in data_format.items():
            response[channel] = {}
            for label, i in segments.items():
                response[channel][label] =  ps.getDataV(channel, 50000, segmentIndex=i)

        returnValue(json.dumps(response, default=lambda x: x.tolist()))

    #Flash LED.  Useful as a sanity check.
    @setting(11, n_flashes='i')
    def flash_led(self, c, n_flashes):
        ps = self.interfaces[0]
        ps.flashLed(n_flashes)

    #Set ADC resolution (Only does something for 5000 class picoscope)
    #Options are "8", "12", "14", "15", "16" input as a string. 
    #For 16 bit operation the picoscope can only use 1 input channel
    #For 15 bit operation, the picoscope can only use 2 input channels
    @setting(12, resolution='s')
    def set_resolution(self, c, resolution):
        ps = self.interfaces[0]
        ps.setResolution(resolution)
        
    #New Functions implemented by Fred    
    
    #Get a running average of the voltage
    @setting(13, channel='s', do_wait='b')
    def get_single_shot_data(self, c, channel = "A", do_wait=False):
        ps = self.interfaces[0]
        ps.setChannel(channel=channel, coupling="DC", VRange=20E-3)
        n_captures = 1  # int(600 * 1.4)
        sample_interval = 0.003
        sample_duration = 0.015
        ps.setSamplingInterval(sample_interval, sample_duration)
        ps.runBlock()
        ps.waitReady()

        data = ps.getDataV("A")
        return WithUnit(np.average(data),'V')
        


__server__ = PicoscopeServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)