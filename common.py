import copy
import itertools
import json
import os
import time
from json import JSONEncoder

import labrad
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from typing import Iterable

#import awgdispatcher as ad
#from calibrations import calibrate
#from channels import *
#from pre_experiments.trap_aligner import TrapAligner
#from pre_experiments.uv_aligner import UVAligner
#from servers.C_waveform_calculation_dll import getFileUID

import logging
import warnings
from logging.handlers import RotatingFileHandler

T = labrad.types
parentPath = r'I:/thompsonlab/AMO/Control programs/main_control_program_lite'

# Calibrations____________________________________________________________________________
# specCal = calibrate.Calibrate(parentPath + '/calibrations/blue_spectroscopy_freq_V_MHz.csv')
# specMHzToV = specCal.CalFunction2

# seedCal = calibrate.Calibrate(parentPath + '/calibrations/blue_seedlight_freq_V_MHz.csv')
# seedMHzToV = seedCal.CalFunction2

# detectCal = calibrate.Calibrate(parentPath + '/calibrations/blue_imaging_V_MHz.csv')
# blowoutMHzToV = detectCal.CalFunction2

# motMixerCal = calibrate.Calibrate(parentPath + '/calibrations/motMixer_V_mW.csv')
# MOTPDmWToV = motMixerCal.CalFunction2

# imagingMixerCal = calibrate.Calibrate(parentPath + '/calibrations/imagingMixer_V_mW.csv')
# imagingPDmWToV = imagingMixerCal.CalFunction2

# tweezerMixerCal = calibrate.Calibrate(parentPath + '/calibrations/tweezerPowerCal532_rfsoc_mW_aod_231031.csv')
# tweezerPDmWToRFSoC = tweezerMixerCal.CalFunction2

# tweezerMixerCal_slm = calibrate.Calibrate(parentPath + '/calibrations/tweezerPowerCal486_V_mW_slm.csv')
# tweezerPDmWToV_slm = tweezerMixerCal_slm.CalFunction2

# pushBeamCal = calibrate.Calibrate(parentPath + '/calibrations/pushBeam_V_mW.csv')
# pushBeamPDmWToV = pushBeamCal.CalFunction2

# redTweezerMixerCal = calibrate.Calibrate(parentPath + '/calibrations/redTweezerMixer_V_mW.csv')
# redTweezerPDmWToV = redTweezerMixerCal.CalFunction2

# sisyphusMixerCal = calibrate.Calibrate(parentPath + '/calibrations/sisyphusMixer_V_uW.csv')
# sisyphusPDuWtoV = sisyphusMixerCal.CalFunction2

# specRydbergMixerCal = calibrate.Calibrate(parentPath + '/calibrations/specDetuning_MHz_vs_Mixer_V.csv')
# specRydbergFreqMHztoMixerV = specRydbergMixerCal.CalFunction1


def flatten(items):
    """Yield items from any nested iterable; see Reference."""

    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def jsonize(param):
    return json.dumps(param, cls=NumpyArrayEncoder)


def getSaveName(params, saveParams):
    saveName = ''
    for k in saveParams:
        if type(params[k]) == bool:
            saveName += ",%s=%d" % (k, params[k])
        elif type(params[k]) == int:
            saveName += ",%s=%d" % (k, params[k])
        elif type(params[k]) == str:
            saveName += ",%s=%s" % (k, params[k])
        else:
            saveName += ",%s=%0.9f" % (k, params[k])

    return saveName[1:]  # To get rid of the extra comma at the beginning.


class phase(object):
    def __init__(self, **kw):

        self.prev_phase = (None,)
        self.next_phase = (None,)

        self.kw = {}
        self.kw.update(kw)

        self.tstart = None
        self.tlen = None

        self.initialized = False

    def setup(self, params):

        # first, check if all the previous phases are done
        # and find the longest of the start + len to compute our tstart

        tstart = 0

        for pl in self.prev_phase:
            if pl is not None:
                if pl.initialized == False:
                    return

                # if we get to this point, all the phases preceeding this one
                # have executed, and it's our turn. We compute what our start time
                # is based on the longest of the previous times + lengths

                new_start = pl.tstart + pl.tlen
                if new_start > tstart:
                    tstart = new_start

        # set our start time to this, and calculate our length
        self.tstart = tstart
        self.tlen = self.getlength(params)
        self.initialized = True

        # now try to set up the following phases:
        for pl in self.next_phase:
            if pl is not None:
                pl.setup(params)

    def getlength(self, params):
        # compute length

        print("In getlength for: ", self.__class__.__name__, self.tstart)
        return 1.0

    def dophase(self, cxn, params):
        # NB: instead of passing tstart as a parameter, here, it should now be read from
        # self.tstart

        # print("Running commands for: ", self.__repr__())
        pass

    def print_checkpoint(self):
        # print("Running commands for: {:s}".format(self.__repr__()))
        pass

    def __repr__(self):
        return "%s" % self.__class__.__name__  # , repr(self.kw) if len(self.kw) > 0 else '', self.tstart)


