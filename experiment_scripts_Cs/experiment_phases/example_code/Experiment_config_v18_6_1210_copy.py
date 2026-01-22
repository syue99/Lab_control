import numpy as np

# -------------------------------
# General settings: sequence name and folder to save images
# -------------------------------
sequence = "RabiFreq"
#folder_path = r"C:\Users\Cryo_rdyberg\Documents\Codebase\Lab_control\TweezerCamKinetix22\OP1006"
#folder_path = r"C:\Users\Cryo_rdyberg\Princeton Dropbox\Yukai Lu\CryoRydberg\Data\2025\10\09\Imag_loss_release_after_op_at_rightamp_0.7"
folder_path = r"C:\Users\Cryo_rdyberg\Princeton Dropbox\Yukai Lu\CryoRydberg\Data\2025\12\10\lifetime_scan"#with_adiabatic_cool_recap_amp2.24V"

#scan_freq_1us_UV_nopulse
#scan_freq_0.4us_UV_pulsed

# -------------------------------
# Analog channels
# -------------------------------
tweezer_slm_amp = 4
bias_fieldx = 3
bias_fieldy = 2
bias_fieldz = 1
three_d_motAOM_amp = 0

efieldvx_ao = 8
efieldvy_ao = 11
efieldvz_ao = 9




# -------------------------------
# TTL channels, port#= channel#//8, line# = channel#%8, e.g., two_d_motAOM = 25 corresponds to port3, line1
# -------------------------------

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

# -------------------------------
# DDS parameters
# -------------------------------
offsetlock = 'DDS1'
OP_dds = 'DDS2'
op_repump_dds = 'DDS5'

offsetlock_amp = -17
dds_start_time_delay = 12.5e-6
dds_trigger = 12



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


#########################################
###############################################
########## -------------------------------
########## Phase parameters and timings
########## -------------------------------
#############################################
#############################################
# -------------------------------
# E field nulling parameters
# -------------------------------
efieldvz = 0.84#0.94
efieldvy = 0.87#0.894
efieldvx = -1.55#-2.35


# -------------------------------
# Tweezer amp parameters
# -------------------------------
tweezer_amp_scaling = 1/5.8#9/49 ### changing from 7 by 7 array to 3 by 3.
#tweezer_loading_amp = 2.24#3.0
tweezer_loading_amp = 2.24*tweezer_amp_scaling
#tweezer_img_amp = 0.69#1.3
tweezer_img_amp = 0.69*tweezer_amp_scaling#1.24#2.24#0.69# tweezer_loading_amp#0.69#2.1

#AO related
tweezer_op_amp =0.15*tweezer_amp_scaling# 0.3#0.69#0.15 #0.15#0.69#0.43#[0.55]#.7
tweezer_op_amp_list = np.array([0.15, 0.3, 0.5, 0.69])*tweezer_amp_scaling

#AO related
tweezer_adiabatic_cooling_amp = 0.035*tweezer_amp_scaling + 0.002  ## there is some background
tweezer_adiabatic_cooling_amp_list = tweezer_op_amp_list#[0.69]#[0.035]#np.concatenate([[0, 0.002], np.arange(0.005, 0.025, 0.005)])#np.arange(0.04, 0.15, 0.02)

tweezer_wait_time = 0.2#0.3
tweezer_waiting_amp = 2.4*tweezer_amp_scaling#3


# -------------------------------
# Tweezer loading from MOT
# -------------------------------
#DDS related:
coolingdetune_for_loading = 139.77

#timing related
mot_loading_time = 0.6#0.8#0.8#0.3 ### 04162025: 200ms works
delay_after_loading = 0.1 ### delay after turning off MOT B field, for both B field and atom background to decay

loading_tot_time = mot_loading_time + delay_after_loading


#AO related


coolingamp_for_loading = 5.47#(output 4.5)  ### 3d mot aom amp

