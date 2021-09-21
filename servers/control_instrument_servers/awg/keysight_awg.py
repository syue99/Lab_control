"""
### BEGIN NODE INFO
[info]
name = Keysight AWG Server
version = 1.0
description = AWG server 
instancename = keysight_awg

[startup]
cmdline = %PYTHON% %FILE%
timeout = 40

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from labrad.server import LabradServer
from labrad.server import setting
import labrad.units as _u
import numpy as _np
from scipy.fftpack import ifft,fft, rfft, irfft
import sys 
try:
    sys.path.append('C:\Program Files\Keysight\SD1\Libraries\Python') 
    import keysightSD1
except:
    print("No keysight API found, plz install SD1 software or check the directory")

sys.path.append('../../../config/awg/')
from awgConfiguration import hardwareConfiguration
sys.path.append('utility/')
from mode_calculation import Axialmodes

SERVERNAME = 'keysight_awg'



class keysightAWGServer(LabradServer):
    """Server for arbitrary function generator using the keysight awg."""
    name = SERVERNAME
    
    def initServer(self):
        model = hardwareConfiguration.model
        #set up the normalization constant for the different AWG, this nor has unit (Mega Sample/s)
        if model == "M3201A":
            self.nor = 500
        elif model == "M3202A":
            self.nor = 1000
        else:
            try:
                self.nor = hardwareConfiguration.nor
            except:
                raise Exception("please specify the right model number, or specify a nor value in configuration file") 
        chassis = hardwareConfiguration.chassis
        self.channel_list = hardwareConfiguration.channel_list
        self.channelfreq = hardwareConfiguration.channel_freq
        self.channelamp = hardwareConfiguration.channel_amp
        slot = hardwareConfiguration.slot
        self.awg=keysightSD1.SD_AOU()
        moduleID = self.awg.openWithSlot(model, chassis, slot)
        if moduleID >0:
            print("connected to AWG with module ID: "+str(moduleID))
            for i in self.channel_list:
                self.awg.channelFrequency(i, self.channelfreq[i-1]["Hz"])
                self.awg.channelAmplitude(i, self.channelamp[i-1]["V"])
                self.awg.channelWaveShape(i, 1)
        else:
            print(moduleID)
            raise Exception("could not connect to AWG, check the Error code above") 

    @setting(1, "Amplitude", channel='w', amplitude='v[V]', returns='')
    def amplitude(self, c, channel=None, amplitude=None):
        """Gets or sets the amplitude of the named channel or the selected channel."""
        if abs(amplitude["V"]) < hardwareConfiguration.channel_amp_thres[channel-1]:
            self.awg.channelAmplitude(channel, amplitude["V"])
        else:
            raise Exception("the amp is bigger than the set threshold")

    @setting(2, "Frequency", channel='w', freq='v[MHz]', returns='')
    def frequency(self, c, channel=None, freq=None):
        """Gets or sets the frequency of the named channel or the selected channel."""
        self.awg.channelFrequency(channel, freq["Hz"])
    
    @setting(3, "Phase", channel='w', phase='v[deg]', returns='')
    def phase(self, c, channel=None, phase=None):
        """Gets or sets the phase of the named channel or the selected channel."""
        self.awg.channelPhase(channel, phase["deg"])

    @setting(4, "AWG Play from File", channel='w', file='s', returns='')
    def awg_play_from_file(self, c, channel=None, file=None):
        """Play the named channel or the selected channel with AWG file input."""
        self.awg.channelWaveShape(channel, 6)
        file = 'waveform/'+file
        self.awg.AWGFromFile(channel, file, triggerMode=0, startDelay=0, cycles=0, prescaler=None, paddingMode = 0)
        
    @setting(5, "AWG stop", channel='w', returns='')
    def awg_stop(self, c, channel=None):
        """Stop playing the AWG sequence."""
        self.awg.AWGstop(channel)  
        self.awg.channelWaveShape(channel, 1)

    @setting(6, "Arbitary AM", channel='w', file='s', deviationGain='v[V]', carrier_freq='v[MHz]', returns='')
    def arb_am(self, c, channel=None, file=None, deviationGain=None, carrier_freq=None):
        """Using the Amplitude modulation with arbitray AM file\n
        channel (int): channel number\n
        file (string): name of the file.csv in the waveform/ folder\n
        deviationGain (Volts): the amplitude of AM\n
        carrier_freq (Hz): the carrier frequency one used"""
        file = 'waveform/'+file
        self.awg.AWGFromFile(channel, file, triggerMode=0, startDelay=0, cycles=0, prescaler=None, paddingMode = 0)
        self.awg.modulationAmplitudeConfig(channel,1,deviationGain["V"])  
        self.awg.channelFrequency(channel, carrier_freq["Hz"])
        self.awg.channelAmplitude(channel, 0)
        self.awg.channelWaveShape(channel, 1)

    @setting(7, "MS AM", channel='w', Robust_gate='w', deviationGain='v[V]', carrier_freq='v[MHz]', omega='v[MHz]', delta='v[MHz]', returns='')
    def MS_am(self, c, channel=None, Robust_gate=None, deviationGain=None, carrier_freq=None, omega=None, delta=None):
        """Using the Amplitude modulation to do MS gate\n
        channel (int): channel number\n
        Robust_gate (Boolean): if we want robust gate or normal MS\n
        deviationGain (Volts): the amplitude of MS\n
        carrier_freq (Hz): the transition AOM freq\n
        omega (Hz): secular freq to locate the freq of blue and red sideband\n
        delta (Hz): detuning from the sideband. (Base detuning in the robust gate)\n
        """
        if Robust_gate==1:
            file_name = "waveform/Robust_gate_omega"+str(omega["MHz"])+"MHz_delta_"+str(delta["MHz"])+"MHz.csv"
            try:
                wf = _np.loadtxt(file_name,delimiter=',')
            except:
                pt = _np.linspace(0,16666*2-1,16666*2)
                wf = 0
                #calculated r, ref: NYU wiki Robust gate investigation
                r = [4*_np.sqrt(2/57),-5*_np.sqrt(3/38),7/_np.sqrt(114)]
                #picked mode
                n = [2,3,7]
                for i in range(0,3):
                #note here the unit is in MHz
                    wf += r[i]*_np.sin(2*_np.pi*(omega["MHz"]-n[i]*delta["MHz"])*pt/self.nor)
                wf = wf/_np.sum(_np.abs(r))
                wf.tofile(file_name,sep=',',format='%10.16f')
        else:
            file_name = "waveform/MS_gate_omega"+str(omega["MHz"])+"MHz_delta_"+str(delta["MHz"])+"MHz.csv"
            try:
                wf = _np.loadtxt(file_name,delimiter=',')
            except:
                pt = _np.linspace(0,int(self.nor*100/(omega["MHz"]-delta["MHz"]))-1,int(self.nor*100/(omega["MHz"]-delta["MHz"]))*2)
                #pt = _np.linspace(0,16666*2-1,16666*2)
                wf = _np.sin(2*_np.pi*(omega["MHz"]-delta["MHz"])*pt/self.nor)
                wf.tofile(file_name,sep=',',format='%10.16f')
        self.awg.AWGfromArray(channel, triggerMode=0, startDelay=0, cycles=0, prescaler=None, waveformType=0, waveformDataA=wf, paddingMode = 0)
        self.awg.modulationAmplitudeConfig(channel,1,deviationGain["V"])  
        self.awg.channelFrequency(channel, carrier_freq["Hz"])
        self.awg.channelAmplitude(channel, 0)
        self.awg.channelWaveShape(channel, 1)

    @setting(8, "multi order sideband cooling", channel='w', amplitude='v[V]', carrier_freq='v[MHz]', cm_freq='v[MHz]', n='w', returns='')
    def sb_cooling(self, c, channel=None, amplitude=None, carrier_freq=None, cm_freq=None, n=None):
        """Using the direct AWG output to generate multitone sideband cooling pulse\n
        channel (int): channel number\n
        amplitudes (Volts): the amplitude of MS\n
        carrier_freq (Hz): the transition AOM freq\n
        cm_freq (Hz): center of mass freq to locate the freq of blue and red sideband\n
        n (int): number of sidebands to cool\n
        """
        file_name = "waveform/sideband_cooling_carrier_"+str(carrier_freq["MHz"])+"MHz_cmfreq_"+str(cm_freq["MHz"])+"MHz_"+str(n)+"order.csv"
        try:
            wf = _np.loadtxt(file_name,delimiter=',')
        except:
            pt = _np.linspace(0,16666*2-1,16666*2)
            wf = 0
            for i in range(1,n+1):
            #note here the unit is in MHz
                wf += _np.sin(2*_np.pi*(carrier_freq["MHz"]-cm_freq["MHz"]*i)*pt/self.nor)
            wf = wf/n
            #USE FFT TO BANDPASS THE SIGNAL, NOT USED ANYMORE
            #wffft = rfft(wf)
            #wffft[int(4*16666/(self.nor/carrier_freq["MHz"])):]=0
            #wf = irfft(wffft)           
            wf.tofile(file_name,sep=',',format='%10.16f')
        self.awg.AWGfromArray(channel, triggerMode=0, startDelay=0, cycles=0, prescaler=None, waveformType=0, waveformDataA=wf, paddingMode = 0)
        self.awg.channelWaveShape(channel, 6)
        if abs(amplitude["V"]) < hardwareConfiguration.channel_awg_amp_thres[channel-1]:
            self.awg.channelAmplitude(channel, amplitude["V"])
        else:
            raise Exception("the amp is bigger than the set threshold")

    @setting(9, "multi ion sideband cooling", channel='w', amplitude='v[V]', carrier_freq='v[MHz]', cm_freq='v[MHz]', n='w', returns='')
    def multi_ion_sb_cooling(self, c, channel=None, amplitude=None, carrier_freq=None, cm_freq=None, n=None):
        """Using the direct AWG output to generate multitone sideband cooling pulse for axial modes for multi-ions\n
        channel (int): channel number\n
        amplitudes (Volts): the amplitude of MS\n
        carrier_freq (Hz): the transition AOM freq\n
        cm_freq (Hz): center of mass freq to locate the freq of blue and red sideband\n
        n (int): number of ions cool\n
        """
        file_name = "waveform/multi_ion_sideband_cooling_carrier_"+str(carrier_freq["MHz"])+"MHz_cmfreq_"+str(cm_freq["MHz"])+"MHz_"+str(n)+"order.csv"
        try:
            wf = _np.loadtxt(file_name,delimiter=',')
        except:
            pt = _np.linspace(0,16666*2-1,16666*2)
            modes = Axialmodes(n,cm_freq["MHz"])  
            wf = 1.5*_np.sin(2*_np.pi*(carrier_freq["MHz"]-modes[0])*pt/self.nor)
            #print(modes)
            for i in modes[1:]:
            #note here the unit is in MHz
                wf += _np.sin(2*_np.pi*(carrier_freq["MHz"]-i)*pt/self.nor)
            wf = wf/(n+0.5)       
            wf.tofile(file_name,sep=',',format='%10.16f')
        self.awg.AWGfromArray(channel, triggerMode=0, startDelay=0, cycles=0, prescaler=None, waveformType=0, waveformDataA=wf, paddingMode = 0)
        self.awg.channelWaveShape(channel, 6)
        if abs(amplitude["V"]) < hardwareConfiguration.channel_awg_amp_thres[channel-1]:
            self.awg.channelAmplitude(channel, amplitude["V"])
        else:
            raise Exception("the amp is bigger than the set threshold")

            
    @setting(10, "stop AM", channel='w')
    def am_stop(self, c, channel=None, deviationGain=0):
        """Shut off am settings after one finished am"""
        self.awg.modulationAmplitudeConfig(channel,0,deviationGain)  
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(keysightAWGServer())
