class channelConfiguration(object):
    """Stores complete configuration for each of the channels."""
    def __init__(self, channelNumber, ismanual, manualstate, manualinversion, autoinversion):
        self.channelnumber = channelNumber
        self.ismanual = ismanual
        self.manualstate = manualstate
        self.manualinv = manualinversion
        self.autoinv = autoinversion


class ddsConfiguration(object):
    """Stores complete configuration of each DDS board."""
    def __init__(self, address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
        self.channelnumber = address
        self.allowedfreqrange = allowedfreqrange
        self.allowedamplrange = allowedamplrange
        self.frequency = frequency
        self.amplitude = amplitude
        self.state = True
        self.boardfreqrange = args.get('boardfreqrange', (0.0, 2000.0))
        self.boardramprange = args.get('boardramprange', (0.000113687, 7.4505806))
        self.board_amp_ramp_range = args.get('board_amp_ramp_range', (0.00174623, 22.8896))
        self.boardamplrange = args.get('boardamplrange', (-48.0, 6.0))
        self.boardphaserange = args.get('boardphaserange', (0.0, 360.0))
        self.off_parameters = args.get('off_parameters', (0.0, -48.0))
        self.phase_coherent_model = args.get('phase_coherent_model', True)
        self.remote = args.get('remote', False)
        self.name = None  # will get assigned automatically


class remoteChannel(object):
    def __init__(self, ip, server, **args):
        self.ip = ip
        self.server = server
        self.reset = args.get('reset', 'reset_dds')
        self.program = args.get('program', 'program_dds')


class hardwareConfiguration(object):
    channelTotal = 32
    timeResolution = '40.0e-9'  # seconds
    timeResolvedResolution = 10.0e-9
    maxSwitches = 1022
    resetstepDuration = 3  # duration of advanceDDS and resetDDS TTL pulses in units of timesteps
    # range for normal pmt counting, the minimum collect time could not be less than 0.001s.
    # Fred change this to test it
    collectionTimeRange = (0.001, 5.0)
    sequenceTimeRange = (0.0, 85.0)  # range for duration of pulse sequence
    isProgrammed = False
    sequenceType = None  # none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal'  # default PMT mode
    collectionTime = {'Normal': 0.100, 'Differential': 0.100}  # default counting rates
    okDeviceID = 'Pulser 2'
    okDeviceFile = 'photon_2015_7_13.bit'
    lineTriggerLimits = (0, 15000)  # values in microseconds
    secondPMT = False
    DAC = False

    # name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {
        # Internal866 is in pulser firmware, this is the required channel name.
        'Internal866': channelConfiguration(0, False, False, False, True),  # camera
        # 866DP is in pulser firmware, this is the required channel name.
        '866DP': channelConfiguration(1, False, False, True, False),
        # Voltage reference for the output voltage of the breakout board
        'VoltageRef': channelConfiguration(2, False, False, False, True),
        'TTL1': channelConfiguration(3, True, True, False, False),  # manual compatible
        # manual compatible
        'TTL2': channelConfiguration(4, True, True, False, False),
        'TTL3': channelConfiguration(5, False, False, False, False),  # manual compatible
        'TTL4': channelConfiguration(6, False, False, False, False),  # manual compatible
        'TTL5': channelConfiguration(7, False, False, False, False),  # manual compatible
        'TTL6': channelConfiguration(8, False, False, False, False),  # manual compatible
        'TTL7': channelConfiguration(9, False, False, False, False),  # manual compatible
        'TTL8': channelConfiguration(10, False, False, False, False),  # manual compatible
        'TTL11': channelConfiguration(11, False, False, False, False),  # manual compatible
        'TTL12': channelConfiguration(12, False, True, False, False),
        'TTL13': channelConfiguration(13, False, False, False, False),
        'TTL14': channelConfiguration(14, False, False, False, False),
        'TTL15': channelConfiguration(15, False, False, False, False),
        'DiffCountTrigger': channelConfiguration(16, False, False, False, False),
        # needed to activate time tagged photon counting
        'TimeResolvedCount': channelConfiguration(17, False, False, False, False),
        'AdvanceDDS': channelConfiguration(18, False, False, False, False),
        'ResetDDS': channelConfiguration(19, False, False, False, False),

        # triggering for analog board, needed to count photons without time tagging.
        'ReadoutCount': channelConfiguration(20, False, False, False, False),
        # triggering for analog board
        'TTL21': channelConfiguration(21, False, False, False, False),
        'TTL22': channelConfiguration(22, True, True, False, False),
        'TTL23': channelConfiguration(23, True, True, False, False),
        # for plotting the clock purpose only
        'TTL24': channelConfiguration(24, False, False, False, False),
        # reserve for weak probe line scan 650
        'TTL25': channelConfiguration(25, False, False, False, False),
        # reserve for weak probe line scan 493
        'TTL26': channelConfiguration(26, False, True, False, False),
        'TTL27': channelConfiguration(27, False, False, False, False),
        'TTL28': channelConfiguration(28, False, False, False, False),
        'TTL29': channelConfiguration(29, False, False, False, False),
        'TTL30': channelConfiguration(30, False, False, False, False),
        'TTL31': channelConfiguration(31, False, True, False, False),
    }
    # address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    # Note here you must configure the correct number of DDS channel here, otherwise 
    # the channel with the lowest channel number will get stuck while programming dds pulses
    remoteChannels = {
    }
    ddsDict = {
        '422 Double Pass': ddsConfiguration(0, (0.0, 800.0), (-48.0, -1.0), 25, -2),
        '1092 Double Pass': ddsConfiguration(1, (0.0, 800.0), (-48.0, -6.0), 340, -9.0),
    }
    '''ddsDict = {
        '422 Double Pass': ddsConfiguration(0, (0.0, 800.0), (-48.0, -1.0), 25, -2),
        '1092 Double Pass': ddsConfiguration(1, (0.0, 800.0), (-48.0, 3.0), 25, -48.0),
        '468 Double Pass': ddsConfiguration(2, (0.0, 800.0), (-48.0, 3.0), 220.0, -48.0),
        '1079 Double Pass': ddsConfiguration(3, (0.0, 800.00), (-48.0, 3.0), 300.0, -48.0),
        '708 Double Pass': ddsConfiguration(4, (0.0, 800.0), (-48.0, 3.0), 200.0, -48.0),
        '802 Double Pass': ddsConfiguration(5, (0.0, 800.0), (-48.0, 3.0), 200.0, -48.0),
        '674 Double Pass': ddsConfiguration(6, (0.0, 800.0), (-48.0, 3.0), 80.0, -48.0),
        'LF': ddsConfiguration(7, (0.0, 10.0), (-48.0, 3.0), 2.0, -48.0),
    }
    remoteChannels = {
    }'''
