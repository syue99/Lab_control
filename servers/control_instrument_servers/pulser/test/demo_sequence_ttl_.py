import labrad
from labrad.units import WithUnit
from pydux.lib.control.servers.script_scanner.experiment import experiment
import sys
sys.path.append('../servers/control_instrument_servers/pulser/pulse_sequences/')
from plot_sequence import SequencePlotter
import numpy as np
with labrad.connect() as cxn:
    #duration = WithUnit(5, 's')
    pulser = cxn.pulser
    pulser.new_sequence()
    channels = pulser.get_channels()
    channel_names = [chan[0] for chan in channels]
    #DDS = [('422 Double Pass', WithUnit(1, 'ms'), WithUnit(0.02, 'ms'), WithUnit(10, 'MHz'), WithUnit(-5.6, 'dBm'), WithUnit(0.0, 'deg'), WithUnit(0.0000, 'MHz'),WithUnit(0, 'dB')),
    #('422 Double Pass', WithUnit(1.02, 'ms'), WithUnit(0.02, 'ms'), WithUnit(10, 'MHz'), WithUnit(-5.6, 'dBm'), WithUnit(53.0, 'deg'), WithUnit(0.0000, 'MHz'),WithUnit(0, 'dB'))
    #]
        # program DDS
    #DDS = []
    #pulser.add_dds_pulses(DDS)
    #for i in range(3):
    
    pulser.add_ttl_pulse('TTL3', WithUnit(0, 'ms'), WithUnit(1, 'ms'))
    pulser.add_ttl_pulse('TTL2', WithUnit(0, 'ms'), WithUnit(10, 'ms'))
    #    pulser.add_ttl_pulse('TTL3', WithUnit(20*i, 'ms'), WithUnit(10, 'ms'))
    #pulser.add_ttl_pulse('TTL5', WithUnit(5, 'ms'), WithUnit(300, 'us'))


    pulser.program_sequence()
    #counts = experiment.repeat_run_with_readouts(2,1)

    #ttl = cxn.pulser.human_readable_ttl()
    #dds_ = cxn.pulser.human_readable_dds()
    #print(channels,dds_)
    #sp = SequencePlotter(np.asarray(ttl),dds_, np.array(channels))
    #sp.makePlot()
    #print(counters)
    pulser.start_number(100)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
