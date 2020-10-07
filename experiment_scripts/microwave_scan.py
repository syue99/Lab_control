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
#Define all experiment parameters
parameter= {
    'RFpower':WithUnit(3,'dBm'),
    'DC':WithUnit(1.5,'V'),
    'TicklingPow':WithUnit(-25,'dBm'),
    'number_of_ions':2,
    }



#scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
class scan(experiment):
    name = 'microwave'
    #should change the independet parameter name here
    parameter_name = "DDS Freq"
    #units are in the input of the scan and measure class
    required_parameters = []
    def program_main_sequence(self,scantime = 10, scanfreq = 100):
        #unit in ms
        far_detuned = 5
        doppler = 10
        self.pulser.new_sequence()
        self.pulser.add_ttl_pulse('TTL2', WithUnit(0, 'ms'), WithUnit(far_detuned, 'ms'))
        self.pulser.add_ttl_pulse('TTL1', WithUnit(0, 'ms'), WithUnit(doppler, 'ms'))
        DDS = [('1092 Double Pass', WithUnit((doppler+1), 'ms'), WithUnit(scantime, 'ms'), WithUnit(scanfreq, 'MHz'), WithUnit(-2, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB'))]
        # program DDS
        self.pulser.add_dds_pulses(DDS)
        self.pulser.add_ttl_pulse('TTL4', WithUnit(doppler+1+scantime, 'ms'), WithUnit(2, 'ms'))

        self.pulser.program_sequence()    
    def initialize(self, cxn, context, ident):
        try:
            self.pulser = self.cxn.pulser
            #self.pmt = self.cxn.normalpmtflow
            #NEED to be written somewhere else
            #self.pulser.amplitude("1092 Double Pass", WithUnit(0,"dBm"))
            #print('scanning at '+str(self.pulser.amplitude("422 Double Pass")))
        except Exception as e:
            print(e)
        print('init, set up pulser')

    def run(self, cxn, context, scanvalue):
        print('scanning at '+str(scanvalue))
        self.program_main_sequence(scanfreq = scanvalue['MHz'])
        self.pulser.switch_auto('TTL1')
        self.pulser.switch_auto('TTL2')
        self.pulser.switch_auto('TTL4')
        self.pulser.start_number(100)
        #count = self.pmt.get_next_counts("ON",270)
        #count = np.array(count)[count < 1000]
        avg_count = 100
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence() 
        #avg_count = np.average(count) 
        self.pulser.switch_manual('TTL1')
        self.pulser.switch_manual('TTL2')
        self.pulser.switch_manual('TTL4')
        print(avg_count)
        return avg_count
        


    def finalize(self, cxn, context):
        print('finalize')

  

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_experiment_1D(scan, parameter, 20, 23, 3, 'MHz')
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


