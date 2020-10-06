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
from scan_experiment_1D_measure import scan_experiment_1D_measure
from experiment import experiment

#Define all experiment parameters
parameter= {
    'RFpower':WithUnit(3,'dBm'),
    'DC':WithUnit(1.5,'V'),
    'TicklingPow':WithUnit(-25,'dBm'),
    'number_of_ions':2,
    }



#scripts for the scanning part. For now we will send a trigger pulser of 1ms from the TTL1 chanel of the pulser once it is runned
class scan(experiment):
    name = 'tickling'
    #should change the independet parameter name here
    parameter_name = "DDS freq"
    #units are in the input of the scan and measure class
    required_parameters = []
    def initialize(self, cxn, context, ident):
        try:
            self.pulser = self.cxn.pulser
            #NEED to be written somewhere else
            self.pulser.amplitude("422 Double Pass", WithUnit(-25,"dBm"))
            print('scanning at '+str(self.pulser.amplitude("422 Double Pass")))
        except Exception as e:
            print(e)
        print('init, set up pulser')

    def run(self, cxn, context, scanvalue):
        #duration = WithUnit(50, 'ms')
        #self.pulser.new_sequence()
        #self.pulser.add_ttl_pulse('TTL1', WithUnit(0, 'ms'), WithUnit(1, 'ms'))
        #self.pulser.program_sequence()
        #self.pulser.start_number(1)
        #self.pulser.wait_sequence_done()
        #self.pulser.stop_sequence()
        #print(type(scanvalue))
        self.pulser.frequency("422 Double Pass", WithUnit(scanvalue[scanvalue.unit],"MHz"))
        print('scanning at '+str(scanvalue))

    def finalize(self, cxn, context):
        print('finalize')

#scripts for the measuring part. For now we will get a pmt reading once it is runned
class measure(experiment):
    name = 'Measuring PMT READOUTS'
    #should change the dependet parameter name here
    parameter_name = "counts"
    parameter_explanation = "PMT ON Signal"
    parameter_unit = "kilo counts"

    required_parameters = []

    def initialize(self, cxn, context, ident):
        try:
            self.pmt = self.cxn.normalpmtflow
            if not self.pmt.isrunning():
                self.pmt.record_data()
        except Exception as e:
            print(e)
        
        print('measure init')

    def run(self, cxn, context):
        try:
            count = self.pmt.get_next_counts("ON",5)
            count = np.array(count)
            avg_count = np.average(count)
            print("average counts from PMT:"+str(avg_count))
            return avg_count
        except Exception as e:
            print(e)
            return 0
        #print(avg_count)

    def finalize(self, cxn, context):
        print('measure finalize')
  

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = scan_experiment_1D_measure(scan, measure, parameter, 3.4, 3.55, 2, 'MHZ')
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)


