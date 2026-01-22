import numpy as np
import sys
sys.path.append("C:/Users/Cryo_rdyberg/Documents/Codebase/Lab_control/config/awg/")
from awgConfiguration import hardwareConfiguration

if hardwareConfiguration.model == "M3201A":
        nor = 500
else:#if hardwareConfiguration.model == "M3202A":
        nor = 1000

AOM_freq = hardwareConfiguration.AOM_freq
cycle_time = hardwareConfiguration.cycle_time #in unit of ns
time_nor = 1/(1000/nor)
cycle_pt = int(cycle_time*time_nor)


class gatedict(object):
    
    def sigma_phi(phi,pt):
        wf = np.cos(2*np.pi*pt*time_nor*AOM_freq/1000+phi)
        #print(phi)
        #phi_time = int(phi/(2*np.pi)*cycle_pt)
        #wf[:phi_time] = 0
        wf[len(pt)-4*cycle_pt:] = 0
        #print(phi_time,-4+phi_time)
        return wf
    
    def sigma_phi_hann(phi,pt):

        l=int(len(pt)-4*cycle_pt)
        wf = np.zeros(len(pt))
        wf[:len(pt)-4*cycle_pt] = 1/2*(1-np.cos(2*np.pi*pt[:len(pt)-4*cycle_pt]/(l)))*np.cos(2*np.pi*pt[:len(pt)-4*cycle_pt]*time_nor*AOM_freq/1000+phi)
        wf[len(pt)-4*cycle_pt:] = 0
        return wf

    def sigma_phi_hamming(phi,pt):
        a0 = 25/46
        l=int(len(pt)-4*cycle_pt)
        wf = np.zeros(len(pt))
        wf[:len(pt)-4*cycle_pt] = (a0 - (1-a0)*(np.cos(2*np.pi*pt[:len(pt)-4*cycle_pt]/(l))))*np.cos(2*np.pi*pt[:len(pt)-4*cycle_pt]*time_nor*AOM_freq/1000+phi)
        wf[len(pt)-4*cycle_pt:] = 0
        return wf
    
    def sigma_phi_tukey(phi,pt):

        #set alpha for tukey pulse
        alpha = 0.3
        l=int(alpha*(len(pt)-4*cycle_pt))
        wf = np.zeros(len(pt))
        wf[:l] = 1/2*(1-np.cos(np.pi*pt[:l]/(l)))*np.cos(2*np.pi*pt[:l]*time_nor*AOM_freq/1000+phi)
        wf[l:len(pt)-4*cycle_pt-l] = np.cos(2*np.pi*pt[l:len(pt)-4*cycle_pt-l]*time_nor*AOM_freq/1000+phi)
        wf[len(pt)-4*cycle_pt-l:len(pt)-4*cycle_pt] = 1/2*(1-np.cos(np.pi*pt[l:2*l]/(l)))*np.cos(2*np.pi*pt[len(pt)-4*cycle_pt-l:len(pt)-4*cycle_pt]*time_nor*AOM_freq/1000+phi)
        wf[len(pt)-4*cycle_pt:] = 0
        return wf
        
    def sigma_x(self, pt):
        return self.sigma_phi(0,pt)

    def sigma_y(self, pt):
        return self.sigma_phi(np.pi/2,pt)

    def blank(pt):
        return pt*0
    

#two Qubit MS Gate part, for ions only

#     
#change the spin phi: phi_b+phi_r)/2  see Luming duan Yukai Wu PRA   
    def phiphi(phi, mu, v1, v2, pt):


        wf = v1*np.cos(2*np.pi*pt*time_nor*(AOM_freq-mu)/1000+phi)
        wf += v2*np.cos(2*np.pi*pt*time_nor*(AOM_freq+mu)/1000+phi)
        wf = wf/(v1+v2)
        wf[len(pt)-4*cycle_pt:] = 0
        return wf

    def phiphi_tukey(phi, mu, v1, v2, alpha, pt):

        l=int(alpha*(len(pt)-4*cycle_pt))
        
        wf = v1*np.cos(2*np.pi*pt*time_nor*(AOM_freq-mu)/1000+phi)
        wf += v2*np.cos(2*np.pi*pt*time_nor*(AOM_freq+mu)/1000+phi)
        wf = wf/(v1+v2)
        wf[:l] = 1/2*(1-np.cos(np.pi*pt[:l]/(l))) * wf[:l]
        wf[len(pt)-4*cycle_pt-l:len(pt)-4*cycle_pt] = 1/2*(1-np.cos(np.pi*pt[l:2*l]/(l))) * wf[-4*cycle_pt-l:-4*cycle_pt]
        wf[len(pt)-4*cycle_pt:] = 0
        return wf        
    
#arbitray detuning gate, now phi, mu and v are lists
    def detuning(phi, mu, v, pt):

        #first check if all the lists have the same length
        if len(phi) != len(mu) or len(v) != len(mu) or len(phi) != len(v):
            raise Exception("gate parameters not correct")
        wf = 0
        for i in range(len(phi)):
            #print(v[i],mu[i],phi[i])
            wf += v[i]*np.cos(2*np.pi*pt*time_nor*(AOM_freq-mu[i])/1000+phi[i])
        wf = wf/(np.sum(v))
        #print(np.sum(v))
        #print(np.max(wf))
        wf[len(pt)-4*cycle_pt:] = 0
        return wf
    

#Fred keep the old code for the IQ, so the time_nor part is not added. Only if we need to use the M3200 series
#If IQ part is not correct in this version, one can back-retract to the older config in github

#For IQ modulation with prescale 2, cycle time is 2nor/500
    def IQ_blank(pt):
        return pt*0    
        
    def IQ_phi(phi,pt):

        IQ_cycle_pt = int(2*nor/500)
        length = int(len(pt)/2)
        pt[:length] = np.cos(phi)*np.ones(length)
        pt[length:] = np.sin(phi)*np.ones(length)
        #pt[length-4*IQ_cycle_pt:] = 0
        pt[length-4*IQ_cycle_pt:length] = 0
        return pt
    
    #how to make the balance needs to calibrate by the experiment, need further implementation
    def IQ_phi_phi(phi, mu, v1, v2, pt):

        IQ_cycle_pt = int(2*nor/500)
        length = int(len(pt)/2)
        vdiff = v1-v2
        wf = np.zeros(len(pt))
        #we set prescale = 2
        wf[:length] = np.sin(-2*np.pi*(2*mu)*pt[:length]/(nor/(2*5)))
        wf[length:] = np.zeros(length)
        #pt[len(pt)-4*IQ_cycle_pt:] = 0
        pt[length-4*IQ_cycle_pt:length] = 0      
        return wf
        
        
    gatedict = {'sigma': sigma_phi, 'sigmatukey':sigma_phi_tukey, 'sigmahann':sigma_phi_hann, 'sigmahamming': sigma_phi_hamming, 'phiphi': phiphi, 'phiphitukey': phiphi_tukey, 'blank': blank, "detuning":detuning,
    "IQblank": IQ_blank, "IQphi": IQ_phi, "IQphiphi": IQ_phi_phi
    }
    
    