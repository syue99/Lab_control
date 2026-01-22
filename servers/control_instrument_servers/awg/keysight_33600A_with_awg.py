import numpy as np
import pyvisa as visa
from labrad.server import LabradServer, setting
import time
import sys 
sys.path.append('utility/')
from gatedict import gatedict

##Fred add the awg uploading feature based on github.com/samdejong86/Agilent33600
class keysight_33600A(LabradServer):
    name = "keysight_33600A"
    #set up the normalization constant for the different AWG, this nor has unit (Mega Sample/s)
    nor = 1000

    def initServer(self):
        self.rm = visa.ResourceManager()
        self.rigol = self.rm.open_resource(u'USB0::0x0957::0x4807::MY53301919::0::INSTR')

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

    @setting(2, "generatePulse",
         ch='i', width_s='v', period_s='v', vpp='v', offset='v',
         rise_s='v', fall_s='v', burst_cycles='i',
         trigger_source='s', output_load='s')
    def generatePulse(self, c,
                    ch=1, width_s=50e-9, period_s=1e-6, vpp=1.0, offset=0.0,
                    rise_s=5e-9, fall_s=5e-9, burst_cycles=1,
                    trigger_source="EXT", output_load="INF"):
        self._writeCommands(f":OUTP{ch}:STAT OFF")  # Turn off output before configuring

        self._writeCommands(f":OUTP{ch}:LOAD {output_load}")      # Set output load
        self._writeCommands(f":SOUR{ch}:FUNC PULSE")              # Set waveform to pulse
        self._writeCommands(f":SOUR{ch}:PULS:WIDT {width_s}")     # Set pulse width
        self._writeCommands(f":SOUR{ch}:PULS:PERI {period_s}")    # Set pulse period
        self._writeCommands(f":SOUR{ch}:PULS:RISE {rise_s}")      # Set rise time
        self._writeCommands(f":SOUR{ch}:PULS:FALL {fall_s}")      # Set fall time
        self._writeCommands(f":SOUR{ch}:VOLT {vpp}")              # Set voltage amplitude
        self._writeCommands(f":SOUR{ch}:VOLT:UNIT VPP")           # Set voltage unit to Vpp
        self._writeCommands(f":SOUR{ch}:VOLT:OFFS {offset}")      # Set voltage offset

        # one shot per trigger
        self._writeCommands(f":SOUR{ch}:BURS:STAT ON")            # Enable burst mode
        self._writeCommands(f":SOUR{ch}:BURS:MODE TRIG")          # Set burst mode to triggered
        self._writeCommands(f":SOUR{ch}:BURS:NCYC {burst_cycles}")# Set number of burst cycles
        self._writeCommands(f":TRIG{ch}:SOUR {trigger_source}")   # Set trigger source

        self._writeCommands(f":OUTP{ch}:STAT ON")                 # Turn on output


    @setting(3, "AWGbyArray", array='*?', vpp='v',burst_cycles='i', trigger_source="s", output_load="s")
    def AWGbyArray(self,c,array,vpp,burst_cycles,trigger_source="EXT" ,output_load="50"):
        name = "AWGbyArray"
        #we can redine sample rate to be the largest 660Msample/s    
        sRate=str(self.nor*1e6)

        #scale signal between 2**15 and -2**15
        #sig = (np.asarray(array, dtype='f4')/max(array)*(2**15-1)).astype(np.int16)
        sig = np.asarray(array, dtype='f4')/np.max(np.abs(array))
        #print(sig)
        print(np.max(np.abs(array)))
        self._writeCommands(f":OUTP1:STAT OFF") # Turn off output before configuring

        #sent start control message
        message="Uploading\nArbitrary\nWaveform"
        self._writeCommands("DISP:TEXT '"+message+"'")

        #create a directory on device (will generate error if the directory exists, but we can ignore that)
        self._writeCommands("MMEMORY:MDIR \"INT:\\remoteAdded\"")

        #set byte order
        self._writeCommands('FORM:BORD SWAP')

        #clear volatile memory
        self._writeCommands('SOUR1:DATA:VOL:CLE')

        #write arb to device
        self.rigol.write_binary_values('SOUR1:DATA:ARB '+name+',', sig, datatype='f', is_big_endian=False)

        #wait until that command is done
        self._writeCommands('*WAI')

        #name the arb
        self._writeCommands('SOUR1:FUNC:ARB '+name)

        #set sample rate, voltage
        self._writeCommands('SOUR1:FUNC:ARB:SRAT ' + sRate)
        self._writeCommands('SOUR1:VOLT:OFFS 0')
        self._writeCommands('SOUR1:FUNC ARB')
        self._writeCommands('SOUR1:VOLT '+str(vpp))

        #save arb to device internal memory
        self._writeCommands('MMEM:STOR:DATA "INT:\\remoteAdded\\'+name+'.arb"')

        #clear message
        self._writeCommands("DISP:TEXT ''")

        #check for error messages
        instrument_err = "error"
        while instrument_err != '+0,"No error"\n':
            self._writeCommands('SYST:ERR?')
            instrument_err = self.rigol.read()
            if instrument_err[:4] == "-257":  #directory exists message, don't display
                continue
            if instrument_err[:2] == "+0":    #no error
                continue
            print(instrument_err)

        self._writeCommands('MMEMORY:LOAD:DATA1 INT:\\remoteAdded\\'+name+'.arb"')   ##load awg file just saved
        self._writeCommands(f":OUTP1:LOAD {output_load}") # Set output load
        self._writeCommands(f"SOUR1:FUNC ARB") # Set waveform to pulse
        self._writeCommands('SOUR1:FUNCtion:ARBitrary INT:\\remoteAdded\\'+name+'.arb"')
        # one shot per trigger
        self._writeCommands(f":SOUR1:BURS:STAT ON") # Enable burst mode
        self._writeCommands(f":SOUR1:BURS:MODE TRIG") # Set burst mode to triggered
        self._writeCommands(f":SOUR1:BURS:NCYC {burst_cycles}") # Set number of burst cycles
        self._writeCommands(f":TRIG1:SOUR {trigger_source}") # Set trigger source
        self._writeCommands(f":OUTP1:STAT ON") # Turn on output



    @setting(10, "single pulse", vpp='v', drive_time = 'v', phase = 'v', burst_cycles='i' )
    def single_pulse(self, c, vpp, drive_time,phase, burst_cycles):
        total_time = int(np.ceil((drive_time)/(1000/self.nor)))
        # time_nor = 1/(1000/self.nor)
        # gatearray = np.zeros(int(total_time))
        # gatearray = np.cos(2*np.pi*.08/time_nor*np.arange(0,int(total_time),1)+phase)

        #use gatedict to generate gatearray
        pt = np.linspace(0,total_time-1,total_time)
        gatearray = gatedict.gatedict["sigma"](phase,pt)
        gatearray[-1] = 0

        self.AWGbyArray(0,gatearray, vpp,burst_cycles,"EXT","50")

    @setting(11, "single tukey pulse", vpp='v', drive_time = 'v', phase = 'v', burst_cycles='i' )
    def single_tukey_pulse(self, c, vpp, drive_time,phase, burst_cycles):
        total_time = int(np.ceil((drive_time)/(1000/self.nor)))   
        ### self.nor is the sample rate with unit of Mega Sample/s, drive_time in ns, so drive_time * self.nor/1000
        # time_nor = 1/(1000/self.nor)
        #set alpha for tukey pulse
        # alpha = 0.3
        # l=int(alpha*drive_time)
        # gatearray = np.zeros(total_time)
        # #print(l,total_time)
        # gatearray[:l] = 1/2*(1-np.cos(np.pi*np.arange(0,l,1)/(l)))*np.cos(2*np.pi*np.arange(0,l,1)*.08/time_nor+phase)
        # gatearray[l:-l] = np.cos(2*np.pi*np.arange(l,total_time-l,1)*.08/time_nor+phase)
        # gatearray[-l:] = 1/2*(1-np.cos(np.pi*np.arange(l,0,-1)/(l)))*np.cos(2*np.pi*np.arange(total_time-l,total_time,1)*.08/time_nor+phase)

        pt = np.linspace(0,total_time-1,total_time)
        gatearray = gatedict.gatedict["sigmatukey"](phase,pt)
        gatearray[-1] = 0
        #for i in gatearray:
        #    print(i)
        self.AWGbyArray(0,gatearray, vpp,burst_cycles,"EXT","50")


    @setting(12, "composite pulse", vpp='v', half_pi_time='v', pi_time='v', burst_cycles='i')
    def composite_pulse(self, c, vpp, half_pi_time,pi_time, burst_cycles,):
        
        spacing = 0
        total_time = int(np.ceil((2*half_pi_time+pi_time+2*spacing)/(1000/self.nor)))
        print(total_time)
        cycle_time_nor = 25/(1000/self.nor)
        time_nor = 1/(1000/self.nor)
        
        # gatearray = np.zeros(int(total_time))
        # alpha = 0.3

        # t_val_1 = int(np.ceil((half_pi_time)*time_nor))
        # #gatearray[:t_val_1] = np.cos(2*np.pi*.08/time_nor*np.arange(0,t_val_1,1))
        # l=int(alpha*t_val_1)
        # #print(l,total_time)
        # gatearray[:l] = 1/2*(1-np.cos(np.pi*np.arange(0,l,1)/(l)))*np.cos(2*np.pi*np.arange(0,l,1)*.08/time_nor)
        # gatearray[l:t_val_1-l] = np.cos(2*np.pi*np.arange(l,t_val_1-l,1)*.08/time_nor)
        # gatearray[t_val_1-l:t_val_1] = 1/2*(1-np.cos(np.pi*np.arange(l,0,-1)/(l)))*np.cos(2*np.pi*np.arange(t_val_1-l,t_val_1,1)*.08/time_nor)


        # t_val_2 = int(np.ceil((half_pi_time+pi_time+spacing)*time_nor))
        # #gatearray[t_val_1:t_val_2] = np.sin(2*np.pi*.08/time_nor*np.arange(t_val_1,t_val_2,1))
        # l=int(alpha*(t_val_2-t_val_1))
        # #print(l,total_time)
        # gatearray[t_val_1:t_val_1+l] = 1/2*(1-np.cos(np.pi*np.arange(0,l,1)/(l)))*np.sin(2*np.pi*np.arange(t_val_1,t_val_1+l,1)*.08/time_nor)
        # gatearray[t_val_1+l:t_val_2-l] = np.sin(2*np.pi*np.arange(t_val_1+l,t_val_2-l,1)*.08/time_nor)
        # gatearray[t_val_2-l:t_val_2] = 1/2*(1-np.cos(np.pi*np.arange(l,0,-1)/(l)))*np.sin(2*np.pi*np.arange(t_val_2-l,t_val_2,1)*.08/time_nor)

        # #gatearray[t_val_2:] = np.cos(2*np.pi*.08/time_nor*np.arange(t_val_2,total_time,1))
        # l=int(alpha*(total_time-t_val_2))
        # #print(l,total_time)
        # gatearray[t_val_2:t_val_2+l] = 1/2*(1-np.cos(np.pi*np.arange(0,l,1)/(l)))*np.cos(2*np.pi*np.arange(t_val_2,t_val_2+l,1)*.08/time_nor)
        # print(t_val_2+l,total_time-l)
        # gatearray[t_val_2+l:total_time-l] = np.cos(2*np.pi*np.arange(t_val_2+l,total_time-l,1)*.08/time_nor)
        # gatearray[total_time-l:] = 1/2*(1-np.cos(np.pi*np.arange(l,0,-1)/(l)))*np.cos(2*np.pi*np.arange(total_time-l,total_time,1)*.08/time_nor)
        
        gatearray = np.zeros(total_time)

        t_val_1 = int(np.ceil((half_pi_time)*time_nor))
        gatearray[:t_val_1] = gatedict.gatedict["sigmatukey"](0,np.arange(0,t_val_1,1))

        t_val_2 = int(np.ceil((half_pi_time+pi_time+spacing)*time_nor))
        gatearray[t_val_1:t_val_2] = gatedict.gatedict["sigmatukey"](-np.pi/2+2*np.pi*t_val_1*.08*time_nor,np.arange(0,t_val_2-t_val_1,1))

        gatearray[t_val_2:] = gatedict.gatedict["sigmatukey"](2*np.pi*t_val_2*.08*time_nor,np.arange(0,t_val_1))


        amp_nor = 0.8
        gatearray[t_val_1:] = gatearray[t_val_1:]*amp_nor
        gatearray[t_val_1:t_val_1+spacing] = 0
        gatearray[t_val_2:t_val_2+spacing] = 0
        gatearray[-1] = 0
        for i in gatearray:
            print(i)
        self.AWGbyArray(0,gatearray, vpp,burst_cycles,"EXT","50")


    @setting(13, "ramsey pulse", vpp='v', half_pi_time='v', scanning_time = 'v', delta_f = 'v', burst_cycles='i')
    def ramsey_pulse(self, c, vpp, half_pi_time,scanning_time,delta_f, burst_cycles,):
        
        spacing = 0
        total_time = int(np.ceil((2*half_pi_time+scanning_time+2*spacing)/(1000/self.nor)))
        print(total_time)
        cycle_time_nor = 25/(1000/self.nor)
        time_nor = 1/(1000/self.nor)
        
        gatearray = np.zeros(int(total_time))
        alpha = 0.3

        t_val_1 = int(np.ceil((half_pi_time)*time_nor))
        gatearray[:t_val_1] = np.cos(2*np.pi*.08*time_nor*np.arange(0,t_val_1,1))

        t_val_2 = int(np.ceil((half_pi_time+scanning_time+spacing)*time_nor))
        gatearray[t_val_1:t_val_2] = 0 #np.cos(2*np.pi*.081/time_nor*np.arange(t_val_1,t_val_2,1)+phase_at_t_val_1)
        ramsey_phase = 2*np.pi*(.080+delta_f/1000)*time_nor*(t_val_2-t_val_1)


        gatearray[t_val_2:] = np.cos(2*np.pi*.08*time_nor*np.arange(t_val_2,total_time,1)+ramsey_phase)
        
        if scanning_time<500:
            amp_nor = 0.8
        else:
            amp_nor = 1.0
        gatearray[t_val_1:] = gatearray[t_val_1:]*amp_nor
        for i in gatearray:
            print(i)
        self.AWGbyArray(0,gatearray, vpp,burst_cycles,"EXT","50")


    @setting(14, "ramey pulse with diff time", vpp='v', half_pi_time_1='v', half_pi_time_2='v', scanning_time = 'v', delta_f = 'v', burst_cycles='i')
    def ramsey_pulse_diff_t(self, c, vpp, half_pi_time_1,half_pi_time_2,scanning_time,delta_f, burst_cycles,):
        
        spacing = 0
        total_time = int(np.ceil((half_pi_time_1+half_pi_time_2+scanning_time+2*spacing)/(1000/self.nor)))
        print(total_time)
        cycle_time_nor = 25/(1000/self.nor)
        time_nor = 1/(1000/self.nor)
        
        gatearray = np.zeros(int(total_time))
        alpha = 0.3

        t_val_1 = int(np.ceil((half_pi_time_1)*time_nor))
        gatearray[:t_val_1] = np.cos(2*np.pi*.08*time_nor*np.arange(0,t_val_1,1))

        t_val_2 = int(np.ceil((half_pi_time_1+scanning_time+spacing)*time_nor))
        gatearray[t_val_1:t_val_2] = 0 #np.cos(2*np.pi*.081/time_nor*np.arange(t_val_1,t_val_2,1)+phase_at_t_val_1)
        ramsey_phase = 2*np.pi*(.080+delta_f/1000)*time_nor*(t_val_2-t_val_1)


        gatearray[t_val_2:] = np.cos(2*np.pi*.08*time_nor*np.arange(t_val_2,total_time,1)+ramsey_phase)
        
        if scanning_time<500:
            amp_nor = 0.8
        else:
            amp_nor = 1.0
        gatearray[t_val_1:] = gatearray[t_val_1:]*amp_nor
        for i in gatearray:
            print(i)
        self.AWGbyArray(0,gatearray, vpp,burst_cycles,"EXT","50")

