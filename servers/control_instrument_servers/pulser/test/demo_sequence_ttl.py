import labrad
from labrad.units import WithUnit
from pydux.lib.control.servers.script_scanner.experiment import experiment

with labrad.connect() as cxn:
    duration = WithUnit(5, 's')
    pulser = cxn.pulser
    pulser.new_sequence()
    channels = pulser.get_channels()
    channel_names = [chan[0] for chan in channels]

    for i in range(20):
    #pulser.add_ttl_pulse('TTL1', WithUnit(0, 'ms'), WithUnit(2, 'ms'))
        pulser.add_ttl_pulse('TTL3', WithUnit(20*i, 'ms'), WithUnit(10, 'ms'))
    #pulser.add_ttl_pulse('TTL5', WithUnit(5, 'ms'), WithUnit(300, 'us'))


    pulser.program_sequence()
    #counts = experiment.repeat_run_with_readouts(2,1)

    #ttl = cxn.pulser.human_readable_ttl()
    #sp = SequencePlotter(ttl.asarray,None, channels)
    #sp.makePlot()
    #print(counters)
    pulser.start_number(1)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
