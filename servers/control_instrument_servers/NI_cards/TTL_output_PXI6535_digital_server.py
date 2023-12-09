import time
import warnings

import PyDAQmx as pydaqmx  # Python library to execute NI-DAQmx code
import matplotlib.pyplot as plt
import numpy as np
from labrad import util
from labrad.server import LabradServer, setting
# from PyDAQmx.DAQmxFunctions import *
# from PyDAQmx.DAQmxConstants import *
from numpy import *
from twisted.internet.defer import inlineCallbacks


class FiniteDOPulses(LabradServer):
    name = 'finitedopulses'  # This is how you will access this class from a labrad connection (with name.replace(" ", "_") and name.lower() )

    @inlineCallbacks
    def initServer(self):
        """ pulseData(rate,t_tot) creates a data object to store information about a pulse sequence
        with total length "t_tot" (in seconds) to be output at a rate "rate" (in samples/second)

        """

        self.initialization(self)

        t_tot = 30e-5
        self.blankWaveform(t_tot)

        self.dioNameDict = {
            "AOM gate": 1,
            "AOM RF switch": 2,
            "EOM 1 TTL": 3,
            "Erb Ref on": 5,
            "Erb Ref off": 6,
            "Counter AND gate": 7,
            "Coherent Cancellation on": 8,
            "Coherent Cancellation off": 9,
            "Tuning pump": 10,
            "Tuning gas": 11,
            "DDS freq switch": 12,
            "SNSPD gate TTL": 13,
        }

        self.dioNameDictInv = {}
        for name in self.dioNameDict:
            self.dioNameDictInv[self.dioNameDict[name]] = name

        yield

    @setting(1, 'blankWaveform', t_tot='v[]', coerce='v[]')
    def blankWaveform(self, c, t_tot=30e-5, coerce=1e7):
        ### initializes waveform with length t_tot, coerced to be a multiple of 1/coerce (ie, sub-divided AO rate)
        # save values for future
        self.t_tot = ceil(t_tot * coerce) / coerce
        print('sample rate: %f' % self.sampleRate)
        self.nPoints = int(self.sampleRate * self.t_tot)
        print ("hi: %f, %d" % (t_tot, self.nPoints))
        self.data = zeros(self.nPoints, dtype=pydaqmx.uInt32)

        print ("Actual t_tot = %f, seq. len = %d points" % (self.t_tot, self.nPoints))

    @setting(2, 'PulseOn', ch='i', t_start='v[]', t_len='v[]')
    def PulseOn(self, c, ch, t_start, t_len):
        """ turn on ch from t_start to t_start + t_len """

        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)
        stop_idx = int((t_start + t_len) * self.sampleRate)

        # this should be all zeros except for the bit ch
        ch_mask = 2 ** ch

        # print

        print ("%d,%d,%d" % (start_idx, stop_idx, ch_mask))
        # now set the appropriate bit to 1 in all data elements between start_idx and stop_idx
        # import pdb; pdb.set_trace()
        # for idx in range(start_idx, stop_idx):
        #     # print("Before OR gate")
        #     # print(self.data)
        #     self.data[idx] = self.data[idx] | ch_mask
        #     # print("After OR gate")
        self.data[start_idx:stop_idx] = bitwise_or(self.data[start_idx:stop_idx], ch_mask)

    #        print(self.data)

    @setting(28, 'PulseOnAndHold', ch='i', t_start='v[]')
    def PulseOnAndHold(self, c, ch, t_start):
        """ turn on ch from t_start to t_start + t_len """

        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)

        # this should be all zeros except for the bit ch
        ch_mask = 2 ** ch

        print ("%d,%d" % (start_idx, ch_mask))

        self.data[start_idx:] = bitwise_or(self.data[start_idx:], ch_mask)

    @setting(25, 'PulseOnLoop', ch='i', t_start='v[]', t_on='v[]', t_off='v[]', nPulses='v[]')
    def PulseOnLoop(self, c, ch, t_start, t_on, t_off, nPulses):
        """ turn on ch from t_start to t_start + t_len """

        idx_start = t_start * self.sampleRate
        idx_on = t_on * self.sampleRate
        idx_off = t_off * self.sampleRate
        idx_per = idx_on + idx_off
        t0 = time.time()
        ch_mask = 2 ** ch
        idx_array = (idx_start + np.add.outer(np.arange(nPulses) * idx_per, np.arange(idx_on)).ravel()).astype(int)
        self.data[idx_array] = bitwise_or(self.data[idx_array], ch_mask)

        print ("time for loop: %f" % (time.time() - t0))

    @setting(26, 'PulseOffLoop', ch='i', t_start='v[]', t_len='v[]', t_tot='v[]', t_per='v[]')
    def PulseOffLoop(self, c, ch, t_start, t_len, t_tot, t_per):
        """ turn on ch from t_start to t_start + t_len """
        self.tlist = arange(0, t_tot, t_per)

        t0 = time.time()
        for t in self.tlist:
            # round these to nearest integers
            start_idx = int((t_start + t) * self.sampleRate)
            stop_idx = int((t_start + t + t_len) * self.sampleRate)

            # this should be all zeros except for the bit ch
            ch_mask = (2 ** self.numChannels - 1) - 2 ** ch

            # print

            #            print "%d,%d,%d" % (start_idx, stop_idx, ch_mask)
            # now set the appropriate bit to 1 in all data elements between start_idx and stop_idx
            # import pdb; pdb.set_trace()
            # for idx in range(start_idx, stop_idx):
            #     # print("Before OR gate")
            #     # print(self.data)
            #     self.data[idx] = self.data[idx] | ch_mask
            #     # print("After OR gate")
            self.data[start_idx:stop_idx] = bitwise_or(self.data[start_idx:stop_idx], ch_mask)

        print ("time for loop: %f" % (time.time() - t0))

    @setting(27, 'repeatSequence', t_start='v[]', t_stop='v[]', nLoops='i')
    def repeatSequence(self, c, t_start, t_stop, nLoops):
        """ repeatSequence from tstart to tstop n times"""
        start_idx = int(t_start * self.sampleRate)
        stop_idx = int(t_stop * self.sampleRate)

        self.data[start_idx:start_idx + nLoops * (stop_idx - start_idx)] = tile(self.data[start_idx:stop_idx], nLoops)

    @setting(3, 'PulseOff', ch='i', t_start='v[]', t_len='v[]')
    def PulseOff(self, c, ch, t_start, t_len):
        """ turn off ch from t_start to t_start + t_len """

        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)
        stop_idx = int((t_start + t_len) * self.sampleRate)

        # this should be all ones except for the bit ch
        ch_mask = (2 ** self.numChannels - 1) - 2 ** ch

        # now set the appropriate bit to 1 in all data elements between start_idx and stop_idx
        # for idx in range(start_idx, stop_idx):
        #     self.data[idx] = self.data[idx] & ch_mask
        self.data[start_idx:stop_idx] = bitwise_and(self.data[start_idx:stop_idx], ch_mask)

    @setting(29, 'PulseOffAndHold', ch='i', t_start='v[]')
    def PulseOffAndHold(self, c, ch, t_start):
        """ turn off ch from t_start to t_start + t_len """

        # round these to nearest integers
        start_idx = int(t_start * self.sampleRate)

        # this should be all ones except for the bit ch
        ch_mask = (2 ** self.numChannels - 1) - 2 ** ch

        self.data[start_idx:] = bitwise_and(self.data[start_idx:], ch_mask)

    @setting(30, 'fastSequence', ch='i', t_start='v[]', period='i', t_end='v[]', duty_cycle='v', t_unit='v')
    def fastSequence(self, c, ch, t_start, period, t_end, duty_cycle, t_unit):
        if t_unit != 1. / self.sampleRate:
            raise ValueError('t_unit is not {:.8f}'.format(1. / self.sampleRate))

        t_list_period = np.linspace(1, 0, period)
        status_one_period = np.zeros(t_list_period.shape)
        status_one_period[t_list_period < duty_cycle] = 1

        start_idx = int(t_start * self.sampleRate)
        start_sync_offset = start_idx % period

        end_idx = int(t_end * self.sampleRate)
        end_sync_offset = end_idx % period

        # start and end index of multiple complete periods
        start_cplt_idx = start_idx + period - start_sync_offset

        end_cplt_idx = end_idx - end_sync_offset

        n_period = (end_cplt_idx - start_cplt_idx) / period
        assert((end_cplt_idx - start_cplt_idx) % period == 0)
        assert(end_cplt_idx > start_cplt_idx)

        arr = np.kron(np.ones(n_period), status_one_period)

        ch_mask_off = (2 ** self.numChannels - 1) - 2 ** ch
        ch_mask_on = 2 ** ch

        # take care of the 1st period

        self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 0] = bitwise_and(
            self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 0], ch_mask_off)

        self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 1] = bitwise_or(
            self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 1], ch_mask_on)

        # take care of the last period

        self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 0] = bitwise_and(
            self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 0], ch_mask_off)

        self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 1] = bitwise_or(
            self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 1], ch_mask_on)

        # take care of the middle complete periods

        self.data[start_cplt_idx:end_cplt_idx][arr == 0] = bitwise_and(
            self.data[start_cplt_idx:end_cplt_idx][arr == 0], ch_mask_off)

        self.data[start_cplt_idx:end_cplt_idx][arr == 1] = bitwise_or(
            self.data[start_cplt_idx:end_cplt_idx][arr == 1], ch_mask_on)

    @setting(31, 'fastSequenceToEnd', ch='i', t_start='v[]', period='i', duty_cycle='v', t_unit='v')
    def fastSequenceToEnd(self, c, ch, t_start, period, duty_cycle, t_unit):
        if t_unit != 1. / self.sampleRate:
            raise ValueError('t_unit is not {:.8f}'.format(1. / self.sampleRate))

        t_list_period = np.linspace(1, 0, period)
        status_one_period = np.zeros(t_list_period.shape)
        status_one_period[t_list_period < duty_cycle] = 1

        start_idx = int(t_start * self.sampleRate)
        start_sync_offset = start_idx % period

        end_idx = self.nPoints-1
        end_sync_offset = end_idx % period

        # start and end index of multiple complete periods
        start_cplt_idx = start_idx + period - start_sync_offset

        end_cplt_idx = end_idx - end_sync_offset

        n_period = (end_cplt_idx - start_cplt_idx) / period

        if not (end_cplt_idx > start_cplt_idx):
            warnings.warn('Modulation time too short, server ignores it')
            return
        assert ((end_cplt_idx - start_cplt_idx) % period == 0)

        arr = np.kron(np.ones(n_period), status_one_period)

        ch_mask_off = (2 ** self.numChannels - 1) - 2 ** ch
        ch_mask_on = 2 ** ch

        # take care of the 1st period

        self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 0] = bitwise_and(
            self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 0], ch_mask_off)

        self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 1] = bitwise_or(
            self.data[start_idx:start_cplt_idx][status_one_period[start_sync_offset:] == 1], ch_mask_on)

        # take care of the last period

        self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 0] = bitwise_and(
            self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 0], ch_mask_off)

        self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 1] = bitwise_or(
            self.data[end_cplt_idx:end_idx][status_one_period[:end_sync_offset] == 1], ch_mask_on)

        # take care of the middle complete periods

        self.data[start_cplt_idx:end_cplt_idx][arr == 0] = bitwise_and(
            self.data[start_cplt_idx:end_cplt_idx][arr == 0], ch_mask_off)

        self.data[start_cplt_idx:end_cplt_idx][arr == 1] = bitwise_or(
            self.data[start_cplt_idx:end_cplt_idx][arr == 1], ch_mask_on)

    @setting(4, 'TurnOn', ch='i', t_start='v[]', t_end='v[]')
    def TurnOn(self, c, ch, t_start, t_end):
        self.PulseOn(c, ch, t_start, t_end - t_start)

    @setting(5, 'TurnOff', ch='i', t_start='v[]', t_end='v[]')
    def TurnOff(self, c, ch, t_start, t_end):
        self.PulseOff(c, ch, t_start, t_end - t_start)

    @setting(6, 'AlwaysOn', ch='i')
    def AlwaysOn(self, c, ch):
        self.PulseOn(self, ch, 0, self.t_tot)

    @setting(7, 'AlwaysOff', ch='i')
    def AlwaysOff(self, c, ch):
        self.PulseOff(self, ch, 0, self.t_tot)

    @setting(20, 'SetFinalState', ch='i', state='i')
    def SetFinalState(self, c, ch, state):

        if state == 0:
            # this should be all ones except for the bit ch
            ch_mask = (2 ** self.numChannels - 1) - 2 ** ch

            self.data[-1] = self.data[-1] & ch_mask
        else:
            ch_mask = 2 ** ch
            self.data[-1] = self.data[-1] | ch_mask

    @setting(8, 'runWaveform', numloops='i')
    def runWaveform(self, c, numloops):  # first, cleanup any old tasks

        # Physical Channel Lists
        # Use commas to separate physical channel names and ranges in a list as follows:
        # Dev1/ai0, Dev1/ai3:6
        # Dev1/port0, Dev1/port1/line0:2

        self.numloops = numloops

        # print 'in runWaveform'

        self.cleanupTask(self)

        # now setup the new task
        self.taskHandle = pydaqmx.TaskHandle(0)

        # int32 __CFUNC     DAQmxCreateTask                (const char taskName[], TaskHandle *taskHandle);
        self._check(pydaqmx.DAQmxCreateTask("", ctypes.byref(self.taskHandle)))

        # int32 __CFUNC     DAQmxCreateDOChan              (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
        self._check(
            pydaqmx.DAQmxCreateDOChan(self.taskHandle, self.channel_string, "", pydaqmx.DAQmx_Val_ChanForAllLines))

        # int32 __CFUNC     DAQmxCfgSampClkTiming          (TaskHandle taskHandle, const char source[], float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChan);
        self._check(pydaqmx.DAQmxCfgSampClkTiming(self.taskHandle,
                                                  None,  # source
                                                  float64(self.sampleRate),  # rate
                                                  pydaqmx.DAQmx_Val_Falling,  # activeEdge
                                                  pydaqmx.DAQmx_Val_FiniteSamps,  # sampleMode # continuous sampling
                                                  pydaqmx.uInt64(numloops * len(self.data))  # numSamples
                                                  ))

        print ("Using Finite Samples, len=%d" % int32(len(self.data)))

        self._check(pydaqmx.DAQmxSetWriteRegenMode(self.taskHandle, pydaqmx.DAQmx_Val_AllowRegen))

        # int32 __CFUNC     DAQmxWriteDigitalU32           (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, const uInt32 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
        self._check(
            pydaqmx.DAQmxWriteDigitalU32(
                self.taskHandle,
                int32(len(self.data)),  # numSampsPerChan
                0,  # autoStart
                float64(10.0),  # timeout
                pydaqmx.DAQmx_Val_GroupByChannel,  # dataLayout
                self.data,  # writeArray[]
                None,  # byref(self.nWritten),           # *sampsPerChanWritten
                None)
        )  # *reserved

        # print self.data

        # DAQmxExportSignal(self.taskHandle, DAQmx_Val_SampleClock, '/PXI1Slot3/PXI_Trig7')
        # DAQmxExportSignal(self.taskHandle, DAQmx_Val_StartTrigger, '/PXI1Slot3/PXI_Trig6')
        pydaqmx.DAQmxExportSignal(self.taskHandle, self.internalClk, self.externalClk)
        pydaqmx.DAQmxExportSignal(self.taskHandle, self.internalTrig, self.externalTrig)
        # pydaqmx.DAQmxExportSignal(self.taskHandle, self.internalTrig, '/Dev1/PFI1')
        # pydaqmx

        self._check(pydaqmx.DAQmxStartTask(self.taskHandle))

        # time.sleep(self.loopperiod)

        # time.sleep(10)

    @setting(9, 'readState')
    def readState(self, c):
        # int32 DAQmxReadDigitalU32 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, uInt32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
        blankArr = zeros(32, dtype=pydaqmx.uInt32)
        blankArr2 = zeros(32, dtype=pydaqmx.bool32)
        currentState = pydaqmx.DAQmxReadDigitalU32(pydaqmx.TaskHandle(), 1, 0, pydaqmx.DAQmx_Val_GroupByChannel,
                                                   blankArr, 32, blankArr, blankArr2)
        return currentState

    @setting(10, 'cleanupTask')
    def cleanupTask(self, c):
        """ clean up old task, ready to restart """

        if getattr(self, 'taskHandle', None) is not None:
            self._check(pydaqmx.DAQmxStopTask(self.taskHandle))
            self._check(pydaqmx.DAQmxClearTask(self.taskHandle))

        self.taskHandle = None

    @setting(11, 'initialization')
    def initialization(self, c):

        self.sampleRate = 1e7
        self.numChannels = 32
        self.channel_string = "PXI1Slot3/line0:31"

        self.internalClk = pydaqmx.DAQmx_Val_SampleClock  # Source of the clock timing the output
        self.internalTrig = pydaqmx.DAQmx_Val_StartTrigger  # Source of the trigger to initiate the sequence
        self.externalClk = '/PXI1Slot3/PXI_Trig7'  # Internal clock will be exported to here to sychronize other tasks
        self.externalTrig = '/PXI1Slot3/PXI_Trig1'  # Internal trigger will be exported here

    @setting(12, 'nPoints', returns='i')
    def nPoints(self, c):
        return self.nPoints

    @setting(13, 'flipTTL', state='i')
    def flipTTL(self, c, state):

        stateArr = zeros(1, dtype=pydaqmx.uInt32)
        stateArr[0] = stateArr[0] | state

        self.cleanupTask(None)

        # now setup the new task
        self.taskHandle = pydaqmx.TaskHandle(0)

        # int32 __CFUNC     DAQmxCreateTask                (const char taskName[], TaskHandle *taskHandle);
        self._check(pydaqmx.DAQmxCreateTask("", ctypes.byref(self.taskHandle)))

        # int32 __CFUNC     DAQmxCreateDOChan              (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
        self._check(
            pydaqmx.DAQmxCreateDOChan(self.taskHandle, self.channel_string, "", pydaqmx.DAQmx_Val_ChanForAllLines))

        self._check(pydaqmx.DAQmxStartTask(self.taskHandle))

        pydaqmx.DAQmxWriteDigitalU32(
            self.taskHandle,
            1,  # numSampsPerChan
            0,  # autoStart
            float64(10.0),  # timeout
            pydaqmx.DAQmx_Val_GroupByChannel,  # dataLayout
            stateArr,  # writeArray[]
            None,  # byref(self.nWritten),           # *sampsPerChanWritten
            None)

        self.cleanupTask(None)

    @setting(97, 'getNumSampsWritten')
    def getNumSampsWritten(self, c):

        nSamps = ctypes.c_uint64(0)

        self._check(pydaqmx.DAQmxGetWriteTotalSampPerChanGenerated(self.taskHandle, ctypes.byref(nSamps)))

        print (nSamps.value)
        return nSamps.value

    @setting(14, 'returnData', returns='*i')
    def returnData(self, c):
        return self.data

    @setting(15, 'plotSequence')
    def plotSequence(self, c):
        """ Plots a diagram of the pulse sequence using self.data """

        ax = plt.subplot(111)
        # data is 100ns bins, so this is xCoords for us bins
        xCoords = [i / 10.0 for i in range(2 * len(self.data))]
        numPlots = 0

        plotArr = zeros([32, len(self.data)])
        for i in range(15):
            chMask = 2 ** i
            plotArr[i] = [sign(chMask & self.data[j]) for j in range(len(self.data))]
            if any(plotArr[i]):  # If the array is ever non-zero
                #change by Fred as not sure what is the dionamedicinv
                ax.plot(xCoords, tile((plotArr[i] + 1.5 * numPlots), 2))
                #ax.plot(xCoords, tile((plotArr[i] + 1.5 * numPlots), 2), label=dioNameDictInv[i])  # Offset the graphs
                numPlots += 1

        box = ax.get_position()
        handles, labels = ax.get_legend_handles_labels()
        ax.set_position([box.x0, box.y0, box.width * 0.6, box.height])
        ax.legend(handles[::-1], labels[::-1], loc='center left', bbox_to_anchor=(1, 0.5))
        plt.xlabel("Time (us)")
        plt.title("Two periods of the sequence")
        plt.show()

    #        plt.savefig("plotSequence.png", dpi=300)

    def _check(self, err):
        """Checks NI-DAQ error messages, prints results"""
        if err < 0:
            buf_size = 128
            buf = pydaqmx.create_string_buffer('\000' * buf_size)
            # this calls the DAQmx error function; byref(buf) passes a pointer to the string
            self.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('NI-DAQ call failed with error %d: %s' % (err, repr(buf.value)))


__server__ = FiniteDOPulses()

if __name__ == '__main__':
    import ctypes

    ctypes.windll.kernel32.SetConsoleTitleA("TTL_output_PXI6535_digital_server")
    util.runServer(__server__)
