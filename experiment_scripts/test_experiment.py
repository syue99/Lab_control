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
#sys.path.append("../pyqt5_clients/Labrad_script_scanner/script_scanner/")

from scan_experiment_1D import scan_experiment_1D
from single_sequence import single_sequence
from experiment import experiment
from twisted.internet.threads import deferToThread
import msvcrt


###Avaliable varaibles to scan:
#e.g. time1(doppler cooling time), time2(mot loading time), freq(doppler cooling freq), etc... 
#we will need to at least view it in the GUI and change it in script
#better if we can change it in GUI
#med-high priority for 2D scan

scan_var = 'time'
#scan_var = 'freq'


Scan_points = 60
repetitions_every_point=10

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
    def program_main_sequence(self, scanvalue=0 ):
        #self.TTL.pulseon(0,0,scanvalue)
        #self.TTL.pulseon(0,0,1e-6)
        for counter in range(3):
            self.TTL.pulseon(0,(1+counter )*1e-4, 1e-6)
            self.TTL.pulseon(1,counter *2e-5, 1e-5)
            self.TTL.pulseon(2,counter *1e-5+1e-5, 1e-6 )
        self.TTL.pulseon(1,2e-4,4e-4)
        #print("Newexp1")

        self.ao.setvoltagepulse(2,0,1e-4,WithUnit(2,"V"))
        self.ao.setvoltagepulse(2,2e-4,4e-4,WithUnit(5,"V"))
        self.ao.setVoltagePulse(1,2e-5,1e-4,WithUnit(1.5,"V"))
        self.ao.setVoltagePulse(0,2e-5,1e-4,WithUnit(2,"V"))
    def initialize(self, cxn, context, ident):
        try:
            self.TTL = self.cxn.finitedopulses
            self.ao = self.cxn.aoserver
            self.TTL.blankwaveform(10e-4)
            self.ao.blankwaveform(10e-4)
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
            self.program_main_sequence(scanvalue = scanvalue['s'])
        #print(repetitions_every_point)
        self.ao.runwaveform(10)
        self.TTL.runwaveform(10)
        
        self._loopWhileRunWaveform()
        return [0,0]
        
        

    def _loopWhileRunWaveform(self):
        scanTime = 0.1
        time_start = time.time()
        runCounter = -1
        while (time.time() - time_start) < (scanTime + 0.1):
            pass
                
    def finalize(self, cxn, context):
        print('finalize')

  

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    if scan_var=='time':
        exprt = scan_experiment_1D(NIcard_scan, parameter, scan_time_start['ms'], scan_time_end['ms'], Scan_points, 'ms')
    else:
        exprt = single_sequence(NIcard_scan)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