# #adapted from the keysight M3202A code
#     @setting(11, "compile gates", vpp='v', pi_time = 'v', burst_cycles='i', gate_list = '*(?,?,s)', returns='v[ns]', )
#     #this might be done using multithreads to speed up
#     def compile_gates(self, c, vpp=None, pi_time = None, burst_cycles = None, gate_list = None):

#         #we specify gates by using the format of (start_time, duration) and for the start time and duration, there can be two different units
#         #1. In the units of regular time s.t. WithUnit(n,'us'). BUT note that n must be divisible by 8. Otherwise we will have an error
#         #2. In the units of pi time s.t. WithUnit(n,'pi-time'). This is used for single qubit gates and n can be floats
        
#         #first we get total time for the sequence: in units of pi time(~0.25us)/actual time + n* 4cycle of 80MHz time (25ns) for n number of gates
#         #we also check if the time is implemented correctly
#         gate_time_nor = pi_time/(1000/self.nor)
#         print(gate_time_nor)
#         cycle_time_nor = 25/(1000/self.nor)
#         time_nor = 1/(1000/self.nor)
#         gate_list = np.array(gate_list)




#         self.AWGbyArray(gate_array, 1,1,"EXT","INF")
#         return WithUnit(total_time*(1000/self.nor),'ns')
    
