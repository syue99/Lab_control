import numpy as np
import pyvisa as visa
from labrad.server import LabradServer, setting
import time


class rigolDG1000Server(LabradServer):
    name = "rigolDG1000Server"

    def initServer(self):
        self.rm = visa.ResourceManager()
        self.rigol = self.rm.open_resource(u'USB0::0x0400::0x09C4::DG1D191902023::INSTR')
        # USB0::0x0400::0x09C4::DG1D191902023::INSTR
        # self.rigol = self.rm.open_resource(u'USB0::0x1AB1::0x0641::DG4E194403248::INSTR')

    def stopServer(self):
        pass

    def _writeCommands(self, cmd):
        print (cmd)
        self.rigol.write(cmd)

    # this is just a test
    @setting(1, "Echo", data="?", returns="?")
    def echo(self, c, data):
        print (data)
        return data

    # @setting(2, "setFreq", channel='i', freq='v', amp='v')
    # def setFreq(self, c, channel, freq, amp):
    #     self._writeCommands('APPL:SIN:CH%d' % channel)
    #     self._writeCommands('FREQ:CH%d %f' % (channel, freq))
    #     # self._writeCommands(':SOUR%d:OUTP:IMP Hiz' % channel)
    #     self._writeCommands('VOLT:UNIT:CH%d Vpp' % channel)
    #     self._writeCommands('VOLT:CH%d %f' % (channel, amp))
    #     self._writeCommands('OUTP:CH%d ON' % channel)

    @setting(2, "setFreq", channel='i', freq='v', amp='v')
    def setFreq(self, c, channel, freq, amp):
        if channel==1:
            self._writeCommands('APPL:SIN %d'% freq)
            time.sleep(0.005)
            self._writeCommands('VOLT:UNIT VPP')
            time.sleep(0.005)
            self._writeCommands('VOLT %.2f'% amp)
            time.sleep(0.005)
            self._writeCommands('OUTP ON')
        elif channel==2:
            self._writeCommands('APPL:SIN:CH2 %d'% freq)
            self._writeCommands('VOLT:UNIT:CH2 VPP')
            self._writeCommands('VOLT:CH2 %.2f'% amp)
            self._writeCommands('OUTP:CH2 ON')




    @setting(3, "setFM", channel='i', freq='v', dev='v')
    def setFM(self, c, channel, freq, dev):
        if channel==1:
            self._writeCommands('FM:SOUR INT')
            self._writeCommands('FM:INT:FREQ %d' % freq)
            self._writeCommands('FM:DEV %d' % freq)
            self._writeCommands('FM:INT:FUNC TRI')
            self._writeCommands('FM:STAT ON')
        else:
            print("Channel 2 does not support FM")

    @setting(4, "modOff", channel='i')
    def modOff(self, c, channel):
        self._writeCommands('FM:STAT OFF')

