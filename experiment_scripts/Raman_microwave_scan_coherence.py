"""
### BEGIN EXPERIMENT INFO
[info]
name = scan and measure example
load_into_scriptscanner = False
allow_concurrent = []
### END EXPERIMENT INFO
"""

import labrad
from labrad.units import WithUnit
import time
import numpy as np
import sys
sys.path.append("../servers/script_scanner/")
from scan_experiment_1D import scan_experiment_1D
from experiment import experiment
from twisted.internet.threads import deferToThread
import msvcrt


scan_var = 'time'
#scan_var = 'freq'


Scan_points = 60
repetitions_every_point=50

if scan_var == 'time':
    Scan_points = 60
    Rabi_scan_time_start=WithUnit(0.0,'ms')
    Rabi_scan_time_end=WithUnit(0.3,'ms')
    Scan_freq=WithUnit(202.045,'MHz')
    parameter= {
    'Scan_time_start':Rabi_scan_time_start,
    'Scan_time_end':Rabi_scan_time_end,
    'Scan_freq':Scan_freq,
    'Scan_points':Scan_points,
    'repetition at every point':repetitions_every_point,
    'Raw_data_column_0':"scan freq",
    "Raw_data_column_1-9":"RAW PMT Counts in 1ms with detection"
    }

if scan_var == 'freq':
    Scan_points = 60
    Scan_freq_start = WithUnit(201.9,'MHz')
    Scan_freq_end = WithUnit(202.15,'MHz')
    Rabi_scan_time = WithUnit(0.02,'ms')
    parameter= {
    'Scan_freq_start':Scan_freq_start,
    'Scan_freq_end':Scan_freq_end,
    'Rabi_scan_time':Rabi_scan_time,
    'Scan_points':Scan_points,
    'repetition at every point':repetitions_every_point,
    'Raw_data_column_0':"scan freq",
    "Raw_data_column_1-9":"RAW PMT Counts in 1ms with detection"
    }

#Define all experiment parameters, program as {('name','labrad unit'),....}



















#scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
class microwave_scan(experiment):
    name = 'MicrowaveRabiScan'
    parameter_name = "DDS Freq"
    required_parameters = [('collection1', 'ramp_time'),
    ]
    USEPMT = False
    
    cam_var = {
            'identify_exposure': WithUnit(1, 'ms'),
            'start_x' : 901,
            'stop_x' : 1100,
            'start_y' : 50,
            'stop_y' : 65,
            'horizontalBinning' : 1,
            'verticalBinning' : 16,
            'kinetic_number' : repetitions_every_point,
            'counter': 0,
            'USEPMT' : USEPMT
        }
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters )
        parameters = list(parameters)
        return parameters
    
    #you program the experimental sequence here
    #unit in ms, you will need to change the time to the correct para if you scan freq and vice versa
    def program_main_sequence(self, scanfreq, scantime):
        far_detuned = 5
        doppler = 0.5
        detection = 0.5
        DDS_delay = 0.00172
        detection_freq = 142
        microwave_pi_2 = 0.01
        raman_pi_2 = 0.00212/2+DDS_delay
        repumper_pumping_freq = detection_freq*2 - 120.6-1
        far_detuned_puming_freq = 270.7 -detection_freq+1
        
        scantime = scantime + DDS_delay
        #this is always needed if you want to start a new sequence
        self.pulser.new_sequence()
        # the Readout count channel is where you program the PMT acutal counts within the set duration, in this case it will return PMT counts in the first 0.5ms of this sequence
        self.pulser.add_ttl_pulse('ReadoutCount', WithUnit(far_detuned+0.55+scantime+0.05, 'ms'), WithUnit(detection, 'ms'))
        self.pulser.add_ttl_pulse('TTL6', WithUnit(far_detuned+scantime+1, 'ms'), WithUnit(0.5, 'ms'))
        
        
        #add TTL for the AWG: for the scanning, need 500ns for the 
        self.pulser.add_ttl_pulse('TTL3', WithUnit(far_detuned+0.55, 'ms'), WithUnit(microwave_pi_2, 'ms'))
        #self.pulser.add_ttl_pulse('TTL3', WithUnit(far_detuned+0.55+microwave_pi_2+scantime, 'ms'), WithUnit(microwave_pi_2, 'ms'))
        #you add DDS pluse by the following code: [(DDS pulse 1),(DDS pulse 2),..]
        #for DDS pulse, you program by (name,start_time,duration,freq,power,phase,ramp freq, ramp pow)
        DDS = [
        #far_detuned/repumper Cooling
        ('DDS7', WithUnit(0.001, 'ms'), WithUnit(far_detuned, 'ms'), WithUnit(repumper_pumping_freq, 'MHz'), WithUnit(-3.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS8', WithUnit(0.001, 'ms'), WithUnit(far_detuned, 'ms'), WithUnit(far_detuned_puming_freq, 'MHz'), WithUnit(-3.6, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #Doppler Cooling
        ('DDS6', WithUnit((-doppler+far_detuned+0.2), 'ms'), WithUnit(doppler, 'ms'), WithUnit(detection_freq-4.5, 'MHz'), WithUnit(-14.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS6', WithUnit((far_detuned+0.25), 'ms'), WithUnit(0.05, 'ms'), WithUnit(detection_freq-4.5, 'MHz'), WithUnit(-16.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS6', WithUnit((far_detuned+0.3), 'ms'), WithUnit(0.1, 'ms'), WithUnit(detection_freq-4.5, 'MHz'), WithUnit(-18.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS6', WithUnit((far_detuned+0.4), 'ms'), WithUnit(0.1, 'ms'), WithUnit(detection_freq-4.5, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #Optical pumping
        ('DDS7', WithUnit(far_detuned+0.5, 'ms'), WithUnit(3, 'us'), WithUnit(repumper_pumping_freq, 'MHz'), WithUnit(-16.5, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS8', WithUnit(far_detuned+0.5, 'ms'), WithUnit(3, 'us'), WithUnit(far_detuned_puming_freq, 'MHz'), WithUnit(-13.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #Microwave is here, but we will use TTL3 to trigger the window in this time period
        ('DDS2', WithUnit(far_detuned+0.55+microwave_pi_2+scantime, 'ms'), WithUnit(raman_pi_2, 'ms'), WithUnit(340, 'MHz'), WithUnit(-3.9, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS3', WithUnit(far_detuned+0.55+microwave_pi_2+scantime, 'ms'), WithUnit(raman_pi_2, 'ms'), WithUnit(220, 'MHz'), WithUnit(-5.6, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS4', WithUnit(far_detuned+0.55+microwave_pi_2+scantime, 'ms'), WithUnit(raman_pi_2, 'ms'), WithUnit(125.04, 'MHz'), WithUnit(-18, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        ('DDS1', WithUnit(far_detuned+0.55+microwave_pi_2+scantime, 'ms'), WithUnit(raman_pi_2, 'ms'), WithUnit(166.5, 'MHz'), WithUnit(-5.6, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #detection
        ('DDS6', WithUnit((far_detuned+0.55+scantime+0.05), 'ms'), WithUnit(detection, 'ms'), WithUnit(detection_freq, 'MHz'), WithUnit(-12.7, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB'))]
        # program DDS
        self.pulser.add_dds_pulses(DDS)
        # you need this to compile the acutal sequence you programmed
        self.pulser.program_sequence()    
    def initialize(self, cxn, context, ident):
        try:
            self.pulser = self.cxn.pulser
            self.pmt = self.cxn.normalpmtflow
            self.awg = self.cxn.keysight_awg
        except Exception as e:
            print(e)
        self.awg.amplitude(3,WithUnit(1.49,"V"))
        self.pulser.switch_manual('TTL3',False)
        self.pulser.switch_auto('TTL3')
        print('init, set up pulser')

    def run(self, cxn, context, scanvalue):
        if msvcrt.kbhit():
            if ord(msvcrt.getch()) == 27:
                print('exit the experiment')
                self.should_stop = True
        print('scanning at '+str(scanvalue))
        #first you compile the sequence with set frequency
       
        #you can program the sequence in the program_main_sequence function
        if scan_var == 'freq':
            #we need to reconfigure AWG here:
            self.awg.frequency(3,scanvalue)
            self.program_main_sequence(scanfreq = scanvalue['MHz'],scantime=Rabi_scan_time['ms'])
        elif scan_var == 'time':
            #we need to reconfigure AWG here:
            self.awg.frequency(3,Scan_freq)
            self.program_main_sequence(scanfreq= Scan_freq['MHz'], scantime = scanvalue['ms'])
        #you set TTL channels you needed to be auto to control them 
        self.pulser.switch_auto('TTL2')
        self.pulser.switch_auto('TTL3')
        #you play the sequence for n times (n=10 here), i.e. number of repeatitions per scan point.
        self.pulser.start_number(repetitions_every_point)
        '''
        if we use readout counts, the following code can be ignored
        #you get the next 100 counts from PMT. Note here the counts is noramized counts in 0.1s 
        count = self.pmt.get_next_counts("ON",100)'''
        #you wait the sequence to be done
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence()
        '''
        if we use readout counts, the following code can be ignored
        #you get the counts here
        count = np.array(count)
        avg_count = np.average(count)
        print("PMT Counts:")
        print(count)'''
        #you get the readout counts, which is the actual counts 
        #you get in the set time scale in the program_main_sequence function
        readout = self.pulser.get_readout_counts()
        print("PMT actual readout counts:")
        print(readout)
        readout = np.array(readout)
        count = np.copy(readout)
        
        #count[count<=3]=0
        #count[count>3]=1
        #print(count)
        avg_count = np.average(count)
        print("averaged readout counts")
        print(avg_count)
        print(' ')
        #you switch back the TTL channels into manual
        self.pulser.switch_manual('TTL1')
        self.pulser.switch_manual('TTL2')
        self.pulser.switch_manual('TTL3')
        #you return the average counts to the scan experiment class,
        #which ends in writing in the data file for this experiment in datavault
        dis_data = avg_count
        raw_data = readout
        return [dis_data,raw_data]
        


    def finalize(self, cxn, context):
        print('finalize')

  

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    if scan_var=='freq':
        exprt = scan_experiment_1D(scan, parameter, Scan_freq_start['MHz'], Scan_freq_end['MHz'], Scan_points, 'MHz')
    elif scan_var=='time':
        exprt = scan_experiment_1D(scan, parameter, Rabi_scan_time_start['ms'], Rabi_scan_time_end['ms'], Scan_points, 'ms')
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


