import copy
import itertools
import os
import time

import ctypes
import time
import numpy as np
import pandas as pd
from datetime import datetime

import csv, math, os, sys, copy, random, json
from numpy import asarray, savetxt
from scipy.optimize import curve_fit
from scipy.integrate import quad
from scipy.io import loadmat



from numba import njit
from line_profiler import LineProfiler



# %load_ext autoreload
# %autoreload 2  # automatically reloads changes made to labrad_helpers.py
import sys, os
def add_path_up(levels=2):
    target = os.path.abspath(os.path.join(os.getcwd(), *['..']*levels))
    if target not in sys.path:
        sys.path.append(target)
    print("Added to path:", target)
add_path_up(3)
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/script_scanner")
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/experiment_scripts_Cs/experiment_phases")



import labrad

from json import JSONEncoder

from labrad_helpers import (
    _parseInstructions,
    _engageCamera,
    jsonize
)


import matplotlib.pyplot as plt
#import networkx as nx
import numpy as np
from typing import Iterable

from labrad.units import WithUnit
import logging
import warnings
from logging.handlers import RotatingFileHandler

from phase import phase


from experiment import experiment
from Experiment_config import *

class experiment_phases(experiment):
    """ Class that runs an experiment made up of phases, using waveforms programmed on hardware """

    name = 'rydberg_experiment'
    parameter_name = "exp_base"
    scanpara_names = []
    #used for logging the scan value information
    scan_value_list = []
    USEPMT = False
    
    
    @classmethod
    def all_required_parameters(cls):
        pass
    
    #we use this function to get the directory for saving data, as it is tied with the experiment performed time
    def get_dir(self,dirc):
        self.dir = dirc

    def _find_seq_length(self):
            # now find the total duration of the sequencey by looking at the last phases
        self.tend = 0
        for p in self.last:
            if p.tstart + p.tlen > self.tend:
                self.tend = p.tstart + p.tlen

        # generate a flat list of phases sorted by start time
        self.phases_flat = list(flatten(self.phases))
        self.phases_flat_sorted = [self.phases_flat[x] for x in
                                    np.argsort([p.tstart for p in self.phases_flat], kind='stable')]
        #print(self.phases_flat_sorted)
        #print(self.tend)
        self.parameters['general']['seqlen'] = WithUnit(self.tend,'s')


    def _initialize(self):

        # initialize tstart for all phases
        # this will run getlength() exactly once for each phase
        for p in self.first:
            #print(p)
            p.setup(self.parameters,self.cxn)

        # now find the total duration of the sequencey by looking at the last phases
        self._find_seq_length()

        if self.parameters['general']['verbose']:
            for p in self.phases_flat_sorted:
                print(p.__repr__(), 'start time: {:.7f}[s]'.format(p.tstart),
                      'takes: {:.7f}[s]'.format(p.getlength(self.parameters[type(p).__name__])))
            print('\ntime per run: ' + str(self.parameters['general']['seqlen']['s'] * self.parameters['general']['nLoops']) + ' seconds')
        try:
            self.TTL = self.cxn.finitedopulses
            self.ao = self.cxn.aoserver
            self.pulser = self.cxn.pulser
            self.TTL.blankwaveform(self.parameters['general']['seqlen']['s'])
            self.ao.blankwaveform(self.parameters['general']['seqlen']['s'])
            self.pulser.new_sequence()
            self.pulser.line_trigger_state(True)
        except Exception as e:
            print(e)
        
        print('init, set up pulser')
        
        # self.reset()
        
        #instruments that initialization are phase dependent (e.g. camera, SLM) will be defined in the phase and excuted here
        #TODO: Some functions (e.g. initialize_cam) should only excute once (maybe should be put in setup)
        #while some functions (e.g. wait_pvcam) should be put here as _initialize will excute every time
        
        # flatten phases and generate sorted list
        # self.plot_phase_graph()


    def _reset(self):
        """ Reset phases and delete stored parameters, to be ready to run again. """
        #self.params = {}

        for p in self.phases_flat:
            p.initialized = False
            p.tstart = None
            p.tlen = None

        #self.ad.reset()

    def _run_before(self):
        """ Stuff that needs to run before dophases(), ie initializting servers, generators, etc """
        #self._initCountersAndConstants(True)    
        # self._waitPvcam(True)

        # print('Align trap')
        # if self.params['isAlignTraps']:
        #     self._alignTrap()
        # if 'isMoveUVMotor' in self.params.keys() and self.params['isMoveUVMotor']:
        #     self._moveUVMotor()
        # # self._recordWavelength()  # Take this out in the future debug 09/10/2023
        # print('init aod')
        # self._initAOD(True)
        # self._initCamera(True)
        # self._setSLM(True)
        # self._servo369()

        # self._resetNICard()
        # self._setPushBeam()
        # self._setMOTBeam()
        # self._setImagingBeam(verbose=True)
        # self._setUVLED()
        # self._setNICard()
        # self._setMOTElectrodes(verbose=True)
        # self._set649And770()
        # self._set399(verbose=True)
        # self._servo770()
        # self._servo302()
        # self._initAWGDispatcher()
        # self._makeSaveDir()
        # print(self.params['colFreq0Arr_MHz'])
        print("before do phase")
        self._dophases()



    def _dophases(self):

        for p in self.phases_flat_sorted:
            #print("test")
            #phase_para_info is loaded while doing initialization when getting time length in phase.py
            p.dophase(self.cxn,p.phase_para_info)


    def _makeSaveDir(self):

        if not os.path.exists(self.prefix + '\\pvcam'):
            os.makedirs(self.prefix + '\\pvcam')
        if not os.path.exists(self.prefix + '\\nuvu'):
            os.makedirs(self.prefix + '\\nuvu')

    def _run_after(self):
        """ Stuff that runs after dophases, ie, setting up cameras
            config AWG
        """
        #self._runAODProgram()
        #self._programSpecAWG()
        #self._setNICardFinalStates()
        self._setUpCameras()

    def _setUpCameras(self):
        image_file_name = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        image_folder_path = self.parameters["general"]["target_path"]
        self.cxn.pvcamNuvuRfsocServer.acquireFastSequence(image_folder_path ,image_file_name, 2*int(self.parameters["general"]['nLoops']))
        #self.cxn.pvcamNuvuRfsocServer.acquireFastSequence(self.parameters["imaging"]['save_dir'],self.parameters["imaging"]["save_params"],int(self.parameters["general"]['nLoops']))
        #    self.prefix,
        #    getSaveName(self.params, self.params['saveParams']),
        #    self.params['nLoops'])
        #PREFIX: directory to save results

        acquistionStatus = self.cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
        acquistionWaitIndex = 0
        while (acquistionStatus == False or acquistionWaitIndex > 60):
            time.sleep(1)
            acquistionStatus = self.cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
            acquistionWaitIndex += 1
            print('wait {:.1f}s for acquistion to get ready'.format(acquistionWaitIndex))
        if acquistionStatus == False:
            raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server (acquisition)')

    def _initializeCamera(self):
        #####_initCamera
        self.cxn.pvcamNuvuRfsocServer.initPvCam([ROIleft,ROItop,ROIwidth,ROIheight],self.parameters['imaging']['exposure_time']) #ROI: [x0,y0,len,len] and exposure time

        #clear previous sequence
        self.cxn.pvcamNuvuRfsocServer.clearSequence()
        #image status decide if the previous programmed sequence is finished or not
        imageStatus = self.cxn.pvcamNuvuRfsocServer.isSequenceFinished()
        
        ######_waitPvcam
        #@@@@a timer for 60s
        imageWaitIndex = 0
        while (imageStatus == 0 or imageWaitIndex > 60):
            time.sleep(1)
            imageStatus = self.cxn.pvcamNuvuRfsocServer.isSequenceFinished()
            imageWaitIndex += 1
            print('wait {:.1f}s for image to finish'.format(imageWaitIndex))
        if imageStatus == False:
            raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server')

        #Here will need to change between cycles as some of the parameter (e.g. timing can change)
        #but I think a lot of time the inst_lst is the same, so it is also possible to put it in the previous sec

        #generate a instruction list: simplest now set to just take one image and save it somewhere
        ### @@@@
        inst_lst = _parseInstructions()

        if type(inst_lst) == dict:
            inst_lst = [inst_lst]
        elif type(inst_lst) is not list:
            raise ValueError('Instructions of imaging phase needs to be a list of dicts')
        self.cxn.pvcamNuvuRfsocServer.acquireImage('pvcam')
        for istr in inst_lst:
            self.cxn.pvcamNuvuRfsocServer.process(jsonize(istr))

    def save_report_as_txt(self, report_str, filename="\\metadata.txt"):
        folder_path = self.parameters["general"]["target_path"]
        with open(folder_path+filename, "a", encoding="utf-8") as file:
            file.write(report_str)



    def _run_wait(self):
        """ Actually start the sequence, and wait for it to finish """
        #print(self.params)
        print('run waveforms, number of loops:', self.parameters['general']['nLoops'])
        self.cxn.pulser.program_sequence()
        self.cxn.pulser.start_number(int(self.parameters['general']['nLoops']))
        self.cxn.aoserver.runwaveform(int(self.parameters['general']['nLoops']))
        self.cxn.finitedopulses.runwaveform(int(self.parameters['general']['nLoops']))

        self._loopWhileRunWaveform()
        self.cxn.pulser.stop_sequence()

    def _loopWhileRunWaveform(self):
        scanTime = self.parameters['general']['seqlen']['s'] * self.parameters['general']['nLoops']
        print("scantime: "+str(scanTime))
        time_start = time.time()
        nPerLoop = self.cxn.finitedopulses.nPoints()
        nTotal = nPerLoop * self.parameters['general']['nLoops']

        runCounter = -1
        while (time.time() - time_start) < (scanTime + 0.1):
            ns = int(self.cxn.finitedopulses.getNumSampsWritten())
            runNumber = ns / nPerLoop
            # if runNumber > runCounter and ns != nTotal:
            #     runCounter = runNumber
            #     print(ns, ns / nPerLoop)

    def _run_cleanup(self):

        """ Handle any image saving, etc. """

        pass

    def _run_analysis(self):
        """ If there is any automatic analysis to do, do it here """
        pass
    

    def initialize(self, cxn, context, ident):
        #basic instruments(e.g. camera) that intialization not depend on phase will be initialized here
        #but pulser, NI cards will be initialize in _initialize() as during scan it will need to be refresh every scan pt
        self._initialize()
        self._initializeCamera()






