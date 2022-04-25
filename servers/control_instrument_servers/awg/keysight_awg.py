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
from labrad.units import WithUnit
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
from gatedict import gatedict

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
        self.coherent_channel = hardwareConfiguration.coherent_channel
        slot = hardwareConfiguration.slot
        self.awg=keysightSD1.SD_AOU()
        moduleID = self.awg.openWithSlot(model, chassis, slot)
        if moduleID >0:
            print("connected to AWG with module ID: "+str(moduleID))
            for i in self.channel_list:
                self.awg.channelFrequency(i, self.channelfreq[i-1]["Hz"])
                self.awg.channelAmplitude(i, self.channelamp[i-1]["V"])
                self.awg.channelWaveShape(i, 1)
                #set trigger s.t. the coherent operation channel listen to the external trigger's rising edge
                self.awg.AWGtriggerExternalConfig(self.coherent_channel, 0, 3, 0)
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

    @setting(12, "AWG Play from Array", channel='w', array='*?', returns='')
    def awg_play_from_array(self, c, channel=None, array=None):
        """Play the named channel or the selected channel with AWG file input."""
        self.awg.channelWaveShape(channel, 6)
        self.awg.AWGfromArray(channel, triggerMode=0, startDelay=0, cycles=0, prescaler=None, waveformType=0, waveformDataA=array, paddingMode = 0)
        
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

    @setting(9, "multi ion sideband cooling", channel='w', amplitude='v[V]', carrier_freq='v[MHz]', cm_freq='v[MHz]', n='w', cm_amp = "v", returns='')
    def multi_ion_sb_cooling(self, c, channel=None, amplitude=None, carrier_freq=None, cm_freq=None, n=None, cm_amp=2):
        """Using the direct AWG output to generate multitone sideband cooling pulse for axial modes for multi-ions\n
        channel (int): channel number\n
        amplitudes (Volts): the amplitude of MS\n
        carrier_freq (Hz): the transition AOM freq\n
        cm_freq (Hz): center of mass freq to locate the freq of blue and red sideband\n
        n (int): number of ions cool\n
        """
        file_name = "waveform/multi_ion_sideband_cooling_carrier_"+str(carrier_freq["MHz"])+"MHz_cmfreq_"+"MHz_"+str(cm_freq["MHz"])+"amp"+str(cm_amp)+"_"+str(n)+"order.csv"
        try:
            wf = _np.loadtxt(file_name,delimiter=',')
        except:
            pt = _np.linspace(0,16666*2-1,16666*2)
            modes = Axialmodes(n,cm_freq["MHz"])  
            wf = cm_amp*_np.sin(2*_np.pi*(carrier_freq["MHz"]-modes[0])*pt/self.nor)
            #print(modes)
            for i in modes[1:]:
            #note here the unit is in MHz
                wf += _np.sin(2*_np.pi*(carrier_freq["MHz"]-i)*pt/self.nor + _np.random.rand()*_np.pi*2)
            wf += 2*_np.sin(2*_np.pi*(carrier_freq["MHz"]-modes[0]*2)*pt/self.nor + _np.random.rand()*_np.pi*2)
            wf += 2*_np.sin(2*_np.pi*(carrier_freq["MHz"]-modes[1]*2)*pt/self.nor + _np.random.rand()*_np.pi*2)
            wf += 2*_np.sin(2*_np.pi*(carrier_freq["MHz"]-modes[0]-mode[1])*pt/self.nor + _np.random.rand()*_np.pi*2)

            
            #wf += 2*_np.sin(2*_np.pi*(carrier_freq["MHz"]-0.237*2.7)*pt/self.nor + _np.random.rand()*_np.pi*2)
            print(_np.max(_np.abs(wf)))

            wf = wf/_np.max(_np.abs(wf))       
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

    @setting(11, "compile gates", channel='w', amplitude='v[V]', repetition = 'w', gate_list = '*(?,?,s)', returns='v[ns]')
    #this might be done using multithreads to speed up
    def compile_gates(self, c, channel=None, amplitude=None, repetition = None, gate_list = None):
        """Using the direct AWG output to generate a gate sequence with single and two-qubit gates\n
        channel (int): channel number\n
        amplitudes (Volts): the amplitude of MS\n
        repetition (int): the number of times for this sequence to repeat (with a new trigger)\n
        gate_list [[start_time(us),duration(us), gate1_specified], [start_time,duration, gate2_specified], ..]: gate sequence\n
        avaliable gates:\n
        sigma_phi(float in degs): single qubit gate: e.g. sigma_y: sigma_90\n
        sigmatukey_phi(float in degs): single qubit gate with tukey pulseshaping(a=0.3): e.g. sigmatukey_y: sigma_90\n
        phiphi_phi_mu(MHz)_r1_r2: two qubit gate: e.g. xx MS with mu=1.2MHz and equal strength for bsb and rsb: phiphi_0_1.2_1_1\n
        phiphitukey_phi_mu(MHz)_r1_r2_a: two qubit gate with tukey pulseshaping: e.g. yy MS with mu=1.2MHz and a=0.1 tukey: phiphitukey_90_1.2_1_1_0.1\n
        """
        #we specify gates by using the format of (start_time, duration) and for the start time and duration, there can be two different units
        #1. In the units of regular time s.t. WithUnit(n,'us'). BUT note that n must be divisible by 8. Otherwise we will have an error
        #2. In the units of pi time s.t. WithUnit(n,'pi-time'). This is used for single qubit gates and n can be floats
        
        #first we get total time for the sequence: in units of pi time(2.5us)/actual time + n* 4cycle of 125MHz time (8ns) for n number of gates
        #we also check if the time is implemented correctly
        gate_time_nor = 2504/(1000/self.nor)
        cycle_time_nor = 8/(1000/self.nor)
        time_nor = 1/(1000/self.nor)
        gate_list = _np.array(gate_list)
        #print(type(gate_list))
        #we will replace the original input list to an array with normalized time
        
        #we need an offset array to count the offsets of every starttime due to rounding
        #Note offset[i] is the offset before ith layer
        #offset[0] = 0 always
        offset = _np.zeros(len(gate_list)+1)
        for i in range(len(gate_list)):
            start_time = gate_list[i][0]
            duration = gate_list[i][1]
            print(start_time,duration)
            start_time = _np.ceil(start_time['ns']) * time_nor + offset[i]
            r = _np.round(_np.remainder(start_time, cycle_time_nor))
            if r < 0.005 or r > cycle_time_nor - 0.005:
                r = 0
                #print(r)
            else:
                #pass
                r = cycle_time_nor - r
                #print(r)
            offset[i] += r
            start_time += r
            
            duration = _np.ceil(duration['ns']) * time_nor
            r = _np.round(_np.remainder(duration, cycle_time_nor))
            if r < 0.005 or r > cycle_time_nor - 0.005:
                r = 0
                #print(r)
            else:
                r = cycle_time_nor - r
                #pass
            #    print(r)
            offset[i] += r
            offset[i+1] += offset[i]
            gate_list[i][0] = start_time
            gate_list[i][1] = duration
            print(start_time,duration)
            """
            #Note: THis is a risky move as we add pi-time as a unit in the labrad.units file

            if start_time.units == 'pi-time':
                start_time = start_time['pi-time'] * gate_time_nor
            else:
                start_time = start_time['ns'] * time_nor
            #first check if the divisible things make sense
            r = _np.abs(_np.remainder(start_time, cycle_time_nor))
            if r < 0.005 or r > cycle_time_nor - 0.005:
                pass
            else:
                print(r)
                raise Exception("wrong gate start time")
            gate_list[i][0] = start_time
            
            if duration == 'pi-time':
                duration = duration['pi-time'] * gate_time_nor
            else:
                duration = duration['ns'] * time_nor
            r = _np.abs(_np.remainder(duration, cycle_time_nor))
            if r < 0.005 or r > cycle_time_nor - 0.005:
                pass
            else:
                print(r)
                raise Exception("wrong gate duration time")
            gate_list[i][1] = duration
            """
            
        total_time = (gate_list[-1][0]+gate_list[-1][1])+len(gate_list)*4*cycle_time_nor
        total_time = int(_np.ceil(total_time))
        #create the wf array with the total time, this can be much faster than np.concat/np.append
        wf = _np.zeros(total_time)
        #we need a time_counter to make sure there is no overlap
        time_counter = 0
        for gate_index in range(len(gate_list)):
            gate_start,gate_duration,gate_type = gate_list[gate_index]
            gate_duration = int(_np.round(gate_duration))
            gate_name = gate_type+"_"+str(gate_duration)+"pts"
            #normalize gate time and gate start time
            #print(gate_start+gate_index*4*cycle_time_nor,gate_duration+4*cycle_time_nor)
            gate_start = int(_np.round(gate_start+gate_index*4*cycle_time_nor))
            gate_duration = int(_np.round(gate_duration+4*cycle_time_nor))
            if gate_start >= time_counter:
                time_counter = gate_start+gate_duration
            else:
                
                raise Exception("gate sequence time not specifying correclty")
            try:
                print(gate_start,gate_start+gate_duration)
                wf[gate_start:gate_start+gate_duration] = _np.load("waveform/gates/"+gate_name+".npy")
            except:
                pt = _np.linspace(0,gate_duration-1,gate_duration)
                #now we need to make the gate 
                gate = gate_type.split("_")
                #single qubit gate: gatename, phi
                if len(gate)==2:
                    gate_phi = int(gate[1])/180*_np.pi
                    print(gate_phi)
                    gate = gate[0]
                    wf[gate_start:gate_start+gate_duration] = gatedict.gatedict[gate](gate_phi,pt)
                #two qubit gate
                #tukey phi phi
                elif len(gate)==6:
                    gate_phi = int(gate[1])/180*_np.pi
                    #mu in MHz
                    gate_mu = float(gate[2])
                    #v for relative amplitude:
                    v1 = int(gate[3])
                    v2 = int(gate[4])
                    alpha = float(gate[5])
                    #print(gate_phi)
                    gate = gate[0]
                    print(gate_start,gate_start+gate_duration)
                    wf[gate_start:gate_start+gate_duration] = gatedict.gatedict[gate](gate_phi,gate_mu,v1,v2,alpha,pt)
                elif len(gate)==4:
                    gate_phi_list = gate[1].split(",")
                    gate_phi = []
                    for i in gate_phi_list:
                        gate_phi.append(float(i)/180*_np.pi)
                    #mu in MHz
                    gate_mu_list = gate[2].split(",")
                    gate_mu = []
                    for i in gate_mu_list:
                        gate_mu.append(float(i))
                    #v for relative amplitude:
                    gate_v_list = gate[3].split(",")
                    gate_v = []
                    for i in gate_v_list:
                        gate_v.append(float(i))
                    #print(gate_phi)
                    gate = gate[0]
                    print(gate_start,gate_start+gate_duration)
                    wf[gate_start:gate_start+gate_duration] = gatedict.gatedict[gate](gate_phi,gate_mu,gate_v,pt)
                elif len(gate)>2:
                    gate_phi = int(gate[1])/180*_np.pi
                    #mu in MHz
                    gate_mu = float(gate[2])
                    #v for relative amplitude:
                    v1 = int(gate[3])
                    v2 = int(gate[4])
                    #print(gate_phi)
                    gate = gate[0]
                    print(gate_start,gate_start+gate_duration)
                    wf[gate_start:gate_start+gate_duration] = gatedict.gatedict[gate](gate_phi,gate_mu,v1,v2,pt)
                else:
                    gate = gate[0]
                    wf[gate_start:gate_start+gate_duration] = gatedict.gatedict[gate](pt)
                _np.save("waveform/gates/"+gate_name,wf[gate_start:gate_start+gate_duration])
        _np.save("waveform/gates/two_MS_example",wf)
        #we add 300*10ns delay as we trigger both the switch and awg using the same ttl 
        self.awg.AWGfromArray(channel, triggerMode=6, startDelay=300, cycles=repetition, prescaler=None, waveformType=0, waveformDataA=wf, paddingMode = 0)
        self.awg.channelWaveShape(channel, 6)
        if abs(amplitude["V"]) < hardwareConfiguration.channel_awg_amp_thres[channel-1]:
            self.awg.channelAmplitude(channel, amplitude["V"])
        else:
            raise Exception("the amp is bigger than the set threshold")       
        
        return WithUnit(total_time*(1000/self.nor),'ns')
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(keysightAWGServer())
