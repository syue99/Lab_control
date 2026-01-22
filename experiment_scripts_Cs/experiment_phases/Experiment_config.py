import numpy as np
from labrad.units import WithUnit
# -------------------------------
# General settings: sequence name and folder to save images
# -------------------------------
sequence = "RabiFreq"
#folder_path = r"C:\Users\Cryo_rdyberg\Documents\Codebase\Lab_control\TweezerCamKinetix22\OP1006"
#folder_path = r"C:\Users\Cryo_rdyberg\Princeton Dropbox\Yukai Lu\CryoRydberg\Data\2025\10\09\Imag_loss_release_after_op_at_rightamp_0.7"
folder_path = r"C:\Users\Cryo_rdyberg\Princeton Dropbox\Yukai Lu\CryoRydberg\Data" #with_adiabatic_cool_recap_amp2.24V"


# -------------------------------
# Repeat
# -------------------------------
repeat_num = 20 #
#dt = 0.02 


# -------------------------------
# Analog channels
# -------------------------------
class AO():
    tweezer_slm_amp = 4
    bias_fieldx = 3
    bias_fieldy = 2
    bias_fieldz = 1
    three_d_motAOM_amp = 0

    efieldvx_ao = 8
    efieldvy_ao = 11
    efieldvz_ao = 9
for k, v in vars(AO).items():
    if not k.startswith("__"):
        globals()[k] = v
AO_dict = {
    v: k for k, v in vars(AO).items()
    if not k.startswith("__")
}
# -------------------------------
# TTL channels, port#= channel#//8, line# = channel#%8, e.g., two_d_motAOM = 25 corresponds to port3, line1
# -------------------------------
class TTL():
    biasBz_direction  = 4
    biasBz_forward_ttl = 16
    biasBz_reverse_ttl = 17
    #### 3D MOT coils
    mot_coil = 0    #### port0, line0
    two_d_motAOM = 25 #### port3, line1, i.e, 
    three_d_motAOM = 27 #### port3, line3
    repump_motAOM = 28 #### port3, line4

    opAOM = 26  #### port3, line2, now labeled as imgAOM
    push_beamAOM = 29 #### port3, line5

    ### tweezer SLM
    tweezer_slm_AOM = 3  #### port0, line3
    tweezer_slm_aom_pid = 5
    bias_y_switch_ttl = 6
    #### camera
    tweezer_camera_trigger = 2   #### port0, line2

    ### uv aom
    uv_aom = 11
    red_aom_switch_ttl = 15 ### TTL high, UV power high (switch box output 0V, red all going through the 0th order for producing high UV power)

    #switch for OP dds to fix the 1us random delay. Could be depreciated by changing to DDS box TTL
    OP_dds_switch = 14

for k, v in vars(TTL).items():
    if not k.startswith("__"):
        globals()[k] = v
TTL_dict = {
    v: k for k, v in vars(TTL).items()
    if not k.startswith("__")
}

# -------------------------------
# DDS parameters
# -------------------------------
offsetlock = 'DDS1'
OP_dds = 'DDS2'
op_repump_dds = 'DDS5'

offsetlock_amp = WithUnit(-17,'dBm')
dds_start_time_delay = WithUnit(12.5e-6,'s')
dds_trigger = 12

opAOM_freq = WithUnit(149.0,"MHz")
op_repump_aom_freq = WithUnit(100.4,"MHz")


# -------------------------------
# Camera ROI
# -------------------------------
ROIleft = 1160
#ROIleft = 1250
ROItop = 1225
ROIwidth = 160
ROIheight = ROIwidth


#### UV pulse generator keysight

ks_ch = 1
ks_width_list = np.arange(0, 3000, 200)*1e-9#np.array([0,400,873])*1e-9#np.array([400])*1e-9# np.array([1000])*1e-9#np.arange(0, 4000, 400)*1e-9 #np.array([700])*1e-9 #np.array([1000])*1e-9#np.array([1000])*1e-9#np.arange(200, 5000, 400)*1e-9#np.array([1000])*1e-9#
ks_period = 1e-4
ks_vpp = 4.0
ks_offset = 2.0
ks_rise_time = 5e-9
ks_fall_time = 5e-9
ks_burst_cycles = 1
ks_trigger_source = "EXT"
ks_load = "INF"







if __name__ == '__main__':
    print(TTL_dict)