# bias field used for overlappin MOT with tweezers
bias_xv_for_loading = 0.5#2.5## changed from 3.2 on 10/21 #2.5#4.25#3.5 #4  ##in V, conversion factor about 0.4G/V
bias_yv_for_loading = 0.5#1.5 #1.13#0.52  # 1G/V  ## zv is applied by an external fixed power supply
bias_zv_for_loading = 0.9  #1.1#0.925#0.46  ## 0.5G/V





# -------------------------------
# PGC cooling at high field
# -------------------------------
#DDS related:
loading_field_coolingdetune_for_pgc = 139.77 + 5.22/64*14

#timing related
loading_field_pgc_cooling_time = 40e-3

#AO related
loading_field_coolingamp_for_pgc = 1.915#1.915

#defined in previous phase
#tweezer_loading_amp = tweezer_loading_amp

bias_xv_for_nulling_high = 4#4#5.3
bias_xv_for_nulling = 4.5#4 for img amp 2.24, 4.2 for img amp 0.69 (can keep the same for simplicity and will not affect img fidelity much) #4.5 #4  ##in V, conversion factor about 0.4G/V
bias_yv_for_nulling = 1.27#1.3#1.375#1.2#1.0#2.5#1.8#1.0#1.0#0.5 # 1G/V
bias_zv_for_nulling = 0.5#0.4#1.2#1.0#0.0  ## 0.5G/V
reverse_zv_nulling = False


# -------------------------------
# Lower tweezer trap depth to an IMG depth and Image
# -------------------------------
#DDS related:
coolingdetune_for_img = 139.77 + 5.22/64*12#139.77 + 5.22/64*12

coolingdetune_for_img_list = [139.77 + 5.22/64*12]#139.77 + 5.22/64*np.arange(12,13)


#timing related
tweezer_ramp_down_time = 20e-3

exposure_time = 60e-3  ### exposure_time <= pgc_cooling_time
imaging_separation = 50e-3
extra_cooling_time = 150e-3
coolingimg_time = exposure_time + imaging_separation

tweezer_cam_delay = 6e-4

#AO related
coolingamp_for_img = 2.2#1.915#(output 1.2)
coolingamp_for_img_list = [2.2, 2.2]#[1.915]#[1, 1.3, 1.6, 1.9, 2.2]



# -------------------------------
# PGC at Img tweezer trap depth
# -------------------------------
#DDS related:
img_field_coolingdetune_for_pgc =  139.77 + 5.22/64*20
img_field_coolingdetune_for_pgc2 = 139.77 + 5.22/64*20  ### added for testing any heating from leakage light while AOM/TTL off
#timing related
img_field_pgc_cooling_time = 10e-3#20e-3#4e-3


#AO related
img_field_coolingamp_for_pgc = 1.5
img_field_coolingamp_for_pgc_list = 1.5 #[0.75, 1, 1.25, 1.5, 1.75, 2, 2.25 ]
#defined in previous phase
#tweezer_img_amp = 0.69#1.3




# -------------------------------
# Optical Pumping
# -------------------------------
#DDS related:
#coolingdetune_for_op_list = 139.77 - 238/64 -  5.22/64*2*np.array([1.1])
coolingdetune_for_op_list = 139.77 - 5.22/64*2*np.arange(0.0,1.0,0.2) 
coolingdetune_for_op = 139.77  -  5.22/64*2*0.6

opAOM_freq = 149
op_repump_aom_freq = 100.4
op_amp = -47#-32#-46#-46#-33

op_repump_amp = op_amp + 3 + 10
op_repump_amp_max = -11
op_amp_list = [-32, -37, -42, -45] # [-32, -33, -34, -35, -36]
depump_amp = -47#-46#-32#-32
depump_amp_list = [-32, -37, -42, -45]#[-46, -48]

#timing related

#defined in previous phase
#tweezer_ramp_down_time=tweezer_ramp_down_time

