from phase import phase
from labrad.units import WithUnit

#Think of a good way to handle parameters with parameter vault
#for parameter vault, we always specify the parameters needed for the exp before the start of the exp,
#we label data in the format of (collection, data), with some data formats supported in labrad
#we want to label the data in the format of (phase, data), with the capability of scan para inside the phase as well


#e.g. in this phase, we need the following params:
#bx0,by0,bz0 in WithUnit (value,V) format

class coolPGC(phase):
    parameter_names = ['pgc_time','by0', 'bz0']
    
    def __init__(self,**kw):
        #print(self.required_parameters)
        super().__init__(**kw)


    def dophase(self, cxn, params):
        ################
        ###### Phase2: PGC cooling
        cxn.ttl.PulseOn(self.config_info.tweezer_slm_AOM, self.tstart, params['pgc_time'])
        ### nulling B field
        cxn.ao.setvoltagepulse(self.config_info.bias_fieldx, self.tstart, duration-mot_loading_time-dt, WithUnit(bias_xv_for_nulling,"V")) ## 
        if sequence == "optical_pumping":
            cxn.ao.setvoltagepulse(self.config_info.bias_fieldy, self.tstart, delay_after_loading + pgc_time, WithUnit(bias_yv_for_nulling,"V")) ## need to be changed after pgc cooling to define quanti. axis
        else:
            cxn.ao.setvoltagepulse(self.config_info.bias_fieldy, self.tstart, duration-mot_loading_time-dt, WithUnit(bias_yv_for_nulling,"V"))
        ### switch Bz from the one for mot loading to the PGC configuration which is in an opposite direction.
        # The dt here makes sure Bz is back to the value for loading before starting a new shot.
        cxn.ttl.PulseOn(self.config_info.biasBz_direction, self.tstart, duration-mot_loading_time-dt) 
        cxn.ao.setvoltagepulse(self.config_info.bias_fieldz, self.tstart, duration-mot_loading_time-dt, WithUnit(bias_zv_for_nulling,"V")) ## 


        ### change the cooling light detuning and amp right after turning off MOT
        cxn.ao.setvoltagepulse(self.config_info.offsetlock, loading_tot_time, duration-loading_tot_time-dt, WithUnit(coolingdetune_for_pgc, "V")) 
        ##### in format (channel num, start time, duration, voltage), The voltage corresponds to -10MHz/V i.e., -2Gamma/V for voltage between -7 and 7V.
        cxn.ao.setvoltagepulse(self.config_info.three_d_motcxn.aoM_amp, loading_tot_time, duration - loading_tot_time -dt, WithUnit(coolingamp_for_pgc,"V"))
        ### amp keeps the same afterwards (can be modified in future), only change on/off.
                    
        #### cooling beam applied with some delay after turning off MOT to reduce background, 100ms should be more than enough
        cxn.ttl.PulseOn(self.config_info.three_d_motcxn.aoM, loading_tot_time, pgc_time) 
                    
        cxn.ttl.PulseOn(self.config_info.repump_motcxn.aoM, loading_tot_time, pgc_time)
        cxn.ttl.PulseOn(self.config_info.tweezer_camera_trigger, loading_tot_time-6e-4, 1e-5)


    def getlength(self, params):
        return 
    
        