#    def run(self, cxn, params, prefix, keys={}):

# We define the heirarchy of params (follows but changed from Jeff), from lowest to highest priority:
# 1. "global params" loaded from datavault (ie, calibration results, exp params)
# 2. scanpara (aka iterlist) (highest priority)
#
# we want scanpara_list to be a list of scanpara, it will be generated via iter over one (or more) scan parameters over a parameter in the required paramter 
#(locally will not change the actual vaule on the paramtervault, but this also breaks the max min lock, maybe we can write something that limit the vaulue of scan paramter)
#The input will be a list of withunits, where the first value will be reflected on y axis rsg

#[WithUnit(1,'ms'), WithUnit(2,"MHz")]
    def run(self, cxn, context, scanpara_list=[]):
        #analyze scanpara
        #we want to trace down the scanpara and update it locally
        #print(self.parameters[self.scanpara_names[0][0]][self.scanpara_names[0][1]])
        # Import the time library


    # Calculate the start time
        start = time.time()
        #print(start)

        self.scan_value_list.append(scanpara_list)
        for i in range(len(scanpara_list)):
            scan_unit = scanpara_list[i].units
            self.parameters[self.scanpara_names[i][0]][self.scanpara_names[i][1]] = scanpara_list[i]
            print(str(self.scanpara_names[i])+" changed to "+str(scanpara_list[i]))

        #scan_unit = scanpara_list[0].units
        self._reset()
        self._initialize()
        #print(self.params)
        """ Run the experiment. Keys is a dictionary of the variables/values associated with the scan,
        which should be used to generate filenames but also to save any automatic analysis results. """
        self._run_before()
        self._run_after()
        end = time.time()
        print("D")
        print( end - start)
        self._run_wait()
        self._run_cleanup()
        val = self._run_analysis()
        # add result to our dictionary. Note that in python > 3.7, dict objects
        # remember the order in which keys were added, so we do it this way to ensure that
        # the first key is the primary variable being iterated over, the next keys are the secondary iterators,
        # and 'value' is the data point.
        new_result = {}
        #new_result.update(keys)
        #new_result['value'] = val
        #self.results.append(new_result)
        end = time.time()
        print("F")
        print( end - start)
        return [0,0]
        #return[scanpara_list[0][scan_unit],0]

    def finalize(self, cxn, context):
        scan_report = "scan "+str(self.scanpara_names)+" with lists:"+str(self.scan_value_list)+"\n"
        self.save_report_as_txt(scan_report)
        self.save_report_as_txt(self.parameters.makeReport())
        print('finalize')


    def plot_phase_graph(self):

        # this is a multi-directed graph, which allows edges going both ways between a set of nodes
        # we use it to plot both the forward and backward edges, to make sure the graph is properly constructed
        # in principle, the forward and backward graphs should give the same information so we would only need to plot
        # one if we were confident that they are right.
        dg = nx.MultiDiGraph()
        labeldict = {}
        posdict = {}
        fixed = []

        for idx, p in enumerate(self.phases_flat):
            # for idx,p in enumerate(phases_flat_sorted):

            # add a directed edge to all of the next phases
            for pl in p.next_phase:
                if pl is not None:
                    dg.add_edge(id(p), id(pl))

            # add a backward edge to all of the previous phases
            for pl in p.prev_phase:
                if pl is not None:
                    dg.add_edge(id(p), id(pl))

            if p.tstart is not None:
                labeldict[id(p)] = "%s\n%.2f" % (str(p), p.tstart)
            else:
                labeldict[id(p)] = "%s" % (str(p))

            # pos_x = p.tstart
            # give everything an x coordinate based on the order in which it will run
            pos_x = self.phases_flat_sorted.index(p)

            # give random y coordinates for phases out of the main list, and let networkx move them around
            pos_y = 0 if p in self.phases else idx / 20.

            posdict[id(p)] = [pos_x, pos_y]

            # fix the position of phases in the main list
            if pos_y == 0:
                fixed.append(id(p))

        # add start and end nodes for clarity
        for p in self.first:
            dg.add_edge("start", id(p))

        for p in self.last:
            dg.add_edge(id(p), "end")

        labeldict["start"] = "start"
        labeldict["end"] = "end"

        posdict["start"] = [-1, 0]
        posdict["end"] = [max([pos[0] for pos in posdict.values()]) + 1, 0]

        fixed.extend(["start", "end"])

        # use spring_layout to find pretty positions. However, we want to restore the original x coordinates afterwards
        pos = nx.spring_layout(dg, pos=None, fixed=None, k=0.3)
        for i, p in pos.items():
            p[0] = posdict[i][0]

        fig, ax = plt.subplots(figsize=(12, 12))
        # nx.draw(dg, labels=labeldict, with_labels=True, pos=pos, width=1.0, node_color='w')
        nx.draw(dg, pos=pos, width=0.5, node_color='w')

        label_options = {"ec": "k", "fc": "white", "alpha": 0.7}
        nx.draw_networkx_labels(dg, labels=labeldict, pos=pos, bbox=label_options)

        plt.show()