##have not tested
    @setting(5, "arbWave", channel='i', freqs='*v', amps='*v', phases='*v', waveFreq='v[Hz]', waveVpp='v[V]')
    def arbWave(self, c, channel, freqs, amps, phases, waveFreq, waveVpp):
        n = 4096  # max number of points in waveform
        wave = np.zeros(n)
        t = np.arange(n)
        for i in range(len(freqs)):
            wave += amps[i] * np.cos(2 * np.pi * freqs[i] * t / n + phases[i])

        waveRounded = list( round((wave / np.max(np.abs(wave)) +1)* 8191 +1))  # allowed values from 0 to 16383
        #waveRounded = ['%0.4f' % i for i in wave]
        waveString = ','.join(waveRounded)
        print (waveString)
        self._writeCommands('DATA VOLATILE,' + waveString)
        if channel==1:
            self._writeCommands('APPL:USER %d,%f'% (waveFreq['Hz'], waveVpp['V']))
            self._writeCommands('OUTP ON')
        elif channel==2:
            self._writeCommands('APPL:SIN:CH2 %d,%f'% (waveFreq['Hz'], waveVpp['V']))
            self._writeCommands('OUTP:CH2 ON')
        

    # @setting(5, "arbWave", channel='i',  wave='*v')
    # def arbWave(self, c, channel, wave):
    #     n = 16384  # max number of points in waveform
    #     wave = list(wave / np.max(np.abs(wave)))  # allowed values from -1 to 1
    #     waveRounded = ['%0.4f' % i for i in wave]
    #     waveString = ','.join(waveRounded)
    #     print waveString
    #
    #     self._writeCommands(':SOUR%d:APPL:USER %f,%f,0.0,0.0' % (channel, waveFreq['Hz'], waveVpp['V']))
    #     self._writeCommands(':TRAC:DATA VOLATILE,' + waveString)
    #     self._writeCommands(':OUTP%d ON' % channel)

    # plt.plot(wave)
    # plt.draw()
    
    # @setting(10, "setPulse", channel='i', time='v')
    # def setPulse(self, c, channel, time):
    #     self._writeCommands(':SOUR%d:VOLT:UNIT Vpp' % channel)
    #     self._writeCommands(':SOUR%d:APP:SQU %f,%f,%f' % (channel, 1 / (2.0 * time), 5.0, 2.5))
    #     self._writeCommands(':SOUR%d:VOLT:OFFS %f' % (channel, 2.5))
    #     self._writeCommands(':SOUR%d:VOLT %f' % (channel, 5.0))
    #     self._writeCommands(':SOUR%d:PER %0.9f' % (channel, 2 * time))
    #     self._writeCommands(':SOUR%d:FUNC:SQU:DCYC %f' % (channel, 50))
    #     self._writeCommands(':SOUR%d:BURS:PHAS 0' % channel)

    #     self._writeCommands(':SOUR%d:BURS:STAT ON' % channel)
    #     self._writeCommands(':SOUR%d:BURS:TRIG:SOUR EXT' % channel)
    #     self._writeCommands(':SOUR%d:BURS:NCYC %d' % (channel, 1))
    #     self._writeCommands(':OUTP%d On' % channel)

    # @setting(11, "sinePulse", channel='i', amp='v[V]', freq='v[Hz]', phase='v', time='v', delay='v')
    # def sinePulse(self, c, channel, amp, freq, phase, time, delay):
    #     # amp is the peak to peak voltage (V), phase in deg, times in seconds
    #     self._writeCommands(':SOUR%d:APP:SIN %f,%f,%f,%f' % (channel, freq['Hz'], amp['V'], 0, phase))
    #     self._writeCommands(':SOUR%d:BURS ON' % channel)
    #     self._writeCommands(':SOUR%d:BURS:MODE TRIG' % (channel))
    #     self._writeCommands(':SOUR%d:BURS:NCYC %f' % (channel, 7))
    #     # self._writeCommands(':SOUR%d:PER %0.9f' % (channel, 2*time))
    #     self._writeCommands(':SOUR%d:BURS:INT:PER %d' % (channel, time))
    #     self._writeCommands(':SOUR%d:BURS:TRIG: SOUR EXT' % (channel))
    #     self._writeCommands(':SOUR%d:BURS:TDEL %d' % (channel, delay))
    #     self._writeCommands(':OUTP%d On' % channel)

    @setting(6, "highZMode", channel='i', highZ='i')
    def highZ(self, c, channel, highZ):
        if channel==1:
            chn_str = ""
        elif channel==2:
            chn_str = ":CH2"
        if highZ:
            self._writeCommands(':OUTP:LOAD'+chn_str+' INF')
        else:
            self._writeCommands(':OUTP:LOAD'+chn_str+' 50')

    @setting(7, "reset")
    def reset(self, c):
        self._writeCommands('*RST')

    @setting(8, "command")
    def command(self, c, str):
        self._writeCommands(str)

    @setting(18, "read")
    def read(self):
        self.rigol.read()

    # def writeArb(self, channel, amp, waveform, sampRate=500e6):
    #     freq = sampRate / float(len(waveform))
    #     waw_write_cmd = ':DATA VOLATILE'
    #     for point in waveform:
    #         # might be okay to change the resolution
    #         waw_write_cmd += ',%.6f' % point
    #     # print(waw_write_cmd)
    #     self._writeCommands('SOUR%d:APPLy:USER %.6f,%.6f,%.6f,0' % (channel, freq, amp, amp / 2.))
    #     self._writeCommands(waw_write_cmd)
    #     # set burst mode
    #     self._writeCommands(r':SOUR%d:BURS ON' % channel)
    #     self._writeCommands(":SOUR%d:BURS:MODE TRIG" % channel)
    #     self._writeCommands(":SOUR%d:BURS:NCYC 1" % channel)
    #     self._writeCommands(":SOUR%d:BURS:PHAS %0.3f DEG" % (channel, 359.999))
    #     self._writeCommands(":SOUR%d:BURS:TRIG:SOUR EXT" % channel)
    #     self._writeCommands(":SOUR%d:BURS:TRIG:SLOP POS" % channel)
    #     self._writeCommands(':OUTP%d ON' % channel)

    # @setting(9, "setFMExt", channel='i', dev='v')
    # def setFMExt(self, c, channel, dev):
    #     self._writeCommands(':SOUR%d:MOD:STAT On' % channel)
    #     self._writeCommands(':SOUR%d:MOD:TYP FM' % channel)
    #     self._writeCommands(':SOUR%d:MOD:FM:SOUR EXT' % channel)
    #     self._writeCommands(':SOUR%d:MOD:FM:DEV %f' % (channel, dev))

    # @setting(13, "writeRabiArb", chanNumber='i', pWidth='v')
    # def writeRabiArb(self, c, chanNumber, pWidth, amp=3.3, sampRate=500e6):
    #     # first write the waveform with no buffer assuming max sample rate
    #     pWidthInt = int(pWidth * sampRate)
    #     # buffer time of 0 output at the end
    #     bufTime = 100e-9
    #     bufInt = int(bufTime * sampRate)
    #     npoints = pWidthInt + bufInt
    #     # we can at most have 16k points
    #     if npoints > 16384:
    #         print('Too many points!!! Consider using a smaller sample rate to decrease the number of points')
    #         return 0
    #     # at this point our total period (including buffer time at the end) should be greater than 25ns s.t.freq < 40MHz
    #     # and the sample rate is set to maximum available
    #     # generate waveform (the default value is initialized to -1)
    #     waveform = (-1) * np.ones(npoints)
    #     # set pulse-on locations to 1
    #     waveform[:pWidthInt] = np.ones(pWidthInt)
    #     self.writeArb(chanNumber, amp, waveform, sampRate)

    # @setting(12, "setPulseDelay", channel='i', time='v', delay='v')
    # def setPulseDelay(self, c, channel, time, delay):
    #     self._writeCommands(':SOUR%d:VOLT:UNIT Vpp' % channel)
    #     self._writeCommands(':SOUR%d:APP:SQU %f,%f,%f' % (channel, 1 / (2.0 * time), 5.0, 2.5))
    #     self._writeCommands(':SOUR%d:VOLT:OFFS %f' % (channel, 2.5))
    #     self._writeCommands(':SOUR%d:VOLT %f' % (channel, 5.0))
    #     self._writeCommands(':SOUR%d:PER %0.9f' % (channel, 2 * time))
    #     self._writeCommands(':SOUR%d:FUNC:SQU:DCYC %f' % (channel, 50))
    #     self._writeCommands(':SOUR%d:BURS:PHAS 0' % channel)

    #     self._writeCommands(':SOUR%d:BURS:STAT ON' % channel)
    #     self._writeCommands(':SOUR%d:BURS:TRIG:SOUR EXT' % channel)
    #     self._writeCommands(':SOUR%d:BURS:TDEL %f' % (channel, delay))
    #     self._writeCommands(':SOUR%d:BURS:NCYC %d' % (channel, 1))
    #     self._writeCommands(':OUTP%d On' % channel)

    # @setting(14, "makeArbWave", channel='i', amp='v', waveform='*v')
    # def makeArbWave(self, c, channel, amp, waveform):
    #     sampRate = 100e3
    #     freq = sampRate / float(len(waveform))
    #     totalT = float(len(waveform)) / (100e3)
    #     waw_write_cmd = ':SOUR%d:DATA VOLATILE' % (channel)
    #     for point in waveform:
    #         # might be okay to change the resolution
    #         waw_write_cmd += ',%.6f' % point
    #     print(totalT)
    #     self._writeCommands(r':SOUR%d:BURS:STAT OFF' % channel)
    #     self._writeCommands(':OUTP%d OFF' % channel)
    #     self._writeCommands('SOUR%d:APPLy:USER %.6f,%.6f,%.6f,0' % (channel, freq, amp, 0.))
    #     # self._writeCommands(':SOUR%d:APPLy:ARB %d,%.6f,%.6f' % (channel, sampRate, amp, 0.))
    #     self._writeCommands(':OUTP%d: FUNC USER' % channel)
    #     self._writeCommands(waw_write_cmd)
    #     self._writeCommands(":SOUR%d:BURS:MODE TRIG" % channel)
    #     self._writeCommands(":SOUR%d:BURS:NCYC 1" % channel)
    #     self._writeCommands(':SOUR%d:BURS:INT:PER %.6f' % (channel, totalT + 2e-6))
    #     self._writeCommands(":SOUR%d:BURS:PHAS %0.3f DEG" % (channel, 0.))
    #     self._writeCommands(":SOUR%d:BURS:TRIG:SOUR EXT" % channel)
    #     self._writeCommands(r':SOUR%d:BURS:STAT ON' % channel)
    #     # self._writeCommands(":SOUR%d:BURS:TRIG:SLOP POS" % channel)
    #     self._writeCommands(':OUTP%d ON' % channel)
    @setting(15, "output Off", channel='i')
    def output_off(self, c, channel):
        if channel==1:
            self._writeCommands('OUTP OFF')
        elif channel==2:
            self._writeCommands('OUTP:CH2 OFF')

    @setting(16, "Burst Mode ON", channel='i', gated='v', cycle='v')
    def burst_mode_on(self, c, channel, gated, cycle):
        if channel==1:
            if gated==1:
                self._writeCommands('BURS:MODE GAT')
            else:
                self._writeCommands('BURS:MODE TRIG')
                self._writeCommands('BURS:NCYC %d' %cycle)
            self._writeCommands('BURS:STAT ON')
        else:
            print("Channel 2 does not support BURST Mode")
    
    @setting(17, "Burst Mode OFF", channel='i')
    def burst_mode_off(self, c, channel):
        if channel==1:
            self._writeCommands('BURS:STAT OFF')
        else:
            print("Channel 2 does not support BURST Mode")

if __name__ == "__main__":
    from labrad import util
    import ctypes

    ctypes.windll.kernel32.SetConsoleTitleA("rigolDG1000_server")
    util.runServer(rigolDG1000Server())
