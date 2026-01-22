import time
import labrad
import sys
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/experiment_scripts/experiment_phases")
sys.path.append("../servers/script_scanner/")

#IMPORT PHASES
from setBFieldsMOT import setBFieldsMOT
from loadMOT import loadMOT
from imaging import imaging
from absorption_imaging import absorption_imaging
from experiment_phases import experiment_phases, S, P

from labrad.units import WithUnit

#IMPORT SCAN EXPERIMENT BASE CLASSES
from scan_experiment import scan_experiment
from single_sequence import single_sequence
from experiment import experiment


from twisted.internet.threads import deferToThread
import msvcrt

#from experiments_utils import *
#from phaseDefinitions import *

scan_var = 'time'

Scan_points = 60
repetitions_every_point=50

if scan_var == 'time':
    Scan_points = 5
    scan_time_start=WithUnit(0.0,'ms')
    scan_time_end=WithUnit(0.3,'ms')
    #parameter= [("loadMOT", "MOTLoadTime_scan"),("loadMOT", "pushBeamPower_mW_scan")]
    parameter = [("absorption_imaging", "image_time")]

#timeZero = time.time()
#cxn = labrad.connect()
#T = labrad.types



#customDate = None
#customRun = None



#savedir = "./test"

def exp_sequence():
    return S(absorption_imaging())








class absorption_imaging_experiment(experiment_phases):
    #for all parameters that are used in the experiment but not in the phases included
    required_parameters = [("general","nLoops"), ("general","nExperimentsPerLoop"), ("general","verbose"), ("general","seqlen"),("absorption_imaging", "image_time"),("absorption_imaging", "imaging_delay")]
    first = None
    phases = None
    last = None

    def __init__(self, name=None, required_parameters=None, cxn=None, min_progress=0.0, max_progress=100.0):
        #self.phases, self.first, self.last,load_required_parameters = exp_sequence()
        #self.required_parameters += load_required_parameters 

        #need to be removed later, depending if we need global variables like an array (or we can just pass a dir in parameter vault)
        #now self.params["seqlen"] are used for calculating time for a single run
        self.params = {}
        self.results = []
        super().__init__(name, self.required_parameters, cxn,min_progress, max_progress)

    @classmethod
    def all_required_parameters(cls):
        if cls.first == None:
            cls.required_parameters += cls._load_parameters_before_init()
        print("running it")
        parameters = set(cls.required_parameters)
        parameters = list(parameters)
        #print(cls.required_parameters)
        return parameters
    
    #This function is used for loading parameters for the SC GUI. In the SC GUI it will call @classmethod all_required_parameters to load paramters
    #@classmethod function will run itself before the class is initialized, that's why we need this function here to avoid an empty parameters
    # we also used it to initialize our experiment seq by letting cls.phase, cls.first cls.last to be what needed to be
    #In this way we do not need to rerun exp_sequence again to find out the first and last phases
    @classmethod
    def _load_parameters_before_init(cls):
        cls.phases, cls.first, cls.last,required_parameters = exp_sequence()
        #print(cls.first)
        return required_parameters
    

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    if scan_var=='time':
        exprt = scan_experiment(absorption_imaging, parameter, scan_time_start['s'], scan_time_end['s'], Scan_points, 's')
    else:
        exprt = single_sequence(absorption_imaging)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
