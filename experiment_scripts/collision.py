import labrad
from labrad.units import WithUnit
import time as time_m
import numpy as np
from time import localtime, strftime
from datetime import datetime
import sys
sys.path.append("../servers/script_scanner/")
#from scan_experiment_1D_measure import single
from experiment import experiment

class contiunously_run_experiment(experiment):
    name = 'Continouly Run an experiment'
    #should change the independet parameter name here
    parameter_name = "counts"
    parameter_explanation = "PMT ON Signal"
    parameter_unit = "kilo counts"

    required_parameters = []
    def program_main_sequence(self):
            far_detuned = 15
            doppler = 10
            self.pulser.new_sequence()
            self.pulser.add_ttl_pulse('TTL2', WithUnit(0, 'ms'), WithUnit(far_detuned, 's'))
            self.pulser.add_ttl_pulse('TTL1', WithUnit(far_detuned, 's'), WithUnit(doppler, 's'))
            for i in range(100):
                self.pulser.add_ttl_pulse('DiffCountTrigger',WithUnit(far_detuned+0.02*i, 's'),WithUnit(10.0, 'us'))
                self.pulser.add_ttl_pulse('DiffCountTrigger',WithUnit(far_detuned+0.02*(i+0.5), 's'),WithUnit(10.0, 'us'))
                self.pulser.add_ttl_pulse('866DP',WithUnit(far_detuned+0.02*i, 's'),WithUnit(10.0, 'ms'),)
                self.pulser.add_ttl_pulse('Internal866',WithUnit(far_detuned+0.02*i, 's'),WithUnit(10.0, 'ms'))
                #self.pulser.extend_sequence_length(2 * WithUnit(10.0, 'ms'),)
            self.pulser.program_sequence()
    
    def initialize(self, cxn, context, ident):
        #get start time
        start_time = datetime.now() 
        self.start_time = 1000000*start_time.month + 10000*start_time.day + 100*start_time.minute + start_time.second
        self.navigate_data_vault(cxn, context)
        try:
            self.pulser = self.cxn.pulser
            self.pulser.amplitude("422 Double Pass", WithUnit(-4,"dBm"))
            self.pmt = self.cxn.normalpmtflow
            if not self.pmt.isrunning():
                self.pmt.record_data()
            #program main sequence
            self.program_main_sequence()
            

        except Exception as e:
            print(e)
        
        print('measure init')

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

    def get_counts(self):
        count = self.pulser.get_pmt_counts()
        #print(count)
        while len(count)== 0:
            count = self.pulser.get_pmt_counts()
        return(count[0][0])
    
    def run(self, cxn, context):
    #Automate the process of getting collision data
        run = True
        reload = True
        recrystalize = 0
        reload_counter = 0
        reload_time = self.start_time
        #reload at the beginning of the experiment
        while(run):
            try:
                if reload_counter>15:
                    run = False
                self.pulser.switch_auto('TTL1')
                self.pulser.switch_auto('TTL2')
                self.pulser.start_number(1)
                time = datetime.now()
                time = 1000000*time.month + 10000*time.day + 100*time.minute + time.second
                time_diff = time - self.start_time
                reload_time_diff = time - reload_time
                #get reload
                if reload_time_diff > 60*60:
                    print("will reload in this cycle")
                    reload = True
                count = self.pmt.get_next_counts("ON",50)
                count = np.array(count)[4:]
                avg_count = np.average(count)
                #print(avg_count,count[2])
                self.pulser.wait_sequence_done()
                self.pulser.stop_sequence()
                self.pulser.switch_manual('TTL1')
                self.pulser.switch_manual('TTL2')
                print("counts from PMT during the entire cycle:"+str(avg_count))
                cxn.data_vault.add([time_diff, avg_count], context=context)
                if (avg_count < 85):
                    recrystalize += 1
                    #run = False
                else:
                    recrystalize = 0
                if reload: 
                    reload_counter +=1 
                    reload = False
                    reload_time = time                    
                    print("reloading")
                    self.pulser.output("422 Double Pass",False)
                    self.pulser.new_sequence()
                    self.pulser.add_ttl_pulse('TTL3', WithUnit(0, 'ms'), WithUnit(15, 'ms'))
                    self.pulser.program_sequence()
                    time_m.sleep(1)
                    self.pulser.output("422 Double Pass",True)
                    self.pulser.start_number(1)                    
                    self.pulser.wait_sequence_done()
                    self.pulser.stop_sequence()
                    #return to normal ttl pulse
                    self.program_main_sequence()
                    recrystalize = 3
                    self.pulser.amplitude("422 Double Pass", WithUnit(-7,"dBm"))
                    
                if recrystalize > 2:
                    recrystalize_time = 0
                    print("recrystalize")
                    #lower trap rf
                    self.pulser.amplitude("422 Double Pass", WithUnit(-7,"dBm"))
                    while recrystalize>2:
                        self.pulser.switch_auto('TTL1')
                        self.pulser.switch_auto('TTL2')
                        self.pulser.start_number(1)
                        time = datetime.now()
                        time = 1000000*time.month + 10000*time.day + 100*time.minute + time.second
                        time_diff = time - self.start_time
                        count = self.pmt.get_next_counts("ON",50)
                        count = np.array(count)[3:]
                        avg_count = np.average(count)                    
                        self.pulser.wait_sequence_done()
                        self.pulser.stop_sequence()
                        self.pulser.switch_manual('TTL1')
                        self.pulser.switch_manual('TTL2')
                        print("counts from PMT during the entire cycle:"+str(avg_count))
                        if (avg_count > 85):
                            recrystalize = 0
                        recrystalize_time += 1
                        if (recrystalize_time >10):
                            print("cannot recrystalize, try reload")
                            recrystalize = 0
                            reload = True
                    print("finish recrystalize")
                    self.pulser.amplitude("422 Double Pass", WithUnit(-4,"dBm"))                

                
            except Exception as e:
                print(e)
                print("Something went wrong")
                run = False
                self.pulser.switch_manual('TTL1')
                self.pulser.switch_manual('TTL2')
        return 
        #print(avg_count)


    def finalize(self, cxn, context):
        self.pulser.switch_manual('TTL1')
        self.pulser.switch_manual('TTL2')
        print('Experiment ends')

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = contiunously_run_experiment()
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