class syncphase(phase):
    def __init__(self, **kw):
        super(syncphase, self).__init__(**kw)
        self.tsync = 0
        if 'tsync' in self.kw.keys():
            self.tsync = self.kw['tsync']
        self.period = None
        if 'period' in self.kw.keys():
            self.period = int(self.kw['period'])

    def setup(self, params):

        # first, check if all the previous phases are done
        # and find the longest of the start + len to compute our tstart

        tstart = 0

        for pl in self.prev_phase:
            if pl is not None:
                if pl.initialized == False:
                    return

                # if we get to this point, all the phases preceeding this one
                # have executed, and it's our turn. We compute what our start time
                # is based on the longest of the previous times + lengths

                new_start = pl.tstart + pl.tlen
                if new_start > tstart:
                    tstart = new_start

        # set our start time to this, and calculate our length
        if self.period is None:
            self.period = int(params['trapModulationTTLPeriod_100ns'])

        if self.tsync >= self.period:
            raise ValueError("In a synced phase: tsync needs to be less than period")

        sample_period_nicard = 0.1e-6
        curr_tstart_int = int(tstart / sample_period_nicard)
        curr_tsync = curr_tstart_int % self.period
        if curr_tsync > self.tsync:
            self.tstart = (curr_tstart_int + self.period - (curr_tsync - self.tsync)) * sample_period_nicard
        else:
            self.tstart = (curr_tstart_int + (self.tsync - curr_tsync)) * sample_period_nicard
        self.tlen = self.getlength(params)
        self.initialized = True

        # now try to set up the following phases:
        for pl in self.next_phase:
            if pl is not None:
                pl.setup(params)


class experiment:

    def run(self, cxn, params):
        """ Does the experiment """
        pass


