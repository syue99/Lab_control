import numpy as np
from time import localtime, strftime
from labrad.units import WithUnit
from experiment import experiment


class scan_experiment_1D(experiment):
    """Used to repeat an experiment multiple times."""

    def __init__(self, script_cls, parameter, minim, maxim, steps, units):
        self.script_cls = script_cls
        self.parameter = parameter
        self.units = units
        self.scan_points = np.linspace(minim, maxim, steps)
        self.scan_points = [WithUnit(pt, units) for pt in self.scan_points]
        scan_name = self.name_format(script_cls.name)
        super(scan_experiment_1D, self).__init__(scan_name)
        
    def name_format(self, scan_name):
    #Revised by Fred
        return 'Scanning {0} in {1}'.format(
            self.script_cls.parameter_name, scan_name)


    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
        self.navigate_data_vault(cxn, self.parameter, context)

    def run(self, cxn, context):
        for i, scan_value in enumerate(self.scan_points):
            if self.pause_or_stop():
                return
            #changed by Fred, only a sketchy fix, need to be fixed later
            self.script.set_parameters({('para1',"para2"): scan_value})
            self.script.set_progress_limits(
                100.0 * i / len(self.scan_points), 100.0 * (i + 1) / len(self.scan_points))
            result = self.script.run(cxn, context, scan_value)
            if self.script.should_stop:
                return
            if result is not None:
                #revised by Fred to add the feature of storing raw data
                #For now raw data is handled without going to the data_vault
                #When the image data is handled properly, we should also add raw data into the image class
                #the logic now is that result=[plotresult,raw] for plotresult=int/float, raw=np array
                #if the result=plotresult, then nothing changed
                if str(type(result))=="<class 'list'>":
                    result[1] = np.insert(result[1],0,scan_value[self.units])
                    self.raw_data.append(result[1]) 
                    result = result[0]
                cxn.data_vault.add([scan_value[self.units], result], context=context)
            self.update_progress(i)
            
            
            
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
        dv.new(dataset_name, [('Iteration', 'Arb')], [
               (self.script.name, 'Arb', 'Arb')], context=context)
        dv.add_parameter('plotLive', True, context=context)
        for para in parameter.keys():
            dv.add_parameter(para, parameter[para], context=context)
    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * \
            float(iteration + 1.0) / len(self.scan_points)
        self.sc.script_set_progress(self.ident, progress)

    def finalize(self, cxn, context):
        self.raw_data=np.array(self.raw_data)
        #saves the raw_data into the same folder as the data vault data
        np.savetxt("../servers/data_vault/__data__/"+self.dirc+"raw_data.csv", self.raw_data, delimiter=",", fmt="%s")
        self.script.finalize(cxn, context)
