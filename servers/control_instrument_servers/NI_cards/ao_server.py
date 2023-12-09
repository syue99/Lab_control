import PyDAQmx
import dill as pickle
import numpy
import numpy as np
from labrad.server import LabradServer, setting


def flatPulse(t, args, idx):
    w = args['durationList'][idx]
    riseTime = args['riseTimeList'][idx]
    tStart = t[0]
    if w < 2 * riseTime:
        return 0
    elif riseTime <= 0:
        return 1
    logist = lambda t, t0, tau: 1 / (1 + np.exp(-(t - t0) * 10 / tau))
    p = lambda t: (logist(t, tStart + riseTime / 2, riseTime) - logist(t, tStart + w - riseTime / 2, riseTime))
    p_norm = (p(t) - p(tStart)) / (1 - p(tStart))
    return np.clip(p_norm, a_min=0, a_max=1)


class AOServer(LabradServer):
    name = "AOServer"

    nCh = 28
    targetSampleRate = 250e3

    channel_string = "Dev3/ao0:27"

    def initServer(self):
        self.sampleClockDivider = int(round(1e7 / self.targetSampleRate))
        self.sampleRate = 1e7 / self.sampleClockDivider

        print("Initializing AO server. Sample rate = %f Hz. Divider = %d" % (self.sampleRate, self.sampleClockDivider))
        pass

    def stopServer(self):
        pass

    @setting(2, "getSampleRate", returns="v[]")
    def getSampleRate(self, c):
        return self.sampleRate

    @setting(1, "setStaticVoltage", ch="i", v="v")
    def setStaticVoltage(self, c, ch, v):

        if ch < 0 or ch > 31:
            print("Error: channel (%d) out of range" % ch)
            return

        vinVolts = v['V']

        if vinVolts < -10.0 or vinVolts > 10.0:
            print("Error: Voltage (%f) out of range" % vinVolts)
            return
        if ch == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return

        chStr = 'PXI1Slot2/ao' + str(ch)

        self.cleanupTask(c)

        taskHandle = PyDAQmx.TaskHandle()
        PyDAQmx.DAQmxCreateTask(0, taskHandle)

        # (TaskHandle taskHandle,
        # const char physicalChannel[],
        # const char nameToAssignToChannel[],
        # float64 minVal,
        # float64 maxVal,
        # int32 units,
        # const char customScaleName[]);
        PyDAQmx.DAQmxCreateAOVoltageChan(taskHandle,
                                         chStr,
                                         "",
                                         -10.0,
                                         10.0,
                                         PyDAQmx.DAQmx_Val_Volts,
                                         "")

        nWritten = ctypes.c_long(0)

        # (TaskHandle taskHandle,
        # int32 numSampsPerChan,
        # bool32 autoStart,
        # float64 timeout,
        # bool32 dataLayout,
        # float64 writeArray[],
        # int32 *sampsPerChanWritten,
        # bool32 *reserved
        PyDAQmx.DAQmxWriteAnalogF64(taskHandle,
                                    1,
                                    1,
                                    1.0,
                                    PyDAQmx.DAQmx_Val_GroupByChannel,
                                    numpy.array([vinVolts]),
                                    ctypes.byref(nWritten),
                                    None)

        PyDAQmx.DAQmxStartTask(taskHandle)

        PyDAQmx.DAQmxStopTask(taskHandle)
        PyDAQmx.DAQmxClearTask(taskHandle)

    @setting(10, 'blankWaveform', t_tot='v[]')
    def blankWaveform(self, c, t_tot=1e-5):
        # save values for future
        self.t_tot = t_tot

        self.nPoints = int(numpy.ceil(self.sampleRate * self.t_tot))
        # print ("hi: %f, %d" %(t_tot,self.nPoints))
        self.data = numpy.zeros((self.nCh, self.nPoints), dtype=numpy.float64)

    @setting(11, 'setVoltagePulse', ch='i', t_start='v[]', t_len='v[]', voltage='v[V]')
    def setVoltagePulse(self, c, ch, t_start, t_len, voltage):
        """ turn on ch from t_start to t_start + t_len """
        if ch == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)
        stop_idx = int((t_start + t_len) * self.sampleRate)

        for idx in range(start_idx, stop_idx):
            # print("Before OR gate")
            # print(self.data)
            self.data[ch][idx] = voltage['V']
            # print("After OR gate")
            #        print(self.data)

    @setting(3, "setConstantVoltage", channel="w", voltage="v[V]", returns="")
    def setConstantVoltage(self, c, channel, voltage):
        if channel == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        """ set channel output to constant voltage """
        self.data[channel, :] = voltage['V']

    @setting(4, "setConstantVoltageTime", channel="w", voltage="v[V]", ton="v", toff="v", returns="")
    def setConstantVoltageTime(self, c, channel, voltage, ton, toff):
        """ set channel output to constant voltage from ton to toff """
        if channel == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        idx_start = int(ton * self.sampleRate)
        idx_stop = int(toff * self.sampleRate)

        print("On " + str(channel) + ", Setting voltage on ch:" + str(channel) + " to " + str(
            voltage['V']) + " from idx " + str(idx_start) + ":" + str(idx_stop))

        self.data[channel, idx_start:idx_stop] = voltage['V']

    @setting(16, "setConstantVoltageTimeAndHold", channel="w", voltage="v[V]", ton="v", returns="")
    def setConstantVoltageTimeAndHold(self, c, channel, voltage, ton):
        """ set channel output to constant voltage from ton to toff """
        if channel == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        idx_start = int(ton * self.sampleRate)

        print("On " + str(channel) + ", Setting voltage on ch:" + str(channel) + " to " + str(
            voltage['V']) + " from idx " + str(idx_start) + ": eternity!")

        self.data[channel, idx_start:] = voltage['V']

    @setting(13, "setConstantVoltageTimeLoop", channel="w", voltage1="v[V]", voltage2="v[V]", ton="v", toff="v",
             tper="v", duty="v", returns="")
    def setConstantVoltageTimeLoop(self, c, channel, voltage1, voltage2, ton, toff, tper, duty):
        """ set channel output to constant voltage from ton to toff """
        self.tlist = np.arange(ton, toff, tper)

        for t in self.tlist:
            idx_start1 = int(t * self.sampleRate)
            idx_start2 = int((t + tper * duty) * self.sampleRate)
            idx_stop = int((t + tper) * self.sampleRate)

            self.data[channel, idx_start1:idx_start2] = voltage1['V']
            self.data[channel, idx_start2:idx_stop] = voltage2['V']

    @setting(5, "rampVoltageTime", channel="w", vi="v[V]", vo="v[V]", t1="v", t2="v", returns="")
    def rampVoltageTime(self, c, channel, vi, vo, t1, t2):
        """ ramp voltage from vi to vo, from time ton to toff """
        idx_start = int((t1) * self.sampleRate)
        idx_stop = int((t2) * self.sampleRate)
        if channel == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        print("On " + str(channel) + ", Ramping voltage from " + str(vi['V']) + ":" + str(
            vo['V']) + ", from idx " + str(idx_start) + ":" + str(idx_stop))

        # print numpy.size(self.data[channel,idx_start:idx_stop])
        # print numpy.size(numpy.linspace(vi['V'],vo['V'],idx_stop-idx_start))
        self.data[channel, idx_start:idx_stop] = numpy.linspace(vi['V'], vo['V'], idx_stop - idx_start)

    @setting(17, "rampToVoltageTime", channel="w", vo="v[V]", t1="v", t2="v", returns="")
    def rampToVoltageTime(self, c, channel, vo, t1, t2):
        """ ramp voltage from what ever we have previous to vf, from time t1 to t2"""
        idx_start = int((t1) * self.sampleRate)
        idx_stop = int((t2) * self.sampleRate)

        if idx_start > 0:
            vstart = self.data[channel, idx_start - 1]
        else:
            vstart = 0

        if channel == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        print("On " + str(channel) + ", Ramping voltage from " + str(vstart) + ":" + str(
            vo['V']) + ", from idx " + str(idx_start) + ":" + str(idx_stop))

        # print numpy.size(self.data[channel,idx_start:idx_stop])
        # print numpy.size(numpy.linspace(vi['V'],vo['V'],idx_stop-idx_start))

        self.data[channel, idx_start:idx_stop] = numpy.linspace(vstart, vo['V'], idx_stop - idx_start)

    @setting(6, "specAOMRampVoltageTime", channel="w", fi="v", fo="v", t1="v", t2="v", returns="")
    def specAOMRampVoltageTime(self, c, channel, fi, fo, t1, t2):
        if channel == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return

        def spec2Mixer_MHz2V(f):
            a, f0, c = np.array([4.00641030e-04, -4.11272722e+00, 2.16015888e-01])
            val = a * (f - f0) ** 2 + c
            return np.clip(val, 0, 0.3)

        """ ramp voltage from vi to vo, from time ton to toff """
        idx_start = int((t1) * self.sampleRate)
        idx_stop = int((t2) * self.sampleRate)

        # print "On " + str(channel) + ", Ramping voltage from " + str(vi['V']) + ":" + str(
        #     vo['V']) + ", from idx " + str(idx_start) + ":" + str(idx_stop)

        # print numpy.size(self.data[channel,idx_start:idx_stop])
        # print numpy.size(numpy.linspace(vi['V'],vo['V'],idx_stop-idx_start))
        self.data[channel, idx_start:idx_stop] = spec2Mixer_MHz2V(numpy.linspace(fi, fo, idx_stop - idx_start))

    @setting(12, 'setFinalState', ch='i', val='v[V]')
    def setFinalState(self, c, ch, val):
        if ch == 17:
            print("AO17 is used for nuclear spin drive! NO CW mode!")
            return
        self.data[ch][-1] = val['V']

    @setting(14, 'ArbWave', ch='i', t_start='v[]', t_len='v[]', ampList='*v', freqList='*v', phaseList='*v',
             pulseDuration='*v', waitTime='*v')
    def ArbWave(self, c, ch, t_start, t_len, ampList, freqList, phaseList, pulseDuration, waitTime):
        """ turn on ch from t_start to t_start + t_len """

        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)

        tList = np.arange(0, t_len, 1 / float(self.sampleRate))
        startTime_s = waitTime[0] + np.concatenate(([0], np.cumsum(pulseDuration[:-1] + waitTime[1:])))
        duration_s = pulseDuration

        nPulses = len(pulseDuration)
        ampList = np.clip(ampList, 0, 3)
        wave = np.zeros_like(tList)
        for i in range(nPulses):
            start_sample = int(startTime_s[i] * self.sampleRate)
            duration_sample = int(duration_s[i] * self.sampleRate)
            # tList has shape 2630
            # print(tList[start_sample:start_sample + duration_sample], tList[start_sample:start_sample + duration_sample].shape)
            wave[start_sample:start_sample + duration_sample] = \
                ampList[i] * np.sin(
                    2 * np.pi * freqList[i] * (tList[start_sample:start_sample + duration_sample]  # )+phaseList[i])
                                               - tList[int(startTime_s[0] * self.sampleRate)]) + phaseList[i])

        self.data[ch, start_idx:start_idx + len(wave)] = wave
        return wave

    @setting(15, 'ArbWaveMod', ch='i', t_start='v[]', t_len='v[]', filename='s')
    def ArbWaveMod(self, c, ch, t_start, t_len, filename):
        """ turn on ch from t_start to t_start + t_len """
        datFile = open(filename, 'rb')
        dat = pickle.load(datFile)
        args = dat
        # ampFns = dat[1]
        print(args)
        # print(ampFns)
        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)
        startTime_s = args['startTime']
        pulseDuration = args['pulseDuration']
        ampList = args['ampList']
        freqList = args['freqList']
        phaseList = args['phaseList']
        tList = np.arange(0, t_len, 1 / float(self.sampleRate))
        duration_s = pulseDuration

        nPulses = len(pulseDuration)
        ampList = np.clip(ampList, 0, 3)
        wave = np.zeros_like(tList)
        for i in range(nPulses):
            start_sample = int(startTime_s[i] * self.sampleRate)
            duration_sample = int(duration_s[i] * self.sampleRate)
            # tList has shape 2630
            print(len(tList))
            wave[start_sample:start_sample + duration_sample] = \
                ampList[i] * args['ampFns'][i](tList[start_sample:start_sample + duration_sample], args, i) * np.sin(
                    2 * np.pi * freqList[i] * (tList[start_sample:start_sample + duration_sample]  # )+phaseList[i])
                                               - tList[int(startTime_s[0] * self.sampleRate)]) + phaseList[i])

        self.data[ch, start_idx:start_idx + len(wave)] = wave
        return wave

    @setting(18, 'ArbWaveLogisticEdge', ch='i', tstartList='*v', ampList='*v', freqList='*v', phaseList='*v',
             durationList='*v', riseTimeList='*v')
    def ArbWaveLogisticEdge(self, c, ch, tstartList, ampList, freqList, phaseList, durationList, riseTimeList):
        """ turn on ch from t_start to t_start + t_len """
        # print(ch, tstartList, ampList, freqList, phaseList, durationList, riseTimeList)
        start_idx = int(tstartList[0] * self.sampleRate)
        startTimeReset_s = np.array(tstartList) - tstartList[0]
        ampList = ampList
        freqList = freqList
        phaseList = phaseList
        t_len = durationList[-1] + tstartList[-1] - tstartList[0]
        tList = np.arange(0, t_len, 1 / float(self.sampleRate)) + tstartList[0]
        duration_s = durationList

        nPulses = len(durationList)
        ampList = np.clip(ampList, 0, 3)
        wave = np.zeros_like(tList)

        args = {'durationList': durationList, 'riseTimeList': riseTimeList}

        # print('success 331')
        for i in range(nPulses):
            start_sample = int(startTimeReset_s[i] * self.sampleRate)
            duration_sample = int(duration_s[i] * self.sampleRate)
            # tList has shape 2630
            wave[start_sample:start_sample + duration_sample] = \
                ampList[i] * flatPulse(tList[start_sample:start_sample + duration_sample], args, i) * \
                np.sin(2 * np.pi * freqList[i] * tList[start_sample:start_sample + duration_sample] + phaseList[i])

        self.data[ch][start_idx:start_idx + len(wave)] = wave
        # round these to nearest integers

        return wave

    @setting(8, 'runWaveform', numloops='i')
    def runWaveform(self, c, numloops):  # first, cleanup any old tasks

        # print self.data

        # Physical Channel Lists
        # Use commas to separate physical channel names and ranges in a list as follows:
        # Dev1/ai0, Dev1/ai3:6
        # Dev1/port0, Dev1/port1/line0:2

        self.numloops = numloops

        # print 'in runWaveform'

        self.cleanupTask(self)

        ###########################
        # first setup a counter task to act as the clock
        ############################
        self.taskHandleClk = PyDAQmx.TaskHandle(0)
        self._check(PyDAQmx.DAQmxCreateTask("", ctypes.byref(self.taskHandleClk)))

        # int32 DAQmxCreateCOPulseChanTicks (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], const char sourceTerminal[], int32 idleState, int32 initialDelay, int32 lowTicks, int32 highTicks);
        self._check(
            PyDAQmx.DAQmxCreateCOPulseChanTicks(self.taskHandleClk,
                                                "/Dev3/ctr0",
                                                "",
                                                "/Dev3/PXI_Trig7",
                                                PyDAQmx.DAQmx_Val_Low,
                                                0,
                                                2,
                                                self.sampleClockDivider - 2
                                                ))

        # int32 DAQmxCfgImplicitTiming (TaskHandle taskHandle, int32 sampleMode, uInt64 sampsPerChanToAcquire);
        self._check(
            PyDAQmx.DAQmxCfgImplicitTiming(
                self.taskHandleClk,
                PyDAQmx.DAQmx_Val_ContSamps,
                0
            )
        )

        # # int32 __CFUNC DAQmxSetCOCtrTimebaseSrc(TaskHandle taskHandle, const char channel[], const char *data);
        # self._check(PyDAQmx.DAQmxSetCOCtrTimebaseSrc(self.taskHandleClk,
        #                                              '/Dev3/ctr0',
        #                                              "/Dev3/PXI_Trig7"
        #                                              ))

        # int32 DAQmxCfgDigEdgeStartTrig (TaskHandle taskHandle, const char triggerSource[], int32 triggerEdge);
        self._check(PyDAQmx.DAQmxCfgDigEdgeStartTrig(self.taskHandleClk,
                                                     '/Dev3/PXI_Trig1',  # source
                                                     PyDAQmx.DAQmx_Val_Rising,  # activeEdge
                                                     ))

        self._check(PyDAQmx.DAQmxStartTask(self.taskHandleClk))

        ##########################
        # now setup the analog output
        ###########################
        self.taskHandle = PyDAQmx.TaskHandle(0)

        # int32 __CFUNC     DAQmxCreateTask                (const char taskName[], TaskHandle *taskHandle);
        self._check(PyDAQmx.DAQmxCreateTask("", ctypes.byref(self.taskHandle)))

        # int32 DAQmxCreateAOVoltageChan (TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
        self._check(
            PyDAQmx.DAQmxCreateAOVoltageChan(self.taskHandle, self.channel_string, "", -10.0, 10.0,
                                             PyDAQmx.DAQmx_Val_Volts, ""))

        # int32 __CFUNC     DAQmxCfgSampClkTiming          (TaskHandle taskHandle, const char source[], float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChan);
        self._check(PyDAQmx.DAQmxCfgSampClkTiming(self.taskHandle,
                                                  '/Dev3/Ctr0InternalOutput',  # source
                                                  ctypes.c_double(self.sampleRate),  # rate
                                                  PyDAQmx.DAQmx_Val_Rising,  # activeEdge
                                                  PyDAQmx.DAQmx_Val_FiniteSamps,  # sampleMode # continuous sampling
                                                  PyDAQmx.uInt64(numloops * self.nPoints)  # numSamples
                                                  ))

        # int32 DAQmxCfgDigEdgeStartTrig (TaskHandle taskHandle, const char triggerSource[], int32 triggerEdge);
        # self._check(PyDAQmx.DAQmxCfgDigEdgeStartTrig(self.taskHandle,
        #                                          '/Dev3/PXI_Trig1',  # source
        #                                          PyDAQmx.DAQmx_Val_Rising,  # activeEdge
        #                                          ))

        print("Using Finite Samples")

        self._check(PyDAQmx.DAQmxSetWriteRegenMode(self.taskHandle, PyDAQmx.DAQmx_Val_AllowRegen))

        # int32 DAQmxWriteAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
        self._check(
            PyDAQmx.DAQmxWriteAnalogF64(
                self.taskHandle,
                ctypes.c_int(self.nPoints),  # numSampsPerChan
                0,  # autoStart
                ctypes.c_double(10.0),  # timeout
                PyDAQmx.DAQmx_Val_GroupByChannel,  # dataLayout
                self.data,  # writeArray[]
                None,  # byref(self.nWritten),           # *sampsPerChanWritten
                None)
        )  # *reserved

        # print self.data

        # DAQmxExportSignal(self.taskHandle, DAQmx_Val_SampleClock, '/PXI1Slot3/PXI_Trig7')
        # DAQmxExportSignal(self.taskHandle, DAQmx_Val_StartTrigger, '/PXI1Slot3/PXI_Trig6')
        # pydaqmx.DAQmxExportSignal(self.taskHandle, self.internalClk, self.externalClk)
        # pydaqmx.DAQmxExportSignal(self.taskHandle, self.internalTrig, self.externalTrig)
        # pydaqmx

        self._check(PyDAQmx.DAQmxStartTask(self.taskHandle))

        # time.sleep(self.loopperiod)

        # time.sleep(10)

    @setting(98, 'saveData', ch='i', path='s')
    def saveData(self, c, ch, path):
        saveDat = self.data[ch]
        np.save(path, saveDat)
        return saveDat

    @setting(99, 'cleanupTask')
    def cleanupTask(self, c):
        """ clean up old task, ready to restart """

        if getattr(self, 'taskHandle', None) is not None:
            self._check(PyDAQmx.DAQmxStopTask(self.taskHandle))
            self._check(PyDAQmx.DAQmxClearTask(self.taskHandle))

        if getattr(self, 'taskHandleClk', None) is not None:
            self._check(PyDAQmx.DAQmxStopTask(self.taskHandleClk))
            self._check(PyDAQmx.DAQmxClearTask(self.taskHandleClk))

        self.taskHandle = None
        self.taskHandleClk = None

    def _check(self, err):
        """Checks NI-DAQ error messages, prints results"""
        if err < 0:
            buf_size = 128
            buf = PyDAQmx.create_string_buffer('\000' * buf_size)
            # this calls the DAQmx error function; byref(buf) passes a pointer to the string
            self.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('NI-DAQ call failed with error %d: %s' % (err, repr(buf.value)))


if __name__ == "__main__":
    from labrad import util
    import ctypes

    ctypes.windll.kernel32.SetConsoleTitleA("AO_server")
    util.runServer(AOServer())
