import labrad
from labrad.units import WithUnit
#from pydux.lib.control.servers.script_scanner.experiment import experiment

with labrad.connect() as cxn:
    duration = WithUnit(0.06, 's')
    ao = cxn.aoserver
    ttl = cxn.finitedopulses
    ttl.blankwaveform(40e-4)
    ao.blankwaveform(40e-4)
    #print(ao.returnData())

    #pulser = cxn.pulser


    #pulser.line_trigger_state(True)
    #pulser.new_sequence()
    #pulser.add_ttl_pulse('TTL2', WithUnit(0.5, 'us'), WithUnit(0.1, 'us'))
    #DDS = [('DDS1', WithUnit(0.5, 'us'), WithUnit(100, 'us'), WithUnit(139.73, 'MHz'), WithUnit(-15.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #       ('DDS1', WithUnit(100.5, 'us'), WithUnit(100, 'ms'), WithUnit(140.23, 'MHz'), WithUnit(-20.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),]
        #far_detuned/repumper Cooling
        #(name, start, dur, freq, ampl, phase, ramp_rate, amp_ramp_rate)

        #Group 1 Raman beams
    #    	('DDS1', WithUnit(0.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
	#        ('DDS1', WithUnit(1000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(30.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(2000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(60.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(3000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(90.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(4000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(120.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(5000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(150.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(6000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(180.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(7000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(210.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(8000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(240.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(9000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(270.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(10000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(300.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(11000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(330.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS1', WithUnit(12000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(360.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #        ('DDS2', WithUnit(0.5, 'us'), WithUnit(13, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.1, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS3', WithUnit(0.5, 'us'), WithUnit(13, 'ms'), WithUnit(230, 'MHz'), WithUnit(-9.5, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        	#('DDS4', WithUnit(0.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
	        #('DDS4', WithUnit(1000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(30.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(2000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(60.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(3000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(90.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(4000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(120.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(5000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(150.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(6000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(180.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(7000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(210.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(8000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(240.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(9000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(270.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(10000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(300.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(11000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(330.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
            #('DDS4', WithUnit(12000.5, 'us'), WithUnit(1, 'ms'), WithUnit(230, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(360.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #]        
                       

    #    ('DDS1', WithUnit(0.1, 'ms'), WithUnit(0.1, 'ms'), WithUnit(125, 'MHz'), WithUnit(-3.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
    #    ('DDS1', WithUnit(0.5, 'ms'), WithUnit(2.2, 'ms'), WithUnit(250, 'MHz'), WithUnit(-3.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(5000, 'dB')),
    #    ('DDS1', WithUnit(12.5, 'ms'), WithUnit(0.5, 'ms'), WithUnit(250, 'MHz'), WithUnit(-3.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB'))
        #('DDS2', WithUnit(1, 'ms'), WithUnit(10, 'ms'), WithUnit(125, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(90.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #('DDS2', WithUnit(0.2, 'ms'), WithUnit(0.1, 'ms'), WithUnit(250, 'MHz'), WithUnit(-3.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #('DDS1', WithUnit(1, 'ms'), WithUnit(10, 'ms'), WithUnit(125, 'MHz'), WithUnit(-10.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB')),
        #('DDS1', WithUnit(12, 'ms'), WithUnit(1, 'ms'), WithUnit(125, 'MHz'), WithUnit(-3.0, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0, 'MHz'),WithUnit(0, 'dB'))
    #]


    for counter in range(3):   
        ttl.pulseon(0,(1+counter )*1e-4, 1e-6)
        ttl.pulseon(1,counter *2e-5, 1e-5)
        ttl.pulseon(2,counter *1e-5+1e-5, 1e-6 )
    ttl.pulseon(0,2e-4,1e-6)
    ttl.pulseon(1,2e-4,2e-6)
    ttl.pulseon(2,2e-4,3e-6)
    ttl.pulseon(3,2e-4,4e-6)
        #print("Newexp1")

    ao.setVoltagePulse(2,0,1e-4,WithUnit(2,"V"))
    ao.setVoltagePulse(2,2e-4,4e-4,WithUnit(5,"V"))
    ao.setVoltagePulse(ch=0, t_start=0, t_len=1e-4, voltage=WithUnit(2,"V"))

    #ao.setVoltagePulse(2,0,5e-6,WithUnit(3,"V"))

    ao.ArbWave(2, 2e-5, 1e-3, [1,2], [100,100], [0,0], [1e-4,1e-4], [1e-4,1e-4])
    ao.ArbWave(2, 2e-5, 5e-3, [1,2,3], [500,1000,2000], [0,0,0], [1e-3,1e-3,1e-3], [1e-4,1e-4,1e-4])


    #ao.ArbWave_offset(2, 2e-5, 100e-5, [5], [0],[10000], [0], [100e-2], [0])
    #ao.setVoltagePulse(2,4.5e-5,1e-5,WithUnit(3,"V"))
    #ao.ArbWave(2, 5.5e-5, 5e-5, [10], [10000], [89.5], [2.5e-5], [0])


    #for i in range(5):
    #    ao.ArbWave_offset(2, 2e-5+i*10e-5, 4e-5, [5], [0],[10000], [0], [2e-5], [0])
    #    ao.setVoltagePulse(2,4e-5+i*10e-5,4e-5,WithUnit(0.3,"V"))
    #    ao.ArbWave_offset(2, 8e-5+i*10e-5, 4e-5, [5], [0],[10000], [89.5], [2e-5], [0])

    #ao.setVoltagePulse(2, 2e-5, 4e-5, WithUnit(1,"V"))
    # ch, t_start, t_len, ampList, aList, pulseDuration, waitTime

    #ao.BH_Window_function(2, 5e-5, 5e-5, [5], [1], [5e-5], [0])
    #ao.BH_Window_function(2, 11e-5, 10e-5, [5], [0.5], [10e-5], [0])
    #ao.BH_Window_function(2, 22e-5, 20e-5, [5], [0.5], [20e-5], [0])

    #ao.setVoltagePulse(5, 5e-5, 5e-5, WithUnit(4,"V"))
    #ao.setVoltagePulse(5, 11e-5, 10e-5, WithUnit(4,"V"))
    #ao.setVoltagePulse(5, 22e-5, 20e-5, WithUnit(4,"V"))


    #pulser.add_dds_pulses(DDS)
    #for i in range(100):

    #pulser.add_ttl_pulse('TTL1', WithUnit(0, 'ms'), WithUnit(2, 'ms'))
    #    pulser.add_ttl_pulse('TTL5', WithUnit(5*i, 'us'), WithUnit(40, 'ns'))
    #pulser.add_ttl_pulse('TTL5', WithUnit(5, 'ms'), WithUnit(300, 'us'))


    #pulser.program_sequence()
    #counts = experiment.repeat_run_with_readouts(2,1)

    #ttl = cxn.pulser.human_readable_ttl()
    #sp = SequencePlotter(ttl.asarray,None, channels)
    #sp.makePlot()
    #print(counters)
    
    
    #!!!AO must be in front of the TTL
    ##If we use TTL for the pulse for triggering things, pulser will need to be in the last
    ao.runWaveform(1)
    ttl.runwaveform(1)
    #pulser.start_number(5)
    #pulser.wait_sequence_done()
    #pulser.stop_sequence()

    