def S(*in_phases):
    """This accepts a list of phases or S(), P() function calls, and
    installs the correct forward and backward connections among the phases to
    execute the elements SERIALLY.

    It returns (phases, first, last), where:
        phases = nested list of all phases
        first = tuple indicating which phases occur first
        last = tuple indicating which phases occur last
    """

    phases = []
    required_parameters = []
    prev_phase = (None,)

    for p in in_phases:
        #print(isinstance(p, phase))

        if isinstance(p, phase):
            phases.append(p)
            #print(phases)
            required_parameters += p.required_parameters()
            p.prev_phase = prev_phase

            for pl in prev_phase:
                if pl is not None:
                    pl.next_phase = (p,)

            prev_phase = (p,)

        elif type(p) == tuple:

            for pl in p[1]:
                if pl is not None:
                    pl.prev_phase = prev_phase

            for pl in prev_phase:
                if pl is not None:
                    pl.next_phase = p[1]

            phases.append(p[0])
            required_parameters += p[3]

            prev_phase = p[2]

    # returns phases, first, last
    first = phases[0] if isinstance(phases[0], Iterable) else (phases[0],)
    return phases, first, prev_phase, required_parameters


def P(*in_phases):
    """This accepts a list of phases or S(), P() function calls, and
    installs the correct forward and backward connections among the phases to
    execute the elements IN PARALLEL.

    It returns (phases, first, last), where:
        phases = nested list of all phases
        first = tuple indicating which phases occur first
        last = tuple indicating which phases occur last
    """

    phases = []
    firsts = []
    lasts = []
    required_parameters = []

    for p in in_phases:

        if isinstance(p, phase):
            phases.append(p)
            required_parameters +=p.required_parameters()
            firsts.append(p)
            lasts.append(p)

        elif type(p) == tuple:

            phases.append(p[0])
            required_parameters += p[3]
            firsts.extend(p[1])
            lasts.extend(p[2])

    return phases, tuple(firsts), tuple(lasts),required_parameters


