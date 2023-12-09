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
    Scan_points = 10
    scan_time_start=WithUnit(0.0,'ms')
    scan_time_end=WithUnit(0.3,'ms')
    parameter= {
    'Scan_time_start':scan_time_start,
    'Scan_time_end':scan_time_end,
    'Scan_points':Scan_points,
    'repetition at every point':repetitions_every_point,
    'Raw_data_column_0':"scan freq",
    "Raw_data_column_1-9":"RAW PMT Counts in 1ms with detection"
    }


#Define all experiment parameters, program as {('name','labrad unit'),....}






#scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
#A test script for NICARD SCAN
class NIcard_scan(experiment):
    name = 'test_experiment'
    parameter_name = "NI_Card_TTL0"
    required_parameters = [('collection1', 'ramp_time'),('collection1', 'scan_time')]
    USEPMT = False
    
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters )
        parameters = list(parameters)
        print(cls.required_parameters)
        return parameters
    
    #you program the experimental sequence here
    #unit in ms, you will need to change the time to the correct para if you scan freq and vice versa
    def program_main_sequence(self, scantime ):
        self.TTL.pulseon(0,0,scantime)

    def initialize(self, cxn, context, ident):
        try:
            self.TTL = self.cxn.finitedopulses
        except Exception as e:
            print(e)
        print('init, set up pulser')

    def run(self, cxn, context, scanvalue):
        if msvcrt.kbhit():
            if ord(msvcrt.getch()) == 27:
                print('exit the experiment')
                self.should_stop = True
        print('scanning at '+str(scanvalue))
        #first you compile the sequence with set frequency
       
        #you can program the sequence in the program_main_sequence function

        if scan_var == 'time':
            self.program_main_sequence(scantime = scanvalue['s'])

        self.TTL.runwaveform(repetitions_every_point)

        return [0,0]
        


    def finalize(self, cxn, context):
        print('finalize')

  

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    if scan_var=='time':
        exprt = scan_experiment_1D(NIcard_scan, parameter, scan_time_start['ms'], scan_time_end['ms'], Scan_points, 'ms')
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


