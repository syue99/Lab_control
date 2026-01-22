import numpy as np
from time import localtime, strftime
from labrad.units import WithUnit
from experiment import experiment
import itertools

#BY FRED

#The general class for scanning an experiment with different parameter types and options for Cameras/PMT etc.
#We want to make this class the standard scan class of Sript scanner
class scan_experiment(experiment):
    """Used to repeat an experiment multiple times."""

    #depend on the scan parameter type. it will respond differently
    #it will output a list with Units for the scanning paramete (equ. iterlist of Jeff's code)



    #not sure if "units" is still needed
    #Add a cmd command for optional command:(e.g. randomized list)
    def __init__(self, script_cls, parameter, minim, maxim, steps, units, cmd={}):
        #load script before make experiment
        self.script_cls = script_cls
        #load parameters
        #tuple means it is a 1d scan
        #list means it is a 2d or more scan
        #for every scan para we have parametername_scan, :-5 remove _scan so that we can change the parameter
        if type(parameter)==tuple:
            self.dim = 1
            self.parameter = parameter
            collection,name = self.parameter
            #for every scan para we have parametername_scan, :-5 remove _scan so that we can change the parameter
            self.script_cls.scanpara_names.append((collection,name[:-5]))
        elif type(parameter)==list:
            self.dim = len(parameter)
            self.parameter = parameter
            collection,name = self.parameter[0]
            #for every scan para we have parametername_scan, :-5 remove _scan so that we can change the parameter
            self.script_cls.scanpara_names.append((collection,name[:-5]))
        else:
            raise Exception("format of parameters are not recognized")
        #ordered scan without CMD command
        #OUR nd scan is more like 1+(n-1) scan, so that the grapher displays #(n-1)dim 1d lines 
        if cmd=={}:
            self.scan_points = np.linspace(minim, maxim, steps)
            self.scan_points = [WithUnit(pt, units) for pt in self.scan_points]
            self.extra_scan_points_list = []
            self.steps_counter = 1
        self.cmd =cmd
                
        scan_name = self.name_format(script_cls.name)
        super(scan_experiment, self).__init__(scan_name)

    #TODO:maybe we need a better name format
    def name_format(self, scan_name):
        # Revised by Fred
        return 'Scanning {0} in {1}'.format(
            self.script_cls.parameter_name, scan_name)

    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)
        if self.cmd=={}:
            for i in range(1,self.dim):
                collection,name = self.parameter[i]
                #for every scan para we have parametername_scan, :-5 remove _scan so that we can change the parameter
                self.script.scanpara_names.append((collection,name[:-5]))
                #avoid overriding, might not be necessary
                #print(collection,name)
                min, max, step = self.script.parameters[collection][name]
                #somehow we lose the units when getting this parameter, but it does not hurt the script
                #TODO: somehow get back the unit here
                unit = self.script.parameters[collection][name[:-5]].units
                self.steps_counter *=step
                points = np.linspace(min, max, step)
                self.extra_scan_points_list.append([WithUnit(pt, unit) for pt in points])
        self.navigate_data_vault(cxn, self.parameter, context)
        self.script.dirc = self.dirc

    def run(self, cxn, context):
        scan_points_len = len(self.scan_points)
        if self.dim == 1:
            for i, scan_value in enumerate(self.scan_points):
                if self.pause_or_stop():
                    return
                #changed by Fred, only a sketchy fix, need to be fixed later
                self.script.set_parameters({('para1',"para2"): scan_value})
                self.script.set_progress_limits(
                    100.0 * i / scan_points_len, 100.0 * (i + 1) / scan_points_len)
                result = self.script.run(cxn, context, [scan_value])
                if self.script.should_stop:
                    return
                if result is not None:
                    # revised by Fred to add the feature of storing raw data
                    # For now raw data is handled without going to the data_vault
                    # When the image data is handled properly, we should also add raw data into the image class
                    # the logic now is that result=[plotresult,raw] for plotresult=int/float, raw=np array
                    # if the result=plotresult, then nothing changed

                    #TODO:we can change usepmt to some better name
                    if str(type(result)) == "<class 'list'>":
                        if self.script.parameters.scan_use_pmt.USEPMT == False:
                            result[1] = np.insert(result[1], 0, scan_value[self.units])
                            self.raw_data.append(result[1])
                            result = result[2]
                            cxn.data_vault.add(result, context=context)
                        elif self.script.parameters.scan_use_pmt.USEPMT == True:
                            result[1] = np.insert(result[1], 0, scan_value[self.units])
                            self.raw_data.append(result[1])
                            result = result[0]
                            cxn.data_vault.add([scan_value[self.units], result], context=context)

                    #cxn.data_vault.add([scan_value[self.units], result], context=context)
                    #cxn.data_vault.add(result, context=context)
                    # cxn.data_vault.add([scan_value[self.units], result], context=context)
                    # cxn.data_vault.add(result, context=context)
                self.update_progress(i)
        else:
            extra_scan_points = itertools.product(*self.extra_scan_points_list)
            counter = 0
            extra_scan_len = self.steps_counter
            for extra_scan_tuple in extra_scan_points:
                for i, scan_value in enumerate(self.scan_points):
                    if self.pause_or_stop():
                        return
                    #changed by Fred, only a sketchy fix, need to be fixed later
                    self.script.set_parameters({('para1',"para2"): scan_value})
                    #print(100.0 * i / scan_points_len/extra_scan_len+ 100/extra_scan_len*counter)

                    #original code is self.script.set_progress_limits, might be used for rsg
                    self.set_progress_limits(
                    100.0 * i / scan_points_len/extra_scan_len+ 100/extra_scan_len*counter, 100.0 * (i + 1) / scan_points_len/extra_scan_len+ 100/extra_scan_len*counter)
                    result = self.script.run(cxn, context, [scan_value,*extra_scan_tuple])
                    if self.script.should_stop:
                        return
                    if result is not None:
                            # revised by Fred to add the feature of storing raw data
                            # For now raw data is handled without going to the data_vault
                            # When the image data is handled properly, we should also add raw data into the image class
                            # the logic now is that result=[plotresult,raw] for plotresult=int/float, raw=np array
                            # if the result=plotresult, then nothing changed

                            #TODO:we can change usepmt to some better name
                        if str(type(result)) == "<class 'list'>":
                            if self.script.parameters.scan_use_pmt.USEPMT == False:
                                result[1] = np.insert(result[1], 0, scan_value[self.units])
                                self.raw_data.append(result[1])
                                result = result[2]
                                cxn.data_vault.add(result, context=context)
                            elif self.script.parameters.scan_use_pmt.USEPMT == True:
                                result[1] = np.insert(result[1], 0, scan_value[self.units])
                                self.raw_data.append(result[1])
                                result = result[0]
                                cxn.data_vault.add([scan_value[self.units], result], context=context)
                    self.update_progress(i)
                counter+=1

