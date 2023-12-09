import labrad
from labrad.units import WithUnit
import time
import numpy as np
import sys
from ZZKY_utils import save_analyze_imgs, start_camera, start_live
#sys.path.append("../servers/script_scanner/")
from scan_experiment_1D_camera import scan_experiment_1D_camera
from experiment import experiment
from twisted.internet.threads import deferToThread
import msvcrt
from time import sleep
from plot_sequence import SequencePlotter
#from ZZKY_utils import save_analyze_imgs


# Global variables in this script:

repetitions_every_point = 100 # No. of repeatitions when scanning every point

# Check and change the following parameters before doing an experiment

# Choose what to scan
# TODO: Add suopport for scanning phase
scan_var = 'time'
scan_var = 'freq'


# Freq in MHz
#pump1_freq = 162
#pump2_freq = 119
#detect_freq = 143

#microwave_freq = 67.961
#Power in dBm
#pump1_amp = -12.0
#pump2_amp = -12.0
#doppler_amp = -12
#microwave_amp = -25


#-5

#Time in ms
pump1 = 6.01
pump2 = 6.01
doppler = 6
#microwave_pi_time = 0.1409  #0.19


DDS_wait_time1 = 0.01
DDS_wait_time2 = 0.01
detection = 0.2
# 1ms . no too long . avoid far detuned population



# the following parameters are used when you scan time/freq respectively




# Define all experiment parameters, program as {('name','labrad unit'),....}


# scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
class scan(experiment):
    name = 'MicrowaveRepumpScan'
    parameter_name = "DDS Freq"
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
                           ('Microwave', 'mw_resonance_freq'),
                           ('Microwave', 'mw_pi_time'),
                           ('Microwave', 'mw_pwr'),
                           ('Microwave', 'mw_repump_resonance_freq'),
                           ('Microwave', 'mw_repump_detuning'),
                           ('Microwave', 'mw_repump_pi_time'),
                           ('Microwave', 'mw_repump_scanfreq'),
                           ('Microwave', 'mw_repump_scantime'),
                           ('Microwave', 'scan_use_detuning'),
                           ('scan_use_pmt', 'USEPMT')
                           ]
    USEPMT = False
    continue_flag = False

    cam_var = {
        'identify_exposure': WithUnit(1, 'ms'),
        'initial_exposure': WithUnit(50, 'ms'),
        'initial_mcp_gain': 3200,
        'mcp_gain': 4000,
        'start_x': 1,
        'width': 1600,   #don't change this value
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

    def program_camera_start_sequence(self):
        # We set up these values in the registry

        period1_start_at = 0.5 #0.5
        # this is always needed if you want to start a new sequence
        self.pulser.new_sequence()


        self.pulser.add_ttl_pulse('TTL1', WithUnit(period1_start_at, 'ms'), WithUnit(50, 'us'))

        # you need this to compile the acutal sequence you programmed
        self.pulser.program_sequence()



    # unit in ms, you will need to change the time to the correct para if you scan freq and vice versa
    def program_main_sequence(self, scanfreq, scantime):
        # We set up these values in the registry
        detect_freq = self.parameters.Cooling.detection_freq
        pump1_freq = self.parameters.Cooling.pump1_freq
        pump2_freq = self.parameters.Cooling.pump2_freq
        doppler_amp = self.parameters.Cooling.detection_pwr
        pump1_amp = self.parameters.Cooling.pump1_pwr
        pump2_amp = self.parameters.Cooling.pump2_pwr
        microwave_amp = self.parameters.Microwave.mw_pwr
        microwave_pi_time = self.parameters.Microwave.mw_pi_time
        microwave_freq = self.parameters.Microwave.mw_resonance_freq
        microwave_hyperfine_amp = self.parameters.Microwave.mw_pwr

        period1_start_at = 2
        microwave1_start_at = period1_start_at + pump1 + DDS_wait_time1
        microwave_repump_start = microwave1_start_at + microwave_pi_time + DDS_wait_time2
        microwave2_start_at = microwave_repump_start + scantime + DDS_wait_time2
        detection_start_at = microwave2_start_at + microwave_pi_time + DDS_wait_time2
        # this is always needed if you want to start a new sequence
        self.pulser.new_sequence()

        self.pulser.add_ttl_pulse('ReadoutCount', WithUnit(detection_start_at, 'ms'),
                                  WithUnit(detection, 'ms'))

        # self.pulser.add_ttl_pulse('TTL1', WithUnit(period1_start_at, 'ms'), WithUnit(50, 'us'))

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
            # pump1

            # microwave_zeeman
            ('Microwave', WithUnit(microwave1_start_at, 'ms'), WithUnit(microwave_pi_time, 'ms'),
             WithUnit(microwave_freq, 'MHz'), WithUnit(microwave_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
             WithUnit(0, 'dB')),
            # microwave_repump
            ('Microwave', WithUnit(microwave_repump_start, 'ms'), WithUnit(scantime, 'ms'),
             WithUnit(scanfreq, 'MHz'), WithUnit(microwave_hyperfine_amp, 'dBm'), WithUnit(0.0, 'deg'),
             WithUnit(0, 'MHz'),
             WithUnit(0, 'dB')),
            ('Microwave', WithUnit(microwave2_start_at, 'ms'), WithUnit(microwave_pi_time, 'ms'),
             WithUnit(microwave_freq, 'MHz'), WithUnit(microwave_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
             WithUnit(0, 'dB')),
            # detection
            ('Doppler AOM', WithUnit(detection_start_at, 'ms'), WithUnit(detection, 'ms'),
             WithUnit(detect_freq, 'MHz'), WithUnit(doppler_amp, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),
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
        #self.cam_var = {
         #   'identify_exposure': WithUnit(1, 'ms'),
         #   'initial_exposure': WithUnit(50, 'ms'),
         #   'initial_mcp_gain': 3200,
         #   'start_x': self.parameters.cam_roi.start_x,
         #   'width': self.parameters.cam_roi.width,  # don't change this value
         #   'start_y': self.parameters.cam_roi.start_y,
         #   'height': self.parameters.cam_roi.height,
         #   'horizontalBinning': 1,
         #   'verticalBinning': 1,
         #   'kinetic_number': repetitions_every_point,
         #   'counter': 0,
         #   'USEPMT': self.USEPMT
        #}
        if self.USEPMT == False:
            start_camera(self.cam, self.cam_var)
        #self.cam.connect_to_camera()
        #self.cam.start_camera(r"C:\Users\Administrator\Desktop\Lab_control-Development\servers\control_instrument_servers\ZhongzhikeyiCam\test_tiff\test_hellowold.tiff")
        #self.cam.camera_disconnect()
        # Initialize AWG for microwave
        # note awg chanel 3 is tied with microwave

        print('init, set up pulser')

    def run(self, cxn, context, scanvalue, units):
        # this is used for stop the experiment with esc key
        usedetuning = self.parameters.Microwave.scan_use_detuning
        if usedetuning:
            detuning = self.parameters.Microwave.mw_repump_detuning
            Scan_Freq = self.parameters.Microwave.mw_repump_resonance_freq - detuning
        else:
            Scan_Freq = self.parameters.Microwave.mw_repump_resonance_freq
        Scan_Time = self.parameters.Microwave.mw_repump_pi_time

        if msvcrt.kbhit():
            if ord(msvcrt.getch()) == 27:
                print('exit the experiment')
                self.should_stop = True

        print('scanning at ' + str(scanvalue))

        #self.cam.start_camera(r"C:\Users\Administrator\Desktop\Lab_control-Development\servers\control_instrument_servers\ZhongzhikeyiCam\test_tiff\test_hellowold.tiff")

        #self.program_camera_start_sequence()
        #self.pulser.start_number(1)
        #self.pulser.wait_sequence_done()
        #self.pulser.stop_sequence()
        if self.continue_flag:
            start_camera(self.cam, self.cam_var)
            print("continue_flag")
            self.continue_flag = False


        # you can program the sequence in the program_main_sequence function
        if units == 'MHz':
            # we need to reconfigure AWG here:
            # print(scanvalue)
            self.program_main_sequence(scanfreq=scanvalue['MHz'], scantime=Scan_Time)
        elif units == 'ms':
            # we need to reconfigure AWG here:
            self.program_main_sequence(scanfreq=Scan_Freq, scantime=scanvalue['ms'])

        if self.USEPMT == False:
            self.cam.start_sequence(
                r"C:\Users\Administrator\Desktop\Lab_control-Development\servers\control_instrument_servers\ZhongzhikeyiCam\test_tiff\test_helloworld.tiff",
                repetitions_every_point-5)
        #self.cam.start_camera(r"C:\Users\Administrator\Desktop\Lab_control-Development\servers\control_instrument_servers\ZhongzhikeyiCam\test_tiff\test_hellowold.tiff")
        # you play the sequence for n times (n=100 here), i.e. number of repeatitions per scan point.
        self.pulser.start_number(repetitions_every_point)

        # you wait the sequence to be done
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence()

        sleep(0.1)
        if self.USEPMT == False:
            self.cam.camera_stop()

        sleep(0.01)

        if self.USEPMT == True:
            readout = self.pulser.get_readout_counts()
            count = np.array(readout)  # [readout>15]
            avg_count = np.average(count)
            #print(count)
            return [avg_count, readout]
            #save_analyze_imgs(self.cam, self.cam_var, self.dirc)

        else:
            readout, avg_image = save_analyze_imgs(self.cam, self.cam_var, self.dirc)
            print(readout)
            count = np.array(readout)  # [readout>15]
            avg_count = np.average(count)
            return [avg_count, readout, avg_image]


        #self.cam.start_camera(r"C:\Users\Administrator\Desktop\Lab_control-Development\servers\control_instrument_servers\ZhongzhikeyiCam\test_tiff\test_hellowold.tiff")
        '''
        readout, avg_image = save_analyze_imgs(self.cam, self.cam_var, self.dirc)
        # print(readout)
        count = np.array(readout)  # [readout>15]
        avg_count = np.average(count)

        readout = self.pulser.get_readout_counts()
        count = np.array(readout)  # [readout>15]
        avg_count = np.average(count)
        avg_image = []
        '''

        #return [avg_count, readout, avg_image]

        #return [avg_count, readout]
        #return [avg_count, readout, avg_image]

    def finalize(self, cxn, context):
        #self.cam.camera_disconnect()
        if self.USEPMT == False:
            start_live(self.cam, self.cam_var)
        print('finalize')


#if __name__ == '__main__':
 #   cxn = labrad.connect()
 #   scanner = cxn.scriptscanner

    ###: you set the scan freqeuncy and data points needed here
 #   if scan_var == 'freq':
 #       exprt = scan_experiment_1D_camera(scan, parameter, Scan_freq_start['MHz'], Scan_freq_end['MHz'], Scan_points, 'MHz')
 #   elif scan_var == 'time':
 #       exprt = scan_experiment_1D_camera(scan, parameter, scan_time_start['ms'], scan_time_end['ms'], Scan_points, 'ms')
 #   ident = scanner.register_external_launch(exprt.name)
 #   exprt.execute(ident)
