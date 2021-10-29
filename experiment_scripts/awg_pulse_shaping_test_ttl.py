import labrad
from labrad.units import WithUnit
from pydux.lib.control.servers.script_scanner.experiment import experiment

with labrad.connect() as cxn:
    duration = WithUnit(5, 's')
    pulser = cxn.pulser
    pulser.new_sequence()
    for i in range(500):
        pulser.add_ttl_pulse('TTL1', WithUnit(0+i*2, 'ms'), WithUnit(10, 'us'))
    #    pulser.add_ttl_pulse('TTL5', WithUnit(5*i, 'us'), WithUnit(40, 'ns'))
    #pulser.add_ttl_pulse('TTL5', WithUnit(5, 'ms'), WithUnit(300, 'us'))


    pulser.program_sequence()

    pulser.start_number(10)
    pulser.wait_sequence_done()
    pulser.stop_sequence()
