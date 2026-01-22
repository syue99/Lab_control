from phase import phase
from labrad.units import WithUnit
import numpy as np
from Experiment_config import *

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

class load_MOT_Tweezers(phase):
    phase_name = "load_MOT_Tweezers"
    parameter_names = ["mot_loading_time","delay_after_loading","loading_field_pgc_cooling_time",'ispushBeamOn','tweezer_loading_amp','bias_xv_for_loading','bias_yv_for_loading', 'extra_cooling_time',
    'bias_zv_for_loading','coolingdetune_for_loading','coolingamp_for_loading','loading_field_coolingamp_for_pgc','reverse_zv_nulling','bias_xv_for_nulling_high','loading_field_coolingdetune_for_pgc']
    external_parameter_names = [("general","efieldvz"),("general","efieldvy"),("general","efieldvx"),("imaging","bias_yv_for_nulling"),("imaging","bias_xv_for_nulling"),("general","tweezer_ramp_down_time"),
                                ("imaging","bias_zv_for_nulling"),("imaging","tweezer_img_amp"),("imaging","coolingamp_for_img"),("imaging","coolingdetune_for_img"),("general","scan_variable"),("general","scan_variable_name")]
    
    def dophase(self, cxn, params):
    ################
    ##### Phase1: load into MOT and tweezer
    #phase1_time = mot_loading_time + delay_after_loading
    ####@@@@!!! DDS needs to be fully defined over the sequence
        #print("test")
        #print(params)
        DDS = []

        phase_time_1 = np.ceil((params["mot_loading_time"]["s"] + params["delay_after_loading"]["s"])*1e6 / 4) * 4/1e6
        phase_time_2 = np.ceil((params["loading_field_pgc_cooling_time"]["s"])*1e6 / 4) * 4/1e6
        phase_time_3 = np.ceil((params["tweezer_ramp_down_time"]["s"] + params["extra_cooling_time"]["s"])*1e6 / 4) * 4/1e6

        if self.tstart < dds_start_time_delay['s']:
            cxn.finitedopulses.PulseOn(dds_trigger, self.tstart, 1e-5)
            cxn.pulser.add_ttl_pulse('TTL2', WithUnit(self.tstart+0.1, 'us'), WithUnit(0.1, 'us')) #### @@@??
            DDS.append((offsetlock, WithUnit(self.tstart+0.5, 'us'),  ### 0.5 is a small start time required for using DDS
                        params["mot_loading_time"] - dds_start_time_delay - WithUnit(0.5,'us'), 
                        params["coolingdetune_for_loading"], 
                        offsetlock_amp, 
                        WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')))
        else:
            DDS.append((offsetlock, WithUnit(self.tstart, 's')-dds_start_time_delay,  ### 0.5 is a small start time required for using DDS
                        params["mot_loading_time"], 
                        params["coolingdetune_for_loading"], 
                        offsetlock_amp, 
                        WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')))            

        cxn.finitedopulses.PulseOn(tweezer_slm_AOM, self.tstart, phase_time_1)
        cxn.finitedopulses.PulseOn(tweezer_slm_aom_pid, self.tstart, phase_time_1)
        cxn.AOServer.setvoltagepulse(tweezer_slm_amp, self.tstart, phase_time_1, params["tweezer_loading_amp"])
        #3D MOT
        ## Turn on quadrupole B field 
        cxn.finitedopulses.PulseOn(mot_coil, self.tstart, params["mot_loading_time"]["s"])

        # #2D MOT
        cxn.finitedopulses.PulseOn(two_d_motAOM, self.tstart, params["mot_loading_time"]["s"])
        #Repump, for both 2d and 3d mot
        cxn.finitedopulses.PulseOn(repump_motAOM, self.tstart, params["mot_loading_time"]["s"])
        #Push beam controlling flux from 2D MOT
        cxn.finitedopulses.PulseOn(push_beamAOM, self.tstart, params["mot_loading_time"]["s"])
        ## 3d mot cooling beam
        cxn.finitedopulses.PulseOn(three_d_motAOM, self.tstart, params["mot_loading_time"]["s"])
        #ao.setvoltagepulse(offsetlock, 0, mot_loading_time, WithUnit(coolingdetune_for_loading,"V"))  
        cxn.AOServer.setvoltagepulse(three_d_motAOM_amp, self.tstart, params["mot_loading_time"]["s"], params["coolingamp_for_loading"]) 
        cxn.AOServer.setvoltagepulse(three_d_motAOM_amp, self.tstart + params["mot_loading_time"]["s"], params["delay_after_loading"]["s"], params["loading_field_coolingamp_for_pgc"]) 

        
        ## bias field used for overlappin MOT with tweezers
        cxn.AOServer.setvoltagepulse(bias_fieldx, self.tstart, params["mot_loading_time"]["s"], params["bias_xv_for_loading"])
        cxn.AOServer.setvoltagepulse(bias_fieldy, self.tstart, params["mot_loading_time"]["s"], params["bias_yv_for_loading"])

        #TODO rewrite this logic
        biasBz_forward_ttl = 16
        cxn.finitedopulses.PulseOn(biasBz_forward_ttl, self.tstart, params["mot_loading_time"]["s"])
        cxn.AOServer.setvoltagepulse(bias_fieldz, self.tstart, params["mot_loading_time"]["s"], params["bias_zv_for_loading"])###  when TTL is off bias z set by the fixed power supply
        if params["reverse_zv_nulling"]:
            biasBz_forward_ttl = biasBz_reverse_ttl
        cxn.finitedopulses.PulseOn(biasBz_forward_ttl, self.tstart+params["mot_loading_time"]["s"], params["delay_after_loading"]["s"])

            

        ################
        ###### Phase2: PGC cooling in deep tweezer
        #phase2_time = loading_field_pgc_cooling_time

        DDS.append((offsetlock, WithUnit(self.tstart,'s') + params["mot_loading_time"] - dds_start_time_delay, 
                    params["delay_after_loading"]+params["loading_field_pgc_cooling_time"],  
                    params["loading_field_coolingdetune_for_pgc"], 
                    offsetlock_amp, 
                    WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')))

        cxn.finitedopulses.PulseOn(tweezer_slm_AOM, self.tstart+phase_time_1, phase_time_2)
        cxn.finitedopulses.PulseOn(tweezer_slm_aom_pid, self.tstart+phase_time_1, phase_time_2)
        
        cxn.AOServer.setvoltagepulse(tweezer_slm_amp, self.tstart+phase_time_1, phase_time_2, params["tweezer_loading_amp"])
    
        
        
        #### cooling beam applied with some delay after turning off MOT to reduce background, 100ms should be more than enough. 
        ###At high tweezer we do not want to image, just to lower the temp
        cxn.finitedopulses.PulseOn(three_d_motAOM, self.tstart+phase_time_1, params["loading_field_pgc_cooling_time"]["s"])  ####@@@ vs changed from pgc_cooling_time*2 to pgc_cooling_time
        cxn.finitedopulses.PulseOn(repump_motAOM, self.tstart+phase_time_1, params["loading_field_pgc_cooling_time"]["s"])
        #ttl.PulseOn(tweezer_camera_trigger, loading_tot_time-6e-4, 1e-5)

        cxn.AOServer.setvoltagepulse(three_d_motAOM_amp, self.tstart+phase_time_1, params["loading_field_pgc_cooling_time"]["s"], params["loading_field_coolingamp_for_pgc"])
        
        cxn.AOServer.setvoltagepulse(bias_fieldx, self.tstart+params["mot_loading_time"]["s"], params["delay_after_loading"]["s"]+params["loading_field_pgc_cooling_time"]["s"], params["bias_xv_for_nulling_high"]) ## 
        #this rampToVoltageTime method is chn,final_voltage, start_time, end_time
        
        cxn.AOServer.setvoltagepulse(bias_fieldy, self.tstart+params["mot_loading_time"]["s"], params["delay_after_loading"]["s"]+params["loading_field_pgc_cooling_time"]["s"], params["bias_yv_for_nulling"])
        ### switch Bz from the one for mot loading to the PGC configuration which is in an opposite direction.
        # The dt here makes sure Bz is back to the value for loading before starting a new shot.
        #ttl.PulseOn(biasBz_direction, mot_loading_time, duration-mot_loading_time-dt) 
        cxn.finitedopulses.PulseOn(biasBz_forward_ttl, self.tstart+phase_time_1, phase_time_2)
        cxn.AOServer.setvoltagepulse(bias_fieldz, self.tstart+params["mot_loading_time"]["s"], params["delay_after_loading"]["s"]+params["loading_field_pgc_cooling_time"]["s"],  params["bias_zv_for_nulling"]) ## 

        

        ################
        ###### Phase3A: lower tweezer trap depth to an intermediate depth, usually followed by a PGC imaging phase
        #phase3_time = tweezer_ramp_down_time
        phase3_start_time = self.tstart + phase_time_1 + phase_time_2
        DDS.append((offsetlock, WithUnit(phase3_start_time,'s') - dds_start_time_delay, ### @@@ dds start time delay
                    WithUnit(phase_time_3,'s'),  #### @@@?? WithUnit(tweezer_ramp_down_time*2+coolingimg_time, 's'), why *2??
                    params["coolingdetune_for_img"], 
                    offsetlock_amp,
                    WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')))
        cxn.finitedopulses.PulseOn(tweezer_slm_AOM, phase3_start_time, phase_time_3)
        cxn.finitedopulses.PulseOn(tweezer_slm_aom_pid, phase3_start_time, phase_time_3)

        cxn.AOServer.rampToVoltageTime(tweezer_slm_amp, params["tweezer_img_amp"],phase3_start_time, phase3_start_time + params["tweezer_ramp_down_time"]["s"])
        cxn.AOServer.setvoltagepulse(tweezer_slm_amp, phase3_start_time + params["tweezer_ramp_down_time"]["s"], params["extra_cooling_time"]["s"], params["tweezer_img_amp"])
        
        cxn.AOServer.setvoltagepulse(three_d_motAOM_amp, phase3_start_time, phase_time_3, params["coolingamp_for_img"])

        ######second cooling with lowered trap with extra_cooling_time
        cxn.finitedopulses.PulseOn(three_d_motAOM, phase3_start_time + params["tweezer_ramp_down_time"]["s"], params["extra_cooling_time"]["s"]) ####@changed from pgc_cooling_time*2 to pgc_cooling_time
        cxn.finitedopulses.PulseOn(repump_motAOM, phase3_start_time + params["tweezer_ramp_down_time"]["s"], params["extra_cooling_time"]["s"])
        
        #magnetic field        
        cxn.AOServer.rampToVoltageTime(bias_fieldx,params["bias_xv_for_nulling"],phase3_start_time,phase3_start_time + params["tweezer_ramp_down_time"]["s"])
        cxn.AOServer.setvoltagepulse(bias_fieldx, phase3_start_time + params["tweezer_ramp_down_time"]["s"], params["extra_cooling_time"]["s"], params["bias_xv_for_nulling"]) ##
        cxn.AOServer.setvoltagepulse(bias_fieldy, phase3_start_time, phase_time_3,  params["bias_yv_for_nulling"])
        cxn.finitedopulses.PulseOn(biasBz_forward_ttl, phase3_start_time, phase_time_3)
        cxn.AOServer.setvoltagepulse(bias_fieldz, phase3_start_time, phase_time_3, params["bias_zv_for_nulling"]) ## 

        cxn.pulser.add_dds_pulses(DDS)
        


    def getlength(self, params):
        return params['mot_loading_time']['s']+ params['delay_after_loading']['s']+ params['loading_field_pgc_cooling_time']['s']+params["tweezer_ramp_down_time"]['s']+params["extra_cooling_time"]['s']



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
    return S(load_MOT_Tweezers())#,imaging())


class load_MOT_tweezer_exp(experiment_phases):
    #for all parameters that are used in the experiment but not in the phases included
    required_parameters = load_MOT_Tweezers.external_parameter_names + [("general","verbose"),("general","seqlen"),("general","nLoops")]
    name = load_MOT_Tweezers.phase_name
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
    exprt = single_sequence(load_MOT_tweezer_exp)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
