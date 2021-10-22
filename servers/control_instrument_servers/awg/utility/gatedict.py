import numpy as np
import sys
sys.path.append('../../../../config/awg/')
from awgConfiguration import hardwareConfiguration

if hardwareConfiguration.model == "M3201A":
        nor = 500
else:#if hardwareConfiguration.model == "M3202A":
        nor = 1000

class gatedict(object):
    
    def sigma_phi(phi,pt):

        wf = np.cos(2*np.pi*pt*125/nor+phi)
        #a cycle time is 4
        #print(phi)
        cycle_time = int(4*nor/500)
        phi_time = int(phi/(2*np.pi)*cycle_time)
        #wf[:phi_time] = 0
        wf[-4*cycle_time:] = 0
        #print(phi_time,-4+phi_time)
        return wf
    def sigma_phi_hann(phi,pt):
        cycle_time = int(4*nor/500)
        l=int(len(pt)-16)
        wf = np.zeros(len(pt))
        wf[:-4*cycle_time] = 1/2*(1-np.cos(2*np.pi*pt[:-4*cycle_time]/(l)))*np.cos(2*np.pi*pt[:-4*cycle_time]*125/500+phi)
        wf[-4*cycle_time:] = 0
        return wf

    def sigma_phi_hamming(phi,pt):
        cycle_time = int(4*nor/500)
        a0 = 25/46
        l=int(len(pt)-16)
        wf = np.zeros(len(pt))
        wf[:-4*cycle_time] = (a0 - (1-a0)*(np.cos(2*np.pi*pt[:-4*cycle_time]/(l))))*np.cos(2*np.pi*pt[:-4*cycle_time]*125/500+phi)
        wf[-4*cycle_time:] = 0
        return wf
        
    def sigma_phi_tukey(phi,pt):
        cycle_time = int(4*nor/500)
        #set alpha for tukey pulse
        alpha = 0.3
        l=int(alpha*(len(pt)-16))
        wf = np.zeros(len(pt))
        wf[:l] = 1/2*(1-np.cos(np.pi*pt[:l]/(l)))*np.cos(2*np.pi*pt[:l]*125/500+phi)
        wf[l:-4*cycle_time-l] = np.cos(2*np.pi*pt[l:-4*cycle_time-l]*125/500+phi)
        wf[-4*cycle_time-l:-4*cycle_time] = 1/2*(1-np.cos(np.pi*pt[l:2*l]/(l)))*np.cos(2*np.pi*pt[-4*cycle_time-l:-4*cycle_time]*125/500+phi)
        wf[-4*cycle_time:] = 0
        return wf
        
    def sigma_x(self, pt):
        return self.sigma_phi(0,pt)

    def sigma_y(self, pt):
        return self.sigma_phi(np.pi/2,pt)

#for now we ignore phi and just do xx        
    def phiphi(phi, mu, v1, v2, pt):
        cycle_time = int(4*nor/500)

        wf = v1*np.cos(2*np.pi*pt*(125-mu)/nor)
        wf += v2*np.cos(2*np.pi*pt*(125+mu)/nor)
        wf = wf/(v1+v2)
        wf[-4*cycle_time:] = 0
        return wf
        
        
    gatedict = {'sigma': sigma_phi, 'sigmatukey':sigma_phi_tukey, 'sigmahann':sigma_phi_hann, 'sigmahamming': sigma_phi_hamming, 'phiphi': phiphi}
    
    