class experiment_phases(experiment):
    """ Class that runs an experiment made up of phases, using waveforms programmed on hardware """

    def __init__(self, phases, first, last, description="I am too lazy to enter a description of this experiment"):
        # print('Phases', phases)
        self.phases = phases
        self.first = first
        self.last = last
        self.cxn = None
        self.params = {}

        self.description = description

        self.results = []

    def _initialize(self):

        # initialize tstart for all phases
        # this will run getlength() exactly once for each phase
        for p in self.first:
            p.setup(self.params)

        # now find the total duration of the sequencey by looking at the last phases
        self.tend = 0
        for p in self.last:
            if p.tstart + p.tlen > self.tend:
                self.tend = p.tstart + p.tlen

        # generate a flat list of phases sorted by start time
        self.phases_flat = list(flatten(self.phases))
        self.phases_flat_sorted = [self.phases_flat[x] for x in
                                   np.argsort([p.tstart for p in self.phases_flat], kind='stable')]
        self.params['seqLen'] = self.tend

        if self.params['verbose']:
            for p in self.phases_flat_sorted:
                print(p.__repr__(), 'start time: {:.7f}[s]'.format(p.tstart),
                      'takes: {:.7f}[s]'.format(p.getlength(self.params)))
            print('\ntime per run: ' + str(self.params['seqLen'] * self.params['nLoops']) + ' seconds')

    def _reset(self):
        """ Reset phases and delete stored parameters, to be ready to run again. """
        self.params = {}

        for p in self.phases_flat:
            p.initialized = False
            p.tstart = None
            p.tlen = None

        self.ad.reset()

    def _run_before(self):
        """ Stuff that needs to run before dophases(), ie initializting servers, generators, etc """
        self._initCountersAndConstants(True)
        self._waitPvcam(True)

        print('Align trap')
        if self.params['isAlignTraps']:
            self._alignTrap()
        if 'isMoveUVMotor' in self.params.keys() and self.params['isMoveUVMotor']:
            self._moveUVMotor()
        # self._recordWavelength()  # Take this out in the future debug 09/10/2023
        print('init aod')
        self._initAOD(True)
        self._initCamera(True)
        self._setSLM(True)
        self._servo369()

        self._resetNICard()
        self._setPushBeam()
        self._setMOTBeam()
        self._setImagingBeam(verbose=True)
        self._setUVLED()
        self._setNICard()
        self._setMOTElectrodes(verbose=True)
        self._set649And770()
        self._set399(verbose=True)
        self._servo770()
        self._servo302()
        self._initAWGDispatcher()
        self._makeSaveDir()
        # print(self.params['colFreq0Arr_MHz'])
        self._dophases()

    def _dophases(self):

        for p in self.phases_flat_sorted:
            p.dophase(self.cxn, self.params)

    def _moveUVMotor(self):
        print('Taking UV positions')
        ua = UVAligner(self.cxn, self.params)
        log_fname = self.params['UVPicomotorFile']

        def log_picomotor_warnings(log_fname):

            logger_file_handler = RotatingFileHandler(log_fname)
            logger_file_handler.setLevel(logging.DEBUG)

            logging.captureWarnings(True)

            logger = logging.getLogger(__name__)
            warnings_logger = logging.getLogger("py.warnings")

            logger.addHandler(logger_file_handler)
            logger.setLevel(logging.DEBUG)
            warnings_logger.addHandler(logger_file_handler)

        def confirm_to_move(log_fname):
            with open(log_fname, 'r') as f:
                a = f.readline()
            if not a:
                try:
                    self.cxn.audio_player.playaudio('save_params_alert.mp3')
                except:
                    print('Alert audio server failed!')
                ans = raw_input('Confirm that you intend to move picomotor! [y/n]')
                if ans != 'y' and ans != 'Y':
                    raise RuntimeError('Do not move picomotor!')
            warnings.warn("Dangerous behavior: trying to move UV picomotor")

        log_picomotor_warnings(log_fname)
        confirm_to_move(log_fname)

        if 'UVPicoX1' in self.params:
            ua.movePicoTo('X1', self.params['UVPicoX1'])
        if 'UVPicoX2' in self.params:
            ua.movePicoTo('X2', self.params['UVPicoX2'])
        if 'UVPicoZ' in self.params:
            ua.movePicoTo('Z', self.params['UVPicoZ'])
        if 'UVPicoY1' in self.params:
            ua.movePicoTo('Y1', self.params['UVPicoY1'])
        if 'UVPicoY2' in self.params:
            ua.movePicoTo('Y2', self.params['UVPicoY2'])
        ua.getPosition(self.params['whichBeamToTakeUVpos'], self.params['savedir'])
        print('UV positions: cam1_X = %f, cam1_Y = %f, cam1_X_width = %f, cam1_Y_width = %f'
              % (
              self.params['cam1_X'], self.params['cam1_Y'], self.params['cam1_X_width'], self.params['cam1_Y_width']))

    def _alignTrap(self):
        print('right in : align trap')
        n_pts = self.params['nSLMTraps']
        ta = TrapAligner(self.cxn, self.params, tweezerPDmWToRFSoC, tweezerPDmWToV_slm)
        ta.set_slm_traps()
        ta.set_aod_traps()
        print('before try: align trap')
        try:
            ta.acquire_affine(thresh=-3)
            print('acquire affine')
            # pos = np.load('I:/thompsonlab/AMO/Daily/2309/230926/array_position.npz')
            # pts_slm_exp = np.concatenate((pos['x_arr'].reshape([-1,1]),pos['y_arr'].reshape([-1,1])), axis=1)
            pts_slm_exp = np.load('I:/thompsonlab/AMO/Daily/2310/231024/ac_slm_pos.npz')['pos']
            # print('debug260')
            aod_freqs = ta.get_aod_freqs(
                pts_slm_exp=pts_slm_exp)  # None means the 11 by 11 one, same to the one used in alignment
            values = []
            fields = []
            for i in range(n_pts):
                values.append(aod_freqs[i, 0])
                values.append(aod_freqs[i, 1])

                xname = "x_" + str(i).zfill(3) + '_MHz'
                yname = "y_" + str(i).zfill(3) + '_MHz'
                fields.append(xname)
                fields.append(yname)
            print('before push to database')
            assert (np.abs(aod_freqs[0, 0] - aod_freqs[75, 0]) < 0.07)
            assert (np.abs(aod_freqs[87, 1] - aod_freqs[77, 1]) < 0.07)
            self.cxn.SQLserver.log("tweezer_positions_calibration_5x422", values, fields, True)
        except:
            aod_freqs = np.zeros([n_pts, 2])
            query_fields = ""
            for i in range(n_pts):
                xname = "x_" + str(i).zfill(3) + '_MHz'
                yname = "y_" + str(i).zfill(3) + '_MHz'
                if i == 0:
                    query_fields += xname + ","
                    query_fields += yname
                else:
                    query_fields += "," + xname + ","
                    query_fields += yname
            # print(query_fields)
            ans = self.cxn.sqlserver.query(
                "select " + query_fields + " from tweezer_positions_calibration_5x422 order by time desc limit 1")[0]

            for i in range(n_pts):
                aod_freqs[i, 0] = ans[2 * i]
                aod_freqs[i, 1] = ans[2 * i + 1]
            print('Auto aligner failed! used the latest stored value!!')

        # import matplotlib.pyplot as plt
        # plt.plot(aod_freqs[:, 0], aod_freqs[:, 1], marker='o')
        # plt.show()

        print('****\nReplace me by updating self.params! Here we show the 1st AOD trap (col, row)')
        ta.reset_aod_dc()
        affine_chroma = np.load('I:/thompsonlab/AMO/Control programs/main_control_program_lite/calibrations/'
                                'monitor2pvcam_affine_532.npz')['affine']
        in_arr = np.append(aod_freqs, np.ones((aod_freqs.shape[0], 1)), axis=1)
        aod_recal = np.matmul(affine_chroma, in_arr.T).T
        self.params['freqArrXY_MHz'] = np.array(aod_recal)
        # self.params['rowFreq0Arr_MHz'] = aod_freqs[self.params['rowSelected'], 1]
        # self.params['colFreq0Arr_MHz'] = aod_freqs[self.params['rowSelected'], 0]

        print('Warning! I overwrite the AOD frequencies!')
        print('****')

    def _initAOD(self, verbose=False):
        #self.cxn.pvcamNuvuRfsocServer.initAOD()
        self.cxn.pvcamNuvuRfsocServer.init_tweezer_ctrl(self.params['max_rfsoc_moves'], self.params['max_nrow'], self.params['max_ncol'])
        if verbose:
            print("AOD warmed up!")

    def _initCamera(self, verbose=False):

        self.cxn.pvcamNuvuRfsocServer.initPvCam(self.params['pvCamROI'],
                                                   T.Value(self.params['exposureTimePerFrame'], 's'))
        if verbose:
            print("PvCamera configured!")
        if self.params['saveImages_nuvu']:
            # print('nuvu roi: ', self.params['nuvuROI'])
            self.cxn.pvcamNuvuRfsocServer.initNuvuCam(self.params['nuvuROI'][:2],  # [centerXlist, centerYlist]
                                                      self.params['nuvuROI'][2:],  # [wX, wY]
                                                      T.Value(self.params['nuvuExposureTime'], 's'),
                                                      self.params['nuvuEmGain'],
                                                      self.params['nuvuBinning'],
                                                      T.Value(self.params['nuvuWaitingTime'], 's'))
            if verbose:
                print("NuvuCamera configured!")
        self.cxn.pvcamNuvuRfsocServer.clearSequence()

    def _setSLM(self, verbose=False):

        fileDir = self.params['SLMTrapPhaseFile']
        dat = np.load(fileDir)
        phase_grid = dat['phase_grid']
        self.cxn.tweezerslm.updatephasemaskdeformzernike(phase_grid, 0.,
                                                         self.params['ZernikeCN2L0'], 0., 0., 0., 0.)
        if verbose:
            print("SLM phase pattern set!")

    def _recordWavelength(self):
        self.params['399'] = self.cxn.ws7withswitch_server.getwavelength(4)
        self.params['862'] = self.cxn.ws7withswitch_server.getwavelength(8)

    def _waitPvcam(self, verbose=False):
        imageStatus = self.cxn.pvcamNuvuRfsocServer.isSequenceFinished()
        imageWaitIndex = 0
        while (imageStatus == 0 or imageWaitIndex > 60):
            time.sleep(1)
            imageStatus = self.cxn.pvcamNuvuRfsocServer.isSequenceFinished()
            imageWaitIndex += 1
            print('wait {:.1f}s for image to finish'.format(imageWaitIndex))
        if imageStatus == False:
            raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server')
        if verbose:
            print("pvcamNuvuRfsocServer initiated and ready to rock!")




    def _servo369(self):
        if not self.params['isServo369']:
            return 0
        # params['ionizePiezoVoltage_V'] = cxn.toptica369_ws7_server.getPiezoVoltage()  # 11ms
        # params['ionizeLaserCurrent_V'] = cxn.toptica369_ws7_server.getLaserCurrent()  # 11ms
        self.cxn.toptica369_ws7_server.stopMoveFrequency()
        self.cxn.toptica369_ws7_server.setTargetFrequency(labrad.types.Value(self.params['369Freq_THz'], 'THz'))
        self.cxn.toptica369_ws7_server.startMoveFrequency()
        while np.abs(self.cxn.toptica369_ws7_server.getFrequency() - self.params['369Freq_THz']) > 0.00002:
            time.sleep(0.25)

    def _initCountersAndConstants(self, verbose=False):

        self.params['nImagesNuvu'] = 0
        self.params['fIdx'] = getFileUID.GetFileUID().fIdx()
        if verbose:
            print("Counters and constants are initialized!")

    def _resetNICard(self):
        self.cxn.finitedopulses.cleanupTask()
        self.cxn.aoserver.cleanupTask()

    def _setPushBeam(self):
        # Push beam
        freq556PushBeam_MHz = self.params['pushBeamDetuning_MHz'] + self.params['556ResonanceFreq_MHz']
        self.cxn.mogQUADServer_2.setRF(4, T.Value(freq556PushBeam_MHz, 'MHz'),
                                       T.Value(0., 'dBm'))
        self.cxn.mogQUADServer_2.output(4, 1, 'ALL')

    def _setMOTBeam(self):
        # Set MOT beam frequency
        freq556MOTLoad_MHz = self.params['MOTLoadDetuning_MHz'] + self.params['556ResonanceFreq_MHz']
        freq556MOTCompress_MHz = self.params['MOTCompressDetuning_MHz'] + self.params['556ResonanceFreq_MHz']

        # set MOT beam EO
        self.cxn.rigoldg400server.highzmode(1, 0)
        ch = 1
        freq = 139. * 1e3
        self.cxn.rigoldg400server.setfreq(ch, freq, self.params['MOTEOMAmplitude_V'])

        self.cxn.aomserver.setrf(0, 1, labrad.types.Value(freq556MOTLoad_MHz, 'MHz'), 0.15, 0.0)

        self.cxn.aomserver.setsweep(0, 1, T.Value(freq556MOTLoad_MHz, 'MHz'),
                                    T.Value(freq556MOTCompress_MHz, 'MHz'), self.params['MOTAmplitude'],
                                    T.Value(self.params['MOTCompressTime'], 's'), 0)

        self.cxn.finitedopulses.AlwaysOff(motProfile)
        self.cxn.finitedopulses.AlwaysOff(motAOM)
        self.cxn.finitedopulses.AlwaysOn(motEOM)

    def _setImagingBeam(self, verbose=True):
        # Set Imaging beam frequency
        if verbose:
            print('Setting imaging beam')
        self.cxn.rigoldg400server.setFMExt(2, self.params['fmdev'] * 1e6)
        self.cxn.rigoldg400server.setFreq(2, (
                self.params['centerFreq'] - self.params['fmdev'] / self.params['fmDenom']) * 1e6, 1.65)

        self.cxn.aoserver.blankwaveform(self.params['seqLen'])
        aoRate = self.cxn.aoserver.getSampleRate()
        self.cxn.finitedopulses.blankwaveform(self.params['seqLen'], aoRate)

        self.cxn.finitedopulses.AlwaysOff(shutterIon)
        self.cxn.finitedopulses.AlwaysOff(imagingBeam)
        self.cxn.finitedopulses.AlwaysOff(rigolTrigger2)

    def _setUVLED(self, ):
        if self.params['isUVLED']:
            self.cxn.finitedopulses.AlwaysOn(uvLED)
        else:
            self.cxn.finitedopulses.AlwaysOff(uvLED)

    def _setNICard(self, verbose=True):
        t0 = time.time()
        self.cxn.finitedopulses.AlwaysOff(shutter649TTL)

        self.cxn.finitedopulses.AlwaysOff(motBeamShutter)

        self.cxn.finitedopulses.AlwaysOn(tweezerIntegratorHold)

        self.cxn.finitedopulses.AlwaysOn(tweezerAODIntegratorHold)

        self.cxn.aoserver.setConstantVoltage(tweezerMixer,
                                             T.Value(tweezerPDmWToV_slm(self.params['tweezerPowerLoad_mW']), 'V'))

        self.cxn.aoserver.setConstantVoltage(AODAmpMod,
                                             T.Value(tweezerPDmWToRFSoC(0), 'V'))

        self.cxn.aoserver.setConstantVoltage(vca1539, T.Value(5.0, 'V'))

        self.cxn.aoserver.setConstantVoltage(uvAmpSet, T.Value(self.params['UVAmp_V'], 'V'))
        dt = time.time() - t0
        if verbose:
            print('Setting NI Card takes {:.3f} s'.format(dt))

    def _setMOTElectrodes(self, verbose=False):

        if verbose:
            print("Setting MOT electrodes")

        # # Set Electrode Voltages
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S']
        zElectrodes = ['A', 'B', 'C', 'D', 'J', 'K', 'L', 'M']
        mzElectrodes = list(set(letters) - set(zElectrodes))
        yElectrodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        myElectrodes = list(set(letters) - set(yElectrodes))
        xElectrodes = ['A', 'B', 'E', 'F', 'J', 'K', 'N', 'P']
        mxElectrodes = list(set(letters) - set(xElectrodes))
        dacVoltages = dict(zip(letters, [0.0] * 16))

        for k in zElectrodes:
            dacVoltages[k] += self.params['zVoltage_V'] / 2.0
        for k in mzElectrodes:
            dacVoltages[k] -= self.params['zVoltage_V'] / 2.0
        for k in yElectrodes:
            dacVoltages[k] += self.params['yVoltage_V'] / 2.0
        for k in myElectrodes:
            dacVoltages[k] -= self.params['yVoltage_V'] / 2.0
        for k in xElectrodes:
            dacVoltages[k] += self.params['xVoltage_V'] / 2.0
        for k in mxElectrodes:
            dacVoltages[k] -= self.params['xVoltage_V'] / 2.0

        # set E fields
        for k in letters:
            self.cxn.motelectrodeserver.setVoltage(labrad.types.Value(dacVoltages[k], 'V'), k)

        if verbose:
            print("MOT electrodes Set!")

    def _set649And770(self):
        # 649 AOM
        self.cxn.mogQUADServer_649.setRF(3, T.Value(self.params['649AOMFreq_MHz'], 'MHz'),
                                         T.Value(self.params['649AOMPower_dBm'], 'dBm'))
        self.cxn.mogQUADServer_649.output(3, 1, 'ALL')
        # 649 EOM
        self.cxn._649RFServer.setfrequencystepwise_ghz(self.params['649SidebandFreq_MHz'] * 1e-3)
        self.cxn._649RFServer.setpower_dbm(self.params['649SidebandPower_dBm'])
        # 770 AOM
        self.cxn.mogQUADServer_649.setRF(1, T.Value(self.params['770AOMFreq_MHz'], 'MHz'),
                                         T.Value(self.params['770AOMPower_dBm'], 'dBm'))
        self.cxn.mogQUADServer_649.output(1, 1, 'ALL')

    def _set399(self, verbose=False):
        if verbose:
            print('Setting 399 imaging AOM RFs')
        self.cxn.mogQUADServer_3.setRF(2, T.Value(163, 'MHz'),
                                       T.Value(self.params['399ImagingPower_dBm'], 'dBm'))
        self.cxn.mogQUADServer_3.setRF(1, T.Value(110, 'MHz'),
                                       T.Value(self.params['399ImagingPowerTTL2_dBm'], 'dBm'))
        self.cxn.mogQUADServer_3.setRF(3, T.Value(110, 'MHz'),
                                       T.Value(self.params['399ImagingPowerTTL1_dBm'], 'dBm'))
        self.cxn.mogQUADServer_3.output(1, 1, 'ALL')
        self.cxn.mogQUADServer_3.output(2, 1, 'ALL')
        self.cxn.mogQUADServer_3.output(3, 1, 'ALL')

    def _servo770(self):
        if not self.params['isServo770']:
            return 0
        self.cxn.mogQUADServer_649.setRF(1, T.Value(self.params['770AOMFreq_MHz'], 'MHz'),
                                         T.Value(self.params['770AOMPower_dBm'], 'dBm'))
        self.cxn.mogQUADServer_649.output(1, 1, 'ALL')
        self.cxn._770RFServer.setfrequencystepwise_ghz(self.params['770SidebandFreq_MHz'] * 1e-3, 0)
        self.cxn.mogQUADServer_649.setRF(4, T.Value(self.params['770PL_MHz'], 'MHz'), T.Value(9.8, 'dBm'))
        self.cxn.mogQUADServer_649.output(4, 1, 'ALL')

    def _servo302(self):
        # print('Start setting UV(604/2) light frequency')
        if not self.params['isServo302']:
            return 0
        curr_freq = self.cxn.orangeeomserver.getFreq()
        print('Current 604 sideband {:.2f}'.format(curr_freq))
        nsteps = int(np.abs(self.params['604SidebandFreq_MHz'] - curr_freq) / (0.002 * 32))
        freq_lst = np.linspace(curr_freq, self.params['604SidebandFreq_MHz'], nsteps)
        for freq in freq_lst:
            self.cxn.aomserver.setrf(0, 3, labrad.types.Value(freq, 'MHz') / 32.0, 0.15, 0.0, wait=True)
            print("Setting 604(302) nm EOM sideband to ", freq)
            time.sleep(0.01)

        self.cxn.orangeeomserver.storeFreq(self.params['604SidebandFreq_MHz'])

    def _initAWGDispatcher(self):
        # to do change to multiple_replay
        self.ad = ad.AWGDispatcher(self.params['spectrumAWGSampleRate_MHz'], multiple_replay=False)
        self.ad.reset()

    def _makeSaveDir(self):

        if not os.path.exists(self.prefix + '\\pvcam'):
            os.makedirs(self.prefix + '\\pvcam')
        if not os.path.exists(self.prefix + '\\nuvu'):
            os.makedirs(self.prefix + '\\nuvu')

    def _run_after(self):
        """ Stuff that runs after dophases, ie, setting up cameras
            config AWG
        """
        self._runAODProgram()
        self._programSpecAWG()
        self._setNICardFinalStates()
        self._setUpCameras()

    def _runAODProgram(self):
        #moveData = self.cxn.pvcamNuvuRfsocServer.compileMoves()
        #self.cxn.rfsoc_tw_server.start_socket_server(moveData)
        state_data = self.cxn.pvcamNuvuRfsocServer.compileMoves()
        self.cxn.rfsoc_tw_server.start_socket_server(self.params['max_rfsoc_moves'])
        self.cxn.pvcamNuvuRfsocServer.uploadBuffer()  # open a client socket and update all buffers to DDS
        print('RFSoC is stuck!')

        if self.params['rfsocMode'] == 'sequence':
            _ = self.cxn.rfsoc_tw_server.run_exp(state_data)
            # print('current counter', self.cxn.rfsoc_tw_server.get_ctr())
        elif self.params['rfsocMode'] == 'auto':
            _ = self.cxn.rfsoc_tw_server.run_exp_internal(state_data)
        print('Just kidding!')

    def _programSpecAWG(self):
        print('Programming Spec AWG')
        for dat in self.params['UVParamsAWG']:
            self.ad.append(dat['tstart'], dat['length'], dat)  # here tstart and length in us
        if len(self.params['UVParamsAWG']) > 0:
            # tcurr = time.time()
            self.ad.analyze()
            # print("self.ad.analyze()  took {:.3f} s".format(time.time()-tcurr))

            # tcurr = time.time()
            self.ad.config_awg(self.cxn)
            # print("self.ad.config_awg(self.cxn) took {:.3f} s".format(time.time()-tcurr))

            # tcurr = time.time()
            self.cxn.awgServerUV.playWaveform(self.ad.idx)
            # print("self.cxn.awgServerUV.playWaveform(self.ad.idx) took {:.3f} s".format(time.time()-tcurr))
        print('Finish programming Spec AWG')

    def _setNICardFinalStates(self):
        self.cxn.finitedopulses.SetFinalState(uvLED, 1)
        self.cxn.finitedopulses.SetFinalState(motAOM, 1)
        self.cxn.finitedopulses.SetFinalState(motEOM, 1)
        self.cxn.finitedopulses.SetFinalState(motEOM, 1)
        self.cxn.finitedopulses.SetFinalState(pbAOM, 1)
        self.cxn.finitedopulses.SetFinalState(tweezerAODIntegratorHold, 1)
        self.cxn.finitedopulses.SetFinalState(tweezerIntegratorHold, 1)
        self.cxn.finitedopulses.SetFinalState(rigolTrigger2, 0)
        self.cxn.finitedopulses.SetFinalState(motProfile, 0)
        self.cxn.finitedopulses.SetFinalState(imagingBeam, 0)
        self.cxn.finitedopulses.SetFinalState(tweezerAOM, 0)
        self.cxn.finitedopulses.SetFinalState(tweezerAOMAOD, 0)
        self.cxn.aoserver.setFinalState(motMixer, T.Value(MOTPDmWToV(self.params['MOTLoadPower_mW']), 'V'))

    def _setUpCameras(self,verbose=False):
        self.cxn.pvcamNuvuRfsocServer.acquireFastSequence(
            self.prefix,
            getSaveName(self.params, self.params['saveParams']),
            self.params['nLoops'])

        acquistionStatus = self.cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
        acquistionWaitIndex = 0
        while (acquistionStatus == False or acquistionWaitIndex > 60):
            time.sleep(1)
            acquistionStatus = self.cxn.pvcamNuvuRfsocServer.isAcquisitionReady()
            acquistionWaitIndex += 1
            print('wait {:.1f}s for acquistiion to get ready'.format(acquistionWaitIndex))
        if acquistionStatus == False:
            raise Warning('pvcamNuvuRfsocServer might have stuck. Check the server (acquisition)')
        if verbose:
            print("pvcamNuvuRfsocServer initiated and ready to rock!")


    def _run_wait(self):
        """ Actually start the sequence, and wait for it to finish """
        print('run waveforms, number of loops:', self.params['nLoops'])
        self.cxn.aoserver.runwaveform(self.params['nLoops'])
        self.cxn.finitedopulses.runwaveform(self.params['nLoops'])

        self._loopWhileRunWaveform()

    def _loopWhileRunWaveform(self):
        scanTime = self.params['seqLen'] * self.params['nLoops']

        time_start = time.time()
        nPerLoop = self.cxn.finitedopulses.nPoints()
        nTotal = nPerLoop * self.params['nLoops']

        runCounter = -1
        while (time.time() - time_start) < (scanTime + 0.1):
            ns = int(self.cxn.finitedopulses.getNumSampsWritten())
            runNumber = ns / nPerLoop
            if runNumber > runCounter and ns != nTotal:
                runCounter = runNumber
                print(ns, ns / nPerLoop)

    def _run_cleanup(self):

        """ Handle any image saving, etc. """

        pass

    def _run_analysis(self):
        """ If there is any automatic analysis to do, do it here """
        pass

    def run(self, cxn, params, prefix, keys={}):
        """ Run the experiment. Keys is a dictionary of the variables/values associated with the scan,
        which should be used to generate filenames but also to save any automatic analysis results. """

        self.params = params
        self.cxn = cxn
        self.prefix = prefix  # directory to save results

        # self.reset()

        self._initialize()
        # flatten phases and generate sorted list
        # self.plot_phase_graph()

        self._run_before()

        self._run_after()

        self._run_wait()

        self._run_cleanup()

        val = self._run_analysis()

        # add result to our dictionary. Note that in python > 3.7, dict objects
        # remember the order in which keys were added, so we do it this way to ensure that
        # the first key is the primary variable being iterated over, the next keys are the secondary iterators,
        # and 'value' is the data point.
        new_result = {}
        new_result.update(keys)
        new_result['value'] = val
        self.results.append(new_result)

        self._reset()

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

    prev_phase = (None,)

    for p in in_phases:
        if isinstance(p, phase):

            phases.append(p)

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

            prev_phase = p[2]

    # returns phases, first, last
    first = phases[0] if isinstance(phases[0], Iterable) else (phases[0],)
    return phases, first, prev_phase


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

    for p in in_phases:

        if isinstance(p, phase):

            phases.append(p)
            firsts.append(p)
            lasts.append(p)

        elif type(p) == tuple:

            phases.append(p[0])
            firsts.extend(p[1])
            lasts.extend(p[2])

    return phases, tuple(firsts), tuple(lasts)


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
