import sys
sys.path.append('../servers/control_instrument_servers/pulser/pulse_sequences')
from pulse_sequence import pulse_sequence
from labrad.units import WithUnit
from treedict import TreeDict
from six import iteritems

class sampleDDS(pulse_sequence):

    def sequence(self):
        start_first = WithUnit(10, 'us')
        on_time = WithUnit(100, 'ms')
        off_time = WithUnit(100, 'ms')

        self.addDDS('1092 Double Pass', WithUnit(0.1, 'ms'), WithUnit(250, 'ms'),
                    WithUnit(25.0, 'MHz'), WithUnit(-2.0, 'dBm'))
        """self.addDDS('422 Double Pass', WithUnit(0.1, 'ms'), WithUnit(250, 'ms'),
                    WithUnit(26.0, 'MHz'), WithUnit(-2.0, 'dBm'))
        self.addDDS('422 Double Pass', WithUnit(260, 'ms'), WithUnit(250, 'ms'),
                    WithUnit(25.0, 'MHz'), WithUnit(-2.0, 'dBm'))"""
        self.addTTL('TTL1', WithUnit(0, 'ms'), WithUnit(100, 'ms'))
        self.addTTL('TTL1', WithUnit(200, 'ms'), WithUnit(100, 'ms'))
        self.addTTL('TTL1', WithUnit(400, 'ms'), WithUnit(100, 'ms'))


if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    cs = sampleDDS(TreeDict())
    #print(cs['422 Double Pass'])
    #print(cs)
    cs.programSequence(cxn.pulser)


    cxn.pulser.start_number(2)
    cxn.pulser.wait_sequence_done()
    cxn.pulser.stop_sequence()

    # print 'DONE'