##not finished
    # @setting(4, "uploadAWG", file_name = 's', amp = 'w', delimiter = 's')
    # def uploadAWG(self,c,filename,amp,delimiter):
    #     if delimiter=="tab":
    #         delimiter="\t"
    #     #remove file extension
    #     name=os.path.splitext(os.path.basename(filename))[0]

    #     #if the arb name is longer than 12, truncate it (maximum length allowed by SCPI interface)
    #     if len(name) > 12:
    #         name=name[:12]
    #         print("Arb name truncated to "+name)

    #     #we can redine sample rate to be the largest 660Msample/s    
    #     samplePeriod=0
    #     num=0
    #     tlast=-1

    #     #load the arbitrary waveform
    #     arb=[]
    #     with open(filename,'r') as f:
    #         reader=csv.reader(f,delimiter=delimiter)
    #         for t,p in reader:
    #             arb.append(float(p))
    #             if tlast != -1:
    #                 samplePeriod=samplePeriod+(float(t)-float(tlast)) #get difference between subsequent time bins
    #                 num=num+1
    #             tlast=t

    #     #get sample rate
    #     samplePeriod=samplePeriod/num
    #     sRate=str(1/samplePeriod)

    #     #scale signal between 1 and -1
    #     sig = np.asarray(arb, dtype='f4')/max(arb)


    #     #sent start control message
    #     message="Uploading\nArbitrary\nWaveform"
    #     self.rigol._writeCommands("DISP:TEXT '"+message+"'")

    #     #create a directory on device (will generate error if the directory exists, but we can ignore that)
    #     self.rigol._writeCommands("MMEMORY:MDIR \"INT:\\remoteAdded\"")

    #     #set byte order
    #     self.rigol._writeCommands('FORM:BORD SWAP')

    #     #clear volatile memory
    #     self.rigol._writeCommands('SOUR1:DATA:VOL:CLE')

    #     #write arb to device
    #     self.rigol.write_binary_values('SOUR1:DATA:ARB '+name+',', sig, datatype='f', is_big_endian=False)

    #     #wait until that command is done
    #     self.rigol._writeCommands('*WAI')

    #     #name the arb
    #     self.rigol._writeCommands('SOUR1:FUNC:ARB '+name)

    #     #set sample rate, voltage
    #     self.rigol._writeCommands('SOUR1:FUNC:ARB:SRAT ' + sRate)
    #     self.rigol._writeCommands('SOUR1:VOLT:OFFS 0')
    #     self.rigol._writeCommands('SOUR1:FUNC ARB')
    #     self.rigol._writeCommands('SOUR1:VOLT '+amp)

    #     #save arb to device internal memory
    #     self.rigol._writeCommands('MMEM:STOR:DATA "INT:\\remoteAdded\\'+name+'.arb"')

    #     #clear message
    #     self.rigol._writeCommands("DISP:TEXT ''")

    #     #check for error messages
    #     instrument_err = "error"
    #     while instrument_err != '+0,"No error"\n':
    #         self.rigol._writeCommands('SYST:ERR?')
    #         instrument_err = self.rigol.read()
    #         if instrument_err[:4] == "-257":  #directory exists message, don't display
    #             continue
    #         if instrument_err[:2] == "+0":    #no error
    #             continue
    #         print(instrument_err)




if __name__ == "__main__":
    from labrad import util
    import ctypes

    ctypes.windll.kernel32.SetConsoleTitleA("keysight_33600A")
    util.runServer(keysight_33600A())









        
