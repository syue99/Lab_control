
import labrad
from labrad.units import WithUnit
import time as time_m
import numpy as np
from time import localtime, strftime
from datetime import datetime
import sys
import msvcrt
sys.path.append("../servers/script_scanner/")
#from scan_experiment_1D_measure import single
from experiment import experiment

class contiunously_run_experiment(experiment):
    name = 'Test Scirpt'
    #should change the independet parameter name here
    parameter_name = "Fake Data"
    #units are in the input of the scan and measure class
    required_parameters = []
    parameter_explanation = "generated with np.random.rand"
    parameter_unit = "NA"
    def initialize(self, cxn, context, ident):
        self.navigate_data_vault(cxn, context)
        self.dv =  cxn.data_vault
        print('init')

    def run(self, cxn, context, scanvalue):
        while True:
            data = np.random.rand()
            print("random data generated: "+str(data))
        return data
        

    def run(self, cxn, context):
    #Automate the process of getting collision data
        run = True
        counter = 0
        #if reload at the beginning of the experiment
        while(run):
            try:
                time_m.sleep(1)
                counter +=1
                data = np.random.rand()
                print("press Esc to stop the program")
                print("random data generated: "+str(data))
                self.dv.add([counter, data], context=context)

                #Press Esc to exit this program 
                if msvcrt.kbhit():
                    if ord(msvcrt.getch()) == 27:
                        print('exit the experiment')
                        break

               
            except Exception as e:
                print(e)
                print("Something went wrong")
        return

    def finalize(self, cxn, context):
        print('finalize')
    


    def navigate_data_vault(self, cxn, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S", local_time)
        directory = ['', 'ScriptScanner']
        directory.extend([strftime("%Y%b%d", local_time), strftime("%H%M_%S", local_time)])
        dv.cd(directory, True, context=context)
        dv.new(dataset_name, [("time", 's')], [
               (self.parameter_name, self.parameter_explanation, self.parameter_unit)], context=context)
        dv.add_parameter('plotLive', True, context=context)



if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = contiunously_run_experiment()
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
