import sys
sys.path.append('C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/experiment_scripts_Cs/')
sys.path.append('C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/experiment_scripts_Cs/experiment_phases/')

#from Experiment_config import TTL_dict, AO_dict
TTL_dict={4: 'biasBz_direction', 16: 'biasBz_forward_ttl', 17: 'biasBz_reverse_ttl', 0: 'mot_coil', 25: 'two_d_motAOM', 27: 'three_d_motAOM', 28: 'repump_motAOM', 26: 'opAOM', 29: 'push_beamAOM', 3: 'tweezer_slm_AOM', 5: 'tweezer_slm_aom_pid', 6: 'bias_y_switch_ttl', 2: 'tweezer_camera_trigger', 11: 'uv_aom', 15: 'red_aom_switch_ttl', 14: 'OP_dds_switch'}
AO_dict={4: 'tweezer_slm_amp', 3: 'bias_fieldx', 2: 'bias_fieldy', 1: 'bias_fieldz', 0: 'three_d_motAOM_amp', 8: 'efieldvx_ao', 11: 'efieldvy_ao', 9: 'efieldvz_ao'}
class pulse_display_item:
    def __init__(self, name, pulse_type, channel, default_display):
        self.name = name
        self.pulse_type = pulse_type
        self.channel = channel
        self.default_display = default_display

    def __repr__(self):
        return f"Item(p1={self.name}, p2={self.pulse_type}, p3={self.channel}, p4={self.default_display})"



class config(object):

    # list in the format (import_path, class_name)
    scripts = [
                ('test_experiment_phase',
                'run_exp_'),
                ('load_MOT_Tweezers',
                'load_MOT_tweezer_exp'),
                ('imaging',
                'imaging_exp'),
                ('shortPGC',
                'shortPGC_exp'),
                ('adiabatic_cooling',
                'adiabatic_cooling_exp'),
                ('optical_pumping',
                'optical_pumping_exp'),
                ('single_pi_pulse',
                'single_pi_pulse_exp'),
                ('fast_pushout',
                'fast_pushout_exp'),
                ('recap',
                'recap_exp'),
                ('thermalize',
                'thermalize_exp'),
                ('set_final_state',
                'set_final_state_exp'),
                # ('imaging',
                # 'imaging_exp'),
                # ('imaging',
                # 'imaging_exp'),

                ]

    allowed_concurrent = {
    }

    launch_history = 1000


    #Script scanner GUI config, this we can revise later
if __name__=="__main__":
    #print(pulse_display_item("test","AO",2,1))
    print(AO_dict)