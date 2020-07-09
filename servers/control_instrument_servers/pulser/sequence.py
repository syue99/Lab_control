import numpy
import array
from six import iteritems
from builtins import range

try:
    from config.pulser.hardwareConfiguration import hardwareConfiguration
except BaseException:
    from pydux.lib.config.pulser.hardwareConfiguration import hardwareConfiguration

from decimal import Decimal


class Sequence():
    """Sequence for programming pulses."""

    def __init__(self, parent):
        self.parent = parent
        self.channelTotal = hardwareConfiguration.channelTotal
        self.timeResolution = Decimal(hardwareConfiguration.timeResolution)
        self.MAX_SWITCHES = hardwareConfiguration.maxSwitches
        self.resetstepDuration = hardwareConfiguration.resetstepDuration
        # dictionary in the form time:which channels to switch
        # time is expressed as timestep with the given resolution
        # which channels to switch is a channelTotal-long array with 1 to switch
        # ON, -1 to switch OFF, 0 to do nothing
        self.switchingTimes = {0: numpy.zeros(self.channelTotal, dtype=numpy.int8)}
        # keeps track of how many switches are to be performed (same as the number
        # of keys in the switching Times dictionary"
        self.switches = 1
        # dictionary for storing information about dds switches, in the format:
        # timestep: {channel_name: integer representing the state}
        self.ddsSettingList = []
        self.advanceDDS = hardwareConfiguration.channelDict['AdvanceDDS'].channelnumber
        self.resetDDS = hardwareConfiguration.channelDict['ResetDDS'].channelnumber

    def addDDS(self, name, start, num, typ):
        timeStep = self.secToStep(start)
        self.ddsSettingList.append((name, timeStep, num, typ))

    def addPulse(self, channel, start, duration):
        """Adding TTL pulse, times are in seconds."""
        start = self.secToStep(start)
        duration = self.secToStep(duration)
        self._addNewSwitch(start, channel, 1)
        self._addNewSwitch(start + duration, channel, -1)

    def extendSequenceLength(self, timeLength):
        """Allows extension of total length of the sequence."""
        timeLength = self.secToStep(timeLength)
        self._addNewSwitch(timeLength, 0, 0)

    def secToStep(self, sec):
        """Converts seconds to time steps."""
        start = '{0:.9f}'.format(sec)  # round to nanoseconds
        start = Decimal(start)  # convert to decimal
        step = (start / self.timeResolution).to_integral_value()
        step = int(step)
        return step

    def numToHex(self, number):
        number = int(number)
        b = bytearray(4)
        b[2] = number % 256
        b[3] = (number // 256) % 256
        b[0] = (number // 65536) % 256
        b[1] = (number // 16777216) % 256
        # print numpy.array([b[0],b[1],b[2],b[3]])
        return b

    def _addNewSwitch(self, timeStep, chan, value):
        if timeStep in self.switchingTimes:
            if self.switchingTimes[timeStep][chan]:  # checks if 0 or 1/-1
                # if set to turn off, but want on, replace with zero, fixes error adding 2
                # TTLs back to back
                if self.switchingTimes[timeStep][chan] * value == -1:
                    self.switchingTimes[timeStep][chan] = 0
                else:
                    raise Exception(
                        'Double switch at time {} for channel {}'.format(timeStep, chan))
            else:
                self.switchingTimes[timeStep][chan] = value
        else:
            if self.switches == self.MAX_SWITCHES:
                raise Exception("Exceeded maximum number of switches {}".format(self.switches))
            self.switchingTimes[timeStep] = numpy.zeros(self.channelTotal, dtype=numpy.int8)
            self.switches += 1
            self.switchingTimes[timeStep][chan] = value

    def progRepresentation(self, parse=True):
        if parse:
            self.ddsSettings = self.parseDDS()
            self.ttlProgram = self.parseTTL()
        return self.ddsSettings, self.ttlProgram

    def userAddedDDS(self):
        return bool(len(self.ddsSettingList))

    def parseDDS(self):
        """Parses DDS switches.

        Parses DDS switches to binary strings and programs self.advanceDDS and self.resetDDS TTL
        switches to trigger DDS switches.

        Variables:
            state saves the parameter (frequency, amplitude, etc.) of each DDS channels.
                The intitial state is off for all channels that are used in the pulse sequence.
                For channels that are not used in the pulse sequence their current state is
                used. So the current state of channels not used in a pulse sequence will not
                be changed, if on, they will remain on, if off, they stay off.
            pulses_end saves the time and type of operation for the last switch of each channel.
                Type of operation is "start" or "stop", corresponding to the start and stop of a
                pulse. dds_program saves the pulse sequence for each channel in binary format.
            entries is a list of switches sorted by times.
                Each element in entries consists of (name, start, num, type):
                name: DDS channel name.
                start: time of the switch.
                num: parameter in num representation to switch to (frequency, amplitude, etc.).
                type: "start" or "stop".
            possibleError saves possible errors during parsing. Format is (time, error_str).
                Default to be (0, '') - no error.
            lastTime saves the time of last parsed switch in all channels.
                lastTime is updated when a switch is parsed.

        Parsing logic:
            A while structure loops through all switches in the order of time.
            For each switch at a time after lastTime (initial value 0), self.advanceDDS
                is programmed to be on to trigger the switch. If two switches on different
                channels happen at the same time, self.advanceDDS is only needed to be triggered
                once. self._addNewSwitch is called twice for each trigger to turn on and off
                TTL on the self.advanceDDS channel.
                Note: Switch time cannot be 0, otherwise the switch does not program.
            state is changed if a switch changes the parameter for a DDS channel. state is parsed
                and added into dds_program when lastTime changes.
            Overlaping of DDS pulses on the same channel is not allowed. A pulse can start at the
                same time as the previous pulse ends on the same channel.
            After all switches are parsed, self.resetDDS is triggered to reset DDSes.
        """
        if not self.userAddedDDS():
            return None
        channels_in_sequence = list(set([kk[0] for kk in self.ddsSettingList]))
        state = self.parent._getCurrentDDSWithOffChannels(channels_in_sequence)
        initial_state = self.parent._getCurrentDDS()
        # time / boolean whether in a middle of a pulse
        pulses_end = {}.fromkeys(state, (0, 'stop'))
        dds_program = {}.fromkeys(state, b'')
        lastTime = 0
        entries = sorted(self.ddsSettingList, key=lambda t: t[1])  # sort by starting time
        possibleError = (0, '')
        while True:
            try:
                name, start, num, typ = entries.pop(0)
            except IndexError:
                if start == lastTime:
                    # still have unprogrammed entries
                    self.addToProgram(dds_program, state)
                    self._addNewSwitch(lastTime, self.advanceDDS, 1)
                    self._addNewSwitch(lastTime + self.resetstepDuration, self.advanceDDS, -1)
                # add termination
                for name in dds_program:
                    dds_program[name] += b'\x00\x00'
                # at the end of the sequence, reset dds
                lastTTL = max(self.switchingTimes.keys())
                self._addNewSwitch(lastTTL, self.resetDDS, 1)
                self._addNewSwitch(lastTTL + self.resetstepDuration, self.resetDDS, -1)
                return dds_program
            end_time, end_typ = pulses_end[name]
            if start > lastTime:
                # the time has advanced, so need to program the previous state
                if possibleError[0] == lastTime and len(possibleError[1]):
                    raise Exception(possibleError[1])  # if error exists and belongs to that time
                if lastTime == 0:
                    self.addToProgram(dds_program, initial_state)
                    self._addNewSwitch(1, self.advanceDDS, 1)
                    self._addNewSwitch(1 + self.resetstepDuration, self.advanceDDS, -1)
                    self.addToProgram(dds_program, state)
                else:
                    self.addToProgram(dds_program, state)
                if not lastTime == 0:
                    self._addNewSwitch(lastTime, self.advanceDDS, 1)
                    self._addNewSwitch(lastTime + self.resetstepDuration, self.advanceDDS, -1)
                lastTime = start
            if start == end_time:
                # overwrite only when extending pulse
                if end_typ == 'stop' and typ == 'start':
                    possibleError = (0, '')
                    state[name] = num
                    pulses_end[name] = (start, typ)
                elif end_typ == 'start' and typ == 'stop':
                    possibleError = (0, '')
            elif end_typ == typ:
                possibleError = (start, 'Found Overlap Of Two Pulses for channel {}'.format(name))
                state[name] = num
                pulses_end[name] = (start, typ)
            else:
                state[name] = num
                pulses_end[name] = (start, typ)

    def addToProgram(self, prog, state):
        for name, num in iteritems(state):
            if not hardwareConfiguration.ddsDict[name].phase_coherent_model:
                buf = self.parent._intToBuf(num)
            else:
                buf = self.parent._intToBuf_coherent(num)
            prog[name] += buf

    def parseTTL(self):
        """Returns the representation of the sequence for programming the FPGA."""
        rep = b''
        lastChannels = numpy.zeros(self.channelTotal)
        powerArray = 2**numpy.arange(self.channelTotal, dtype=numpy.uint64)
        for key, newChannels in sorted(iteritems(self.switchingTimes)):
            channels = lastChannels + newChannels  # computes the action of switching on the state
            if (channels < 0).any():
                raise Exception('Trying to switch off channel that is not already on')
            channelInt = numpy.dot(channels, powerArray)
            # converts the new state to hex and adds it to the sequence
            rep = rep + self.numToHex(key) + self.numToHex(channelInt)
            lastChannels = channels
        rep = rep + 2 * self.numToHex(0)  # adding termination
        return rep

    def humanRepresentation(self):
        """Returns the human readable version of the sequence for FPGA for debugging."""
        dds, ttl = self.progRepresentation(parse=False)
        ttl = self.ttlHumanRepresentation(ttl)
        dds = self.ddsHumanRepresentation(dds)
        return ttl, dds

    def ddsHumanRepresentation(self, dds):
        program = []
        print(dds)
        for name, buf in iteritems(dds):
            print("name is ", name)
            arr = array.array('B', buf)
            arr = arr[:-2]  # remove termination
            channel = hardwareConfiguration.ddsDict[name]
            coherent = channel.phase_coherent_model
            freq_min, freq_max = channel.boardfreqrange
            ampl_min, ampl_max = channel.boardamplrange

            def chunks(l, n):
                """ Yield successive n-sized chunks from l."""
                for i in range(0, len(l), n):
                    yield l[i:i + n]
            if not coherent:
                for a, b, c, d in chunks(arr, 4):
                    freq_num = (256 * b + a)
                    ampl_num = (256 * d + c)
                    freq = freq_min + freq_num * (freq_max - freq_min) / float(16**4 - 1)
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / float(16**4 - 1)
                    program.append((name, freq, ampl))
            else:
                for a0, a1, amp0, amp1, a2, a3, a4, a5, f0, f1, f2, f3, f4, f5, f6, f7, in chunks(
                        arr, 16):
                    freq_num = 256**2 * (256 * f7 + f6) + (256 * f5 + f4)
                    ampl_num = 256 * amp1 + amp0
                    freq = freq_min + freq_num * (freq_max - freq_min) / float(16**8 - 1)
                    print("freq is ", freq)
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / float(16**4 - 1)
                    print(" ampl is ", ampl)
                    program.append((name, freq, ampl))
        return program

    def ttlHumanRepresentation(self, rep):
        arr = numpy.frombuffer(rep, dtype=numpy.uint16)
        # once decoded, need to be able to manipulate large numbers
        arr = numpy.array(arr, dtype=numpy.uint32)
        # arr = numpy.array(rep,dtype = numpy.uint16)
        arr = arr.reshape(-1, 4)
        times = (65536 * arr[:, 0] + arr[:, 1]) * float(self.timeResolution)
        channels = (65536 * arr[:, 2] + arr[:, 3])

        def expandChannel(ch):
            """Function for getting the binary representation, i.e 2**32 is 1000...0."""
            expand = bin(ch)[2:].zfill(32)
            reverse = expand[::-1]
            return reverse

        channels = list(map(expandChannel, channels))
        return numpy.vstack((times, channels)).transpose()