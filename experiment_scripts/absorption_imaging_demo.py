import labrad
from labrad.units import WithUnit
#from pydux.lib.control.servers.script_scanner.experiment import experiment

#this is the delay time in s between the camera and a TTL pulse 
camera_delay = -0.034

#TTL channel number

#camera_channel is for allied vision
camera_trigger = 24
two_d_motAOM = 25
three_d_motAOM = 27
repump_motAOM = 28
imgAOM = 26

mot_top_coil = 1
mot_bot_coil = 0

#TTL.pulseon: unit in s 

with labrad.connect() as cxn:
    duration = WithUnit(5, 's')
    #ao = cxn.aoserver
    ttl = cxn.finitedopulses
    
    
    #every exp cycle for 2S
    ttl.blankwaveform(2)
    #ao.blankwaveform(40e-4)

    #flush the camera 
    ttl.PulseOn(camera_trigger, 0, 1e-5) ### channel_num, star time, duration in s, note that camera exporesure time is set in its own software, here is just requesting a pic in this time

    #2D MOT
    ttl.PulseOn(two_d_motAOM, 0.4, 0.9999)
    #3D MOT
    ttl.PulseOn(three_d_motAOM, 0.4, 0.9999)
    #Repump
    ttl.PulseOn(repump_motAOM, 0.4, 0.9999)


    #Abs Image with MOT: image right after turning off 3D MOT light and B field
    ttl.PulseOn(mot_top_coil, 1.39, 0.1)
    ttl.PulseOn(mot_bot_coil, 1.39, 0.1)
    #first Camera with signal
    ttl.PulseOn(camera_trigger, 1.4 + camera_delay, 1e-5)
    #img light 100us 
    ttl.PulseOn(imgAOM, 1.4, 1e-4)
    #also put rempump on
    ttl.PulseOn(repump_motAOM, 1.4, 1e-4)

    #Abs image without MOT: simply waiting for 100ms for the MOT to disappear (100ms should be enough since there is no MOT light)
    ttl.PulseOn(camera_trigger, 1.5 + camera_delay, 1e-5)
    #img light 100us 
    ttl.PulseOn(imgAOM, 1.5, 1e-4)
    #also put rempump on
    ttl.PulseOn(repump_motAOM, 1.5, 1e-4)

    #background image
    ttl.PulseOn(camera_trigger, 1.6 + camera_delay, 1e-5)  

    #ao = cxn.aoserver
    #ao.setvoltagepulse(0,0,1e-4,WithUnit(2,"V"))
    #ao.runWaveform(1)
    
                       


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
    ttl.runwaveform(1)


    