import labrad
from labrad.units import WithUnit
import numpy as np
#from pydux.lib.control.servers.script_scanner.experiment import experiment

# #this is the delay time in s between the camera and a TTL pulse 
# camera_delay = -0.034

#TTL channel number

#############
#### analog channels
offsetlock = 16


#############
#### digital channels
two_d_motAOM = 25 #### port3, line1, i.e, channel_num//8, channel_num%8
three_d_motAOM = 27 #### port3, line3
repump_motAOM = 28 #### port3, line4

imgAOM = 26 #### port3, line2
push_beamAOM = 29 #### port3, line5

#### 3D MOT coils
### Note that for the two coils, TTL on corresponds to B field off
mot_coil = 0    #### port0, line0

tweezer_camera_trigger = 2   #### port0, line2


#TTL.pulseon: unit in s 
#mot2d_loading_time = 5
mot_loading_time = 5  ### when set to 5, we can only see a bright MOT for 2.5s....
#mot3d_B_off_time = 1
exposure_time = 1e-3
image_time = exposure_time+ 10
image_delay = 2e-3 ### delay after turning off MOT B field
image_num = 10
# mot_off1 = 0.2
# mot_off2 = 0.2


 ### exposure time + extra 10ms (seems enough for readout)


with labrad.connect() as cxn:
    ao = cxn.aoserver
    ttl = cxn.finitedopulses

#first we load atoms

    #duration in unit of s
    duration = mot_loading_time + 0.001  #np.max([image_delay + image_num*image_time, 0.2]) ### having at least 0.2s turning off MOT
    
    
    #every exp cycle for duration S
    ao.blankwaveform(duration)
    ttl.blankwaveform(duration)

    # # #### Turn off MOT B field at the beginning 
    ttl.PulseOn(mot_coil, 0, mot_loading_time) #### +0.1 here is just to keep the B field off till the end of the duration so that it remains off afterwards
    #### Note that for both TTL and AO pulses, the channels remain at the status set at the end of the waveform duration
    

    # #### load into MOT and tweezer, tweezer always on 
    # #2D MOT
    ttl.PulseOn(two_d_motAOM, 0, mot_loading_time)
    
    #Push beam controlling flux from 2D MOT
    ttl.PulseOn(push_beamAOM, 0, mot_loading_time)#tot_mot_loading_time)

    #3D MOT
    ttl.PulseOn(three_d_motAOM, 0, mot_loading_time)
    #ttl.PulseOn(three_d_motAOM, mot_off1, tot_mot_loading_time)
    #Repump
    ttl.PulseOn(repump_motAOM, 0, mot_loading_time)
    #ttl.PulseOn(repump_motAOM, mot_off1, tot_mot_loading_time)
    

    # ### change the detuning
    #ao.setvoltagepulse(offsetlock, tot_mot_loading_time, mot_off, WithUnit(-0.5,"V"))
    # ##### in format (channel num, start time, duration, voltage), The voltage corresponds to -10MHz/V i.e., -2Gamma/V for voltage between -7 and 7V.
    
 
    for i in range(image_num):
        ttl.PulseOn(three_d_motAOM, mot_loading_time + i*image_time+ image_delay-1e-3, exposure_time+2e-3) ### Turn on cooling/imaging and repump light 1ms before imaging
        ttl.PulseOn(repump_motAOM, mot_loading_time + i*image_time+ image_delay-1e-3, exposure_time+2e-3)
        
        ttl.PulseOn(tweezer_camera_trigger, mot_loading_time + i*image_time+ image_delay, 1e-5)  ### the delay before different images need to be slightly longer than the exposure time. I use 30ms delay for 20ms exposure.
    
    #ttl.PulseOn(mot_coil, duration-0.001, 1e-3)
    #ttl.PulseOn(mot_coil, duration-0.001, 1e-3)
    #ttl.PulseOn(mot_coil, duration-0.001, 1e-3)
    ### camera delay time is neglected here




    #for counter in range(3):   
    #    ttl.pulseon(0,(1+counter )*1e-4, 1e-6)
    #    ttl.pulseon(1,counter *2e-5, 1e-5)
    #    ttl.pulseon(2,counter *1e-5+1e-5, 1e-6 )
    #ttl.pulseon(0,2e-4,1e-6)
    #ttl.pulseon(1,2e-4,2e-6)
    #ttl.pulseon(2,2e-4,3e-6)
    #ttl.pulseon(3,2e-4,4e-6)
        #print("Newexp1")

    #ao.setVoltagePulse(2,0,1e-4,WithUnit(2,"V"))
    #ao.setVoltagePulse(2,2e-4,4e-4,WithUnit(5,"V"))
    #ao.setVoltagePulse(ch=0, t_start=0, t_len=1e-4, voltage=WithUnit(2,"V"))


    
    #!!!AO must be in front of the TTL
    ##If we use TTL for the pulse for triggering things, it will need to be in the last
    #ao.runWaveform(1)
    #while True:
    ttl.runwaveform(1)


    