# We want a heirarchy of params, from lowest to highest priority:
# 1. initial params dict (lowest priority)
# 2. "global params" loaded from database (ie, calibration results)
# 3. iterlist (highest priority)
#
# In this approach, a calibration experiment can update the database and the new parameter
# will be used for subsequent experiments in the same and future runs. However, it can be overwritten
# by explicitly scanning that parameter in iterlist, which is how you would perform a new calibration
# experiment.

def update_params(params_in, globals_in, iters_in):
    """ Create a deep copy of params_in, and update it with new_params_in.
    This is so we don't have to make changes to params directly, which would have
    unwanted persistence across multiple runs.

    An alternative way to write this function would be to tell it which global params you want to
    load, and let it go and fetch them from the database server.
    """

    ret = copy.deepcopy(params_in)
    ret.update(globals_in)
    ret.update(iters_in)

    return ret


def iterparams(iterlist, itercond=lambda x: True):
    """ Iterate over all combinations of iterlist, returning a dictionary that can be used to update params and
    a list of actively scanned keys that can be used to make plots and set filenames.

    Returns:
        - idx: index of the iteration, not counting any skipped steps
        - new_params: a params dict containing entries for every key in iterlist
        - keys: a second params dict containing entries for every _scanned_ key in iterlist

    Note that keys.keys() can be used to print which things are being scanned.

    Also, care is taken to ensure that the order of keys in keys is such that the "innermost" (fast)
    scanning items occur _first_. Therefore, if you wanted to automatically generate a plot of the results
    of the experiment, you could guess that the first key in keys should be the x-axis.
    """

    all_keys = list(iterlist.keys())
    # print(iterlist.keys())
    # itertools.product scans over the _last_ argument first
    tuples = itertools.product(*iterlist.values())

    # pull out keys that we are actually iterating over
    iter_keys = [k for k, v in iterlist.items() if len(v) > 1]

    idx = 0

    for t in tuples:

        ret = {}
        ret_keys = {}

        # reversing entries ensures that we scan over the _first_ argument first
        for k, v in zip(reversed(all_keys), reversed(t)):

            ret[k] = v

            if k in iter_keys:
                ret_keys[k] = v

        if itercond(ret):
            # yield makes this into a generator -- when you iterate over the result of this function
            # it will stop here and return the value, then start again at this point the next time you
            # ask.
            yield idx, ret, ret_keys

            idx += 1

def flatten(items):
    """Yield items from any nested iterable; see Reference."""

    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x