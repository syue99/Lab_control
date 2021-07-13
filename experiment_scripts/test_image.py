import numpy as np
from time import localtime, strftime
import labrad
from labrad.units import WithUnit
import sys
sys.path.append("../servers/script_scanner/")
import time
from experiment import experiment


class test_image(experiment):
    """Used to repeat an experiment multiple times."""
    parameter= {
    'RFpower':WithUnit(-16,'dBm'),
    'DC':WithUnit(1.5,'V'),
    'TicklingPow':WithUnit(-25,'dBm'),
    'number_of_ions':2,
    }
    def __init__(self):
        super(test_image, self).__init__("Test")
        


    def initialize(self, cxn, context, ident):
        self.navigate_data_vault(cxn, self.parameter, context)

    def run(self, cxn, context):
        for i in range(80):
            readout = [0 * i,1 * i ,2 * i]
            time.sleep(2.4)
            print("PMT actual readout counts:")
            print(readout)
            readout = np.array(readout)
            avg_count = np.average(readout)
            print("averaged readout counts")
            print(avg_count)
            print(' ')
            cxn.data_vault.add(readout, context=context)
        return 0
            
            
#pass array of independent and dependent as ["name","unit"]
#Revised by Fred by adding parameter
    def navigate_data_vault(self, cxn, parameter, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S", local_time)
        directory = ['ScriptScanner']
        directory.extend([strftime("%Y%b%d", local_time), strftime("%H%M_%S", local_time)])
        #need this directory to save raw_data
        for text in directory:
            self.dirc=self.dirc+text+'.dir/'
        dv.cd(directory, True, context=context)
        dv.newmatrix(dataset_name, (3,3), 'f', context=context)
        dv.add_parameter('plotLive', True, context=context)
        for para in parameter.keys():
            dv.add_parameter(para, parameter[para], context=context)


    def finalize(self, cxn, context):
        print("finalize")


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    exprt = test_image()
    ident = scanner.register_external_launch("test_image")
    exprt.execute(ident)