op_delay_after_switching_bfield = 50e-3 #120e-3#30e-3#50e-3

op_pump_time_list = [0, 30e-6, 100e-6, 300e-6, 1e-3,2e-3]#np.arange(30,150,30)*1e-6#[0, 30e-6, 100e-6, 300e-6, 1e-3]#[100e-6]#[0, 8e-6, 16e-6, 32e-6, 100e-6, 200e-6]#[0, 2e-6, 4e-6, 8e-6,12e-6,24e-6,48e-6]#[0,10e-6,50e-6,100e-6,200e-6]
op_pump_time = 2e-3 #125e-6 #25e-6 #

op_depump_time_list = np.array([0, 10e-3, 30e-3, 100e-3])#np.array([0,0.8e-3, 2e-3, 4e-3, 8e-3, 20e-3,30e-3])*2#[0,200e-6,500e-6,1e-3,2e-3,4e-3]
op_depump_time = 0#1e-3#2e-3#0#500e-6




bias_xv_for_op_quant_axis_list = [3.5]#np.arange(2.8,3.8,.2)#[3.2]#4.1]#,4.3,4.7,4.9]#,4.3,4.7,4.9]#,4.45,4.55]
bias_zv_for_op_quant_axis_list=[0.42]#[-0.5]
bias_yv_for_op_quant_axis = 5.5#5.5  ## 1G/V
bias_xv_for_op_quant_axis = 3.5 #4.0#4.13
bias_zv_for_op_quant_axis = 0.42#-0.5




# -------------------------------
#Adiabatically lowering trap depth
# -------------------------------
#DDS related:
#defined in previous phase
#coolingdetune_for_img = coolingdetune_for_img
#For shutting down OP light as it is the first phase after OP
opAOM_shut_freq = 130
opAOM_shut_amp = -48

#timing related
adiabatic_cool_time = 10e-3#20e-3


#defined in previous phase
#bias_xv_for_op_quant_axis_list = [4.13]#4.1]#,4.3,4.7,4.9]#,4.3,4.7,4.9]#,4.45,4.55]
#bias_zv_for_op_quant_axis_list=[0.5]#[-0.5] ### @@@ ???
#bias_yv_for_op_quant_axis = 5.5  ## 1G/V
#bias_xv_for_op_quant_axis = 4.13
#bias_zv_for_op_quant_axis = 0.5


# -------------------------------
#Push Out
# -------------------------------


#DDS related:
#coolingdetune_for_push_out_list = 139.77  -  5.22/64*2*np.array([1.55,1.75,1.95,2.15,2.35]) - 238/64
coolingdetune_for_push_out_list = 139.77  -  5.22/64*2*(np.arange(-7,11,1)*0.5+0.95) - 238/64
#this is for with the OP 4,4->5,5
#coolingdetune_for_push_out = 139.77 -  5.22/64*2*2.0 - 238/64 
#this is for without the OP 4->5 generally
#coolingdetune_for_push_out = 139.77 -  5.22/64*2*1.95 - 238/64

coolingdetune_for_op_pushout = 139.77 -  5.22/64*3.9 - 238/64
coolingdetune_for_fast_pushout = 139.77 -  5.22/64*2.9- 238/64

#coolingdetune_for_push_out_list = 139.77  - 5.22/64*np.array([3.0,2.5,2.0,3.5,4.0])
#coolingdetune_for_push_out = 139.77 -  5.22/64*2*3.0
#defined in previous phase
#opAOM_freq = opAOM_freq

push_out_amp_OPtest = -22.5# -33
push_out_amp_fastpush = 2# - 6 - 6 - 6
#push_out_amp = -8#33