#initialize the real simple grapher plot feature
    # pass array of independent and dependent as ["name","unit"]
    # Revised by Fred by adding parameter
    def navigate_data_vault(self, cxn, parameter, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S", local_time)
        directory = ['ScriptScanner']
        directory.extend([strftime("%Y%b%d", local_time), strftime("%H%M_%S", local_time)])
        # need this directory to save raw_data
        for text in directory:
            self.dirc = self.dirc + text + '.dir/'
        dv.cd(directory, True, context=context)
        # dv.newmatrix(dataset_name, (1,200), 'f', context=context)
        if self.script.parameters.scan_use_pmt.USEPMT == False:
            dv.newmatrix(dataset_name, (1, 1600), 'f', context=context)
            dv.add_parameter('plotLive', True, context=context)
            # for para in parameter.keys():
            #  dv.add_parameter(para, parameter[para], context=context)
            # add parameters used in the experiment
            for para in self.script.parameters:
                dv.add_parameter(para, self.script.parameters[para], context=context)
            # add scan points to the first element of the dataset_name
            # we set 300 as this is very close to the background noise
            # scan_para = np.ones((1,200))*300
            scan_para = np.ones((1, 1600)) * 300
            # print(self.scan_points)
            scan_para[0, 0] += self.scan_points[0][self.units]
            scan_para[0, 1] += self.scan_points[len(self.scan_points) - 1][self.units]
            scan_para[0, 2] += len(self.scan_points)

            dv.add(scan_para, context=context)
        elif self.script.parameters.scan_use_pmt.USEPMT == True:
            dv.new(dataset_name, [('Iteration', 'Arb')], [
                (self.script.name, 'Arb', 'Arb')], context=context)
            dv.add_parameter('plotLive', True, context=context)
            # collection, param = parameter
            # for para in parameter.keys():
            # for para in param.keys():
            # dv.add_parameter(para, parameter[para], context=context)
            # dv.add_parameter(para, param[para], context=context)
            # add parameters used in the experiment
            for para in self.script.parameters:
                dv.add_parameter(para, self.script.parameters[para], context=context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * \
                   float(iteration + 1.0) / len(self.scan_points)
        self.sc.script_set_progress(self.ident, progress)

    def finalize(self, cxn, context):
        self.raw_data = np.array(self.raw_data)
        # saves the raw_data into the same folder as the data vault data
        if self.raw_data != []:
            # np.savetxt("../data_vault/__data__/"+self.dirc+"raw_data.csv", self.raw_data, delimiter=",", fmt="%s")
            np.savetxt("../data_vault/__data__/"+self.dirc+"raw_data.csv", self.raw_data, delimiter=",", fmt="%s")
        self.script.finalize(cxn, context)
