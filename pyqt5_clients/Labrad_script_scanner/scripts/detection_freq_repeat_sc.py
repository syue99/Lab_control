import labrad
from labrad.units import WithUnit
import time
import numpy as np
import sys

#sys.path.append("../servers/script_scanner/")
from repeat_reload import repeat_reload
from experiment import experiment
from twisted.internet.threads import deferToThread
import msvcrt
from plot_sequence import SequencePlotter
from ZZKY_utils import save_analyze_imgs, start_camera, start_live
from time import sleep


# Global variables in this script:


repetitions_every_point = 5  # No. of repeatitions when scanning every point

# Check and change the following parameters before doing an experiment

# Choose what to scan
# TODO: Add suopport for scanning phase

#Time in ms
pump1 = 6.01
pump2 = 6.01
doppler = 6

microwave_pi_time = 1#1


DDS_wait_time1 = 0.01
DDS_wait_time2 = 0.01
detection = 0.2 # 1ms . no too long . avoid far detuned population




# Define all experiment parameters, program as {('name','labrad unit'),....}


# scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
class scan(experiment):
    name = 'DetectionRepeat'
    parameter_name = "Detection Freq"
    required_parameters = [('cam_roi', 'height'),
                           ('cam_roi', 'start_x'),
                           ('cam_roi', 'start_y'),
                           ('cam_roi', 'width'),
                           ('cam_roi', 'mcp_gain'),
                           ('Cooling', 'detection_freq'),
                           ('Cooling', 'pump1_freq'),
                           ('Cooling', 'pump2_freq'),
                           ('Cooling', 'detection_pwr'),
                           ('Cooling', 'pump1_pwr'),
                           ('Cooling', 'pump2_pwr'),
                           ('scan_use_pmt', 'USEPMT')]
    USEPMT = False

    cam_var = {
        'identify_exposure': WithUnit(1, 'ms'),
        'initial_exposure': WithUnit(50, 'ms'),
        'initial_mcp_gain': 3200,
        'mcp_gain': 4000,
        'start_x': 1,
        'width': 1600,  # don't change this value
        'start_y': 689,
        'height': 80,
        'horizontalBinning': 1,
        'verticalBinning': 1,
        'kinetic_number': repetitions_every_point,
        'counter': 0,
        'USEPMT': USEPMT
    }

    # Note the following function is used to load parameters from pv
    # This is needed for all experiments that needs to use parameter vault
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = list(parameters)
        return parameters

    # you program the experimental sequence here for DDS and TTL
    # the logic here is to pack all the TTL/DDS command sequences of scanning 1 point together and send to FPGA on pulser

    # unit in ms, you will need to change the time to the correct para if you scan freq and vice versa
    def program_main_sequence(self):
        # We set up these values in the registry
        detect_freq = self.parameters.Cooling.detection_freq
        pump1_freq = self.parameters.Cooling.pump1_freq
        pump2_freq = self.parameters.Cooling.pump2_freq
        doppler_amp = self.parameters.Cooling.detection_pwr
        pump1_amp = self.parameters.Cooling.pump1_pwr
        pump2_amp = self.parameters.Cooling.pump2_pwr

        period1_start_at = 0.5
        #doppler_cooling_at = period1_start_at + pump1 + DDS_wait_time1
        #microwave_start_at = period1_start_at + pump1 + DDS_wait_time1
        #detection_start_at = microwave_start_at + scantime + DDS_wait_time2
        detection_start_at = period1_start_at + pump1 + DDS_wait_time1
        # this is always needed if you want to start a new sequence
        self.pulser.new_sequence()

        self.pulser.add_ttl_pulse('ReadoutCount', WithUnit(detection_start_at, 'ms'),
                                  WithUnit(detection, 'ms'))

        self.pulser.add_ttl_pulse('TTL1', WithUnit(detection_start_at, 'ms'), WithUnit(50, 'us'))

        # you add DDS pluse by the following code: [(DDS pulse 1),(DDS pulse 2),..]
        # for DDS pulse, you program by (name,start_time,duration,freq,power,phase,ramp freq, ramp pow)

        DDS = [
            # pump1
            ('Pump1 AOM', WithUnit(period1_start_at, 'ms'), WithUnit(pump1, 'ms'),
             WithUnit(pump1_freq, 'MHz'), WithUnit(pump1_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
             WithUnit(0, 'dB')),
            # pump2
            ('Pump2 AOM', WithUnit(period1_start_at, 'ms'), WithUnit(pump2, 'ms'),
             WithUnit(pump2_freq, 'MHz'), WithUnit(pump2_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
             WithUnit(0, 'dB')),
            # doppler
            ('Doppler AOM', WithUnit(period1_start_at, 'ms'), WithUnit(doppler, 'ms'),
             WithUnit(detect_freq - 4.5, 'MHz'), WithUnit(doppler_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
             WithUnit(0, 'dB')),

            # microwave
            #('Microwave', WithUnit(microwave_start_at, 'ms'), WithUnit(scantime, 'ms'),
            # WithUnit(scanfreq, 'MHz'), WithUnit(microwave_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
            # WithUnit(0, 'dB')),
            # detection
            ('Doppler AOM', WithUnit(detection_start_at, 'ms'), WithUnit(detection, 'ms'),
             WithUnit(detect_freq, 'MHz'), WithUnit(doppler_amp-2, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
             WithUnit(0, 'dB'))
        ]
        # program DDS
        self.pulser.add_dds_pulses(DDS)
        # you need this to compile the acutal sequence you programmed
        self.pulser.program_sequence()

    def initialize(self, cxn, context, ident):
        try:
            self.pulser = self.cxn.pulser
            self.pmt = self.cxn.normalpmtflow
            self.dv = self.cxn.data_vault
            self.cam = self.cxn.ZZKYServer
        except Exception as e:
            print(e)
        # refresh pv
        self.pv = self.cxn.parametervault
        self.pv.reload_parameters()
        self.USEPMT = self.parameters.scan_use_pmt.USEPMT
        self.cam_var['start_x'] = int(self.parameters.cam_roi.start_x)
        print(self.cam_var['start_x'])
        self.cam_var['start_y'] = int(self.parameters.cam_roi.start_y)
        print(self.cam_var['start_y'])
        self.cam_var['width'] = int(self.parameters.cam_roi.width)
        print(self.cam_var['width'])
        self.cam_var['height'] = int(self.parameters.cam_roi.height)
        print(self.cam_var['height'])
        self.cam_var['mcp_gain'] = int(self.parameters.cam_roi.mcp_gain)
        print(self.cam_var['mcp_gain'])
        self.cam_var['USEPMT'] = self.USEPMT
        print(self.cam_var['USEPMT'])
        # Initialize AWG for microwave
        # note awg chanel 3 is tied with microwave

        if self.USEPMT == False:
            start_camera(self.cam, self.cam_var)

        print('init, set up pulser')

    def run(self, cxn, context):
        # this is used for stop the experiment with esc key
        if msvcrt.kbhit():
            if ord(msvcrt.getch()) == 27:
                print('exit the experiment')
                self.should_stop = True
        #print('scanning at ' + str(scanvalue))

        # you can program the sequence in the program_main_sequence function
        #if scan_var == 'freq':
            # we need to reconfigure AWG here:
            # print(scanvalue)
            #self.program_main_sequence(scanfreq=scanvalue['MHz'], scantime=Scan_time['ms'])
        #elif scan_var == 'time':
            # we need to reconfigure AWG here:
            #self.program_main_sequence(scanfreq=Scan_freq['MHz'], scantime=scanvalue['ms'])

        self.program_main_sequence()

        if self.USEPMT == False:
            self.cam.start_sequence(
                r"C:\Users\Administrator\Desktop\Lab_control-Development\servers\control_instrument_servers\ZhongzhikeyiCam\test_tiff\test_helloworld.tiff",
                5)
            self.pulser.start_number(8)
        elif self.USEPMT == True:
            self.pulser.start_number(1)

        # you play the sequence for n times (n=100 here), i.e. number of repeatitions per scan point.
        #self.pulser.start_number(1)

        # you wait the sequence to be done
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence()

        sleep(0.1)
        if self.USEPMT == False:
            self.cam.camera_stop()

        sleep(0.01)

        if self.USEPMT == True:
            readout = self.pulser.get_readout_counts()
            print(readout)
            # save_analyze_imgs(self.cam, self.cam_var, self.dirc)

        else:
            readout, avg_image = save_analyze_imgs(self.cam, self.cam_var, self.dirc)
            #print(readout)
            count = np.array(readout)  # [readout>15]
            avg_count = np.average(count)
            #readout = avg_count / (self.cam_var['width'] * self.cam_var['height'])
            readout = avg_count / self.cam_var['width'] / repetitions_every_point
            readout = np.floor(readout)
            readout = int(readout)
            print(readout)

        #count = np.array(readout)  # [readout>15]
        #avg_count = np.average(count)
        #avg_image = []


        #return [avg_count, readout, avg_image]

        #return [avg_count, readout]
        return readout

    def finalize(self, cxn, context):
        if self.USEPMT == False:
            start_live(self.cam, self.cam_var)
        print('finalize')


#if __name__ == '__main__':
 #   cxn = labrad.connect()
 #   scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
 #   exprt = repeat_reload(scan, repetitions_every_point, True)
 #   ident = scanner.register_external_launch(exprt.name)
 #   exprt.execute(ident)