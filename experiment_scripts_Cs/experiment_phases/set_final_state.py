from phase import phase
from labrad.units import WithUnit
import numpy as np
from Experiment_config import *
from thermalize import thermalize
#channel information, will combine to the same file later
#we also have the clibrate class and calibrate functions that we can integrate later


#meta info
#scan variable + Unit


###think about the parameter handling here

#the parameter names within the phase are saved in parametervault[phase_name_folder]
#there should be another global parameters that save the information all across the phase 
#and another global config files that save all config information (e.g. camera ROI, channel information)

#difference between global config and global parameters
#idea is that global parameters might be changed (e.g. repeat_num, image_num, exposure_time) it is just multiple phases share the same para in the experiment
#config are usually fixed (e.g. within one version of scripts) and change it will change all experiments afterwards

#For all the parameters, it come with a unit. However, as some of the servers do not take unit parameter as an input (e.g. TTL), so we have to normalize it to a unitless parameters
#E.g. All TTL time input is in unit of s, so we do params["name"]["s"] to give a normalized unit in second to the TTL input

#Path information:
#Current path is set to be folder_path = r"C:\Users\Cryo_rdyberg\Princeton Dropbox\Yukai Lu\CryoRydberg\Data\year\month\day\name
#We can also automate it 



#load mot tweezer phase:
#we usually use this phase to start an experiment
#It contains load MOT->tweezer->high-field cooling->ramping tweezer down to img field (img field can be overide to other field if needed)

#usually after this phase we will follow by imaging phase

class set_final_state(phase):
    phase_name = "set_final_state"
    parameter_names = []
    external_parameter_names = [("general","efieldvz"),("general","efieldvy"),("general","efieldvx"),("general","scan_variable"),("general","scan_variable_name"),
                                ("load_MOT_Tweezers","coolingamp_for_loading"),("load_MOT_Tweezers","bias_xv_for_loading"),("load_MOT_Tweezers","bias_yv_for_loading"),
                                ("load_MOT_Tweezers","bias_zv_for_loading"),("thermalize","tweezer_waiting_amp")]
    
    def dophase(self, cxn, params):
    ################
    ##### Phase3B: image with PGC config
    ####@@@@!!! DDS needs to be fully defined over the sequence
        cxn.AOServer.setFinalState(efieldvy_ao, params["efieldvy"])
        cxn.AOServer.setFinalState(efieldvz_ao, params["efieldvz"])
        cxn.AOServer.setFinalState(efieldvx_ao, params["efieldvx"])
        cxn.AOServer.setFinalState(tweezer_slm_amp, params["tweezer_waiting_amp"])  
        cxn.AOServer.setFinalState(three_d_motAOM_amp, params["coolingamp_for_loading"])  
        #cxn.AOServer.setFinalState(offsetlock, WithUnit(coolingdetune_for_loading"])
        cxn.AOServer.setFinalState(bias_fieldx, params["bias_xv_for_loading"]) 
        cxn.AOServer.setFinalState(bias_fieldy, params["bias_yv_for_loading"]) 
        cxn.AOServer.setFinalState(bias_fieldz, params["bias_zv_for_loading"]) 
        cxn.finitedopulses.SetFinalState(biasBz_forward_ttl,1)

        cxn.finitedopulses.SetFinalState(tweezer_slm_AOM,1)
        cxn.finitedopulses.SetFinalState(tweezer_slm_aom_pid,1)
        cxn.finitedopulses.SetFinalState(three_d_motAOM,1)
        cxn.finitedopulses.SetFinalState(repump_motAOM,1)
        cxn.finitedopulses.SetFinalState(two_d_motAOM,1)
        cxn.finitedopulses.SetFinalState(push_beamAOM,1)
        cxn.finitedopulses.SetFinalState(opAOM,0)  
        #cxn.finitedopulses.SetFinalState(mot_coil,1) 


        


    def getlength(self, params):
        return 0



import labrad
import sys
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/experiment_scripts_Cs/experiment_phases")
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/script_scanner/")
#IMPORT PHASES
from experiment_phases import experiment_phases, S, P
#IMPORT SCAN EXPERIMENT BASE CLASSES
from single_sequence import single_sequence


#from experiments_utils import *
#from phaseDefinitions import *


def exp_sequence():
    return S(thermalize(),set_final_state())#,imaging())


class set_final_state_exp(experiment_phases):
    #for all parameters that are used in the experiment but not in the phases included
    required_parameters = set_final_state.external_parameter_names + [("general","verbose"),("general","seqlen"),("general","nLoops")]
    name = set_final_state.phase_name
    first = None
    phases = None
    last = None

    def __init__(self, name=None, required_parameters=None, cxn=None, min_progress=0.0, max_progress=100.0):
        #self.phases, self.first, self.last,load_required_parameters = exp_sequence()
        #self.required_parameters += load_required_parameters 

        #need to be removed later, depending if we need global variables like an array (or we can just pass a dir in parameter vault)
        #now self.params["seqlen"] are used for calculating time for a single run
        self.params = {}
        self.results = []
        super().__init__(self.name, self.required_parameters, cxn,min_progress, max_progress)

    @classmethod
    def all_required_parameters(cls):
        if cls.first == None:
            cls.required_parameters += cls._load_parameters_before_init()
        print("running it")
        parameters = set(cls.required_parameters)
        parameters = list(parameters)
        #print(cls.required_parameters)
        #print("test")
        return parameters
    
    #This function is used for loading parameters for the SC GUI. In the SC GUI it will call @classmethod all_required_parameters to load paramters
    #@classmethod function will run itself before the class is initialized, that's why we need this function here to avoid an empty parameters
    # we also used it to initialize our experiment seq by letting cls.phase, cls.first cls.last to be what needed to be
    #In this way we do not need to rerun exp_sequence again to find out the first and last phases
    @classmethod
    def _load_parameters_before_init(cls):
        cls.phases, cls.first, cls.last,required_parameters = exp_sequence()
        #print(cls.first)
        return required_parameters
    

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    exprt = single_sequence(set_final_state_exp)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
