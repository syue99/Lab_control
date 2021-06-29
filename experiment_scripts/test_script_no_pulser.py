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


#Define all experiment parameters, program as {('name','labrad unit'),....}
parameter= {
    'RFpower':WithUnit(-16,'dBm'),
    'DC':WithUnit(1.5,'V'),
    'TicklingPow':WithUnit(-25,'dBm'),
    'number_of_ions':2,
    }



#scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
class scan(experiment):
    name = 'Rabi'
    parameter_name = "DDS Freq"
    required_parameters = []
    
    #you program the experimental sequence here
    #unit in ms, you will need to change the time to the correct para if you scan freq and vice versa
    def program_main_sequence(self,scantime = 2, scanfreq = 100):
        far_detuned = 5
        doppler = 0.5
        detection = 0.5
        #this is always needed if you want to start a new sequence
        #self.pulser.new_sequence()
        #you add ttl pulse by the following code: (name,start_time,duration)
        #self.pulser.add_ttl_pulse('TTL3', WithUnit(0, 'ms'), WithUnit(far_detuned, 'ms'))
        #self.pulser.add_ttl_pulse('TTL4', WithUnit(0, 'ms'), WithUnit(far_detuned, 'ms'))
        #doppler 
        #self.pulser.add_ttl_pulse('TTL2', WithUnit(far_detuned, 'ms'), WithUnit(doppler, 'ms'))
        #self.pulser.add_ttl_pulse('TTL2', WithUnit(far_detuned+doppler+scantime+0.002, 'ms'), WithUnit(detection, 'ms'))
        #you add DDS pluse by the following code: [(DDS pulse 1),(DDS pulse 2),..]
        #for DDS pulse, you program by (name,start_time,duration,freq,power,phase,ramp freq, ramp pow)
        #DDS = [('422 Double Pass', WithUnit((doppler+far_detuned), 'ms'), WithUnit(scantime, 'ms'), WithUnit(scanfreq, 'MHz'), WithUnit(-15.6, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB'))]
        # program DDS
        #self.pulser.add_dds_pulses(DDS)
        # the Readout count channel is where you program the PMT acutal counts within the set duration, in this case it will return PMT counts in the first 0.5ms of this sequence
        #self.pulser.add_ttl_pulse('ReadoutCount', WithUnit(far_detuned+doppler+scantime+0.002, 'ms'), WithUnit(detection, 'ms'))
        # you need this to compile the acutal sequence you programmed
        #self.pulser.program_sequence()
        print("programmed")
    def initialize(self, cxn, context, ident):
        print('init, set up pulser')

    def run(self, cxn, context, scanvalue):
        print('scanning at '+str(scanvalue))
        #first you compile the sequence with set frequency
        #you can program the sequence in the program_main_sequence function
        self.program_main_sequence(scanfreq = scanvalue['MHz'])
        #you set TTL channels you needed to be auto to control them 
        #self.pulser.switch_auto('TTL2')
        #self.pulser.switch_auto('TTL3')
        #self.pulser.switch_auto('TTL4')
        #you play the sequence for n times (n=10 here), i.e. number of repeatitions per scan point.
        #self.pulser.start_number(10)
        '''
        if we use readout counts, the following code can be ignored
        #you get the next 100 counts from PMT. Note here the counts is noramized counts in 0.1s 
        count = self.pmt.get_next_counts("ON",100)'''
        #you wait the sequence to be done
        #self.pulser.wait_sequence_done()
        #self.pulser.stop_sequence()
        '''
        if we use readout counts, the following code can be ignored
        #you get the counts here
        count = np.array(count)
        avg_count = np.average(count)
        print("PMT Counts:")
        print(count)'''
        #you get the readout counts, which is the actual counts 
        #you get in the set time scale in the program_main_sequence function
        #readout = self.pulser.get_readout_counts()
        readout = [0,1,2,3,4,5,6,7,8,9]
        print("PMT actual readout counts:")
        print(readout)
        readout = np.array(readout)
        avg_count = np.average(readout)
        print("averaged readout counts")
        print(avg_count)
        print(' ')
        #you switch back the TTL channels into manual
        #self.pulser.switch_manual('TTL1')
        #self.pulser.switch_manual('TTL2')
        #self.pulser.switch_manual('TTL4')
        #you return the average counts to the scan experiment class,
        #which ends in writing in the data file for this experiment in datavault
        return [avg_count,readout]
        


    def finalize(self, cxn, context):
        print('finalize')

  

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    exprt = scan_experiment_1D(scan, parameter, 165, 175, 10, 'MHz')
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