push_out_time_list = np.arange(0,3,0.5)*1e-6#[100e-6]#np.arange(0,6,1)*1e-6#np.arange(0,100,16)*1e-6#np.arange(0,6,1)*1e-6#np.array([48])*1e-6#np.arange(0,50,15)*1e-6#
push_out_time = 2e-6#100e-6#6e-6#100e-6#100e-6
push_out_time_lockswitch_delay = 0#1e-3
push_out_time_total = push_out_time_lockswitch_delay*2+push_out_time


# -------------------------------
# (Phase7:) Apply UV skipped
# -------------------------------

red_high_duration = 1.2e-3 #2e-3
uv_duration = 1e-6
uv_duration_list = ks_width_list
uv_on_delay = 2e-6
#uv_pulse_delay = 1e-8
uv_release_time = 28*1e-6
#uv_freq_list =np.array([644.489])*1e6 + np.arange(0, -200, -5)*1e5#np.arange(-50, 50, 5)*1e5 #+ np.arange(-5, 5, 0.5)*1e5 #634e6 + np.arange(0, 20, 1)*1e5 #np.array([631.9])*1e6#633e6 - np.arange(0, 20, 2)*1e5
uv_freq_list = [90e6]#505.5e6 + np.arange(0, 20, 1)*2e5 #[635.44e6]#634.5e6 + np.arange(0, 15, 1)*1e5 # 631e6 + np.arange(0, 8, 0.2) *1e6#np.array([634.8])*1e6 #- np.arange(0, 90, 2)*1e5
uv_freq = 90e6# 635.45e6 #634.8*1e6
tweezer_extra_off_time_list = [1e-6]#np.array([0])*1e-6 #np.arange(0, 40, 10)*1e-6#np.arange(10, 30, 3)*1e-6#10e-6#7e-6
tweezer_extra_off_time = 1e-6#tweezer_extra_off_time_list[0]
uv_extra_delay = 1.5e-6

uv_pi_time = 282e-9#873e-9

pushout_time_afteruv = 2e-6
uv_pulse_separation = pushout_time_afteruv
rydberg_lifetime_scan_list =  np.array([3,4,5,6,7,8,9,10])*1e-6
pushdds_delay_time = 1e-6
uv_trigger_time = 1e-6

# -------------------------------
# Recap with high tweezer field
# -------------------------------
#DDS related:
#defined in previous phase
#coolingdetune_for_img = coolingdetune_for_img


#timing related
recap_duration = 100e-6
recap_hold_duration = 0
recap_ramp_duration = 50e-6#35e-6#50e-6
recap_ramp_duration_list = np.array([5e-6, 0,  10e-6, 20e-6])

tweezer_recap_delay = 2e-6 ### empirical for high recap depth 2.24V
cooling_delay_after_trap_on = 10e-6 ### make sure turning on light after tweezer on
#AO related
#tweezer_recap_amp = 0.1#tweezer_img_amp#tweezer_loading_amp #+0.1
tweezer_recap_ini_amp = 0.1*tweezer_amp_scaling
tweezer_recap_final_amp = tweezer_img_amp

#defined in previous phase
#bias_xv_for_op_quant_axis_list = [4.13]#4.1]#,4.3,4.7,4.9]#,4.3,4.7,4.9]#,4.45,4.55]
#bias_zv_for_op_quant_axis_list=[0.5]#[-0.5] ### @@@ ???
#bias_yv_for_op_quant_axis = 5.5  ## 1G/V
#bias_xv_for_op_quant_axis = 4.13
#bias_zv_for_op_quant_axis = 0.5



# -------------------------------
# Lower tweezer trap depth to an IMG depth and Image (we switch B field here)
# -------------------------------



img_num =2  ### including the one during PGC

#the time for imaging phase
delay_after_switching_bfield = 100e-3#50e-3#200e-3
img_tot_time = delay_after_switching_bfield + coolingimg_time*(img_num-1)


# -------------------------------
# tweezer wait
# -------------------------------




# -------------------------------
# Repeat
# -------------------------------
repeat_num = 80
dt = 0.02 + 0.3








