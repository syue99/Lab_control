import time
import os
import labrad
import sys
sys.path.append('../servers/script_scanner/')
sys.path.append('../servers/script_scanner/utility/')
from experiment import experiment
from utility import utility as _utility
import numpy as _n
import labrad.types as _T


class IonExperiment(experiment):
    """Base class for strontium and radium experiments.

    Adapted from Anthony Ransford's QsimExperiment and Xueping Long's MoleculeExperiment
    """

    exp_parameters = []

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def __init__(self, name=None, required_parameters=None, cxn=None,
                 min_progress=0.0, max_progress=100.0):
        required_parameters = self.all_required_parameters()
        experiment.__init__(self, name, required_parameters, cxn, min_progress, max_progress)

        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name

        self.p = self.parameters

    def initialize(self, cxn, context, ident):
        """Gets initial pulser and pmt parameters.

        self.has_ion_experiment_initialize_run checks whether initialize has run.
        If it has run, it will not run again.
        It prevents running the function multiple times with multiple inherited child classes.
        """
        self._get_pulser_attributes()
        try:
            self.has_ion_experiment_initialize_run
        except Exception as e:
            self.has_ion_experiment_initialize_run = False

        if not self.has_ion_experiment_initialize_run:
            self.has_ion_experiment_initialize_run = True
            self.ident = ident
            experiment.initialize(self, cxn, context, ident)
            self._check_pmt_mode()
            self._clear_pulser_sequence()

    def finalize(self, cxn, context):
        self.set_initial_parameters()

    def set_initial_parameters(self):
        """Sets PMT and pulser to its initial mode.

        This function makes sure that the pulse sequence is stopped
        and PMT is set to the original mode.
        It should always be called when the experiment finishes or aborts.

        This function should be overrided if an experiment needs to do other work at the end
        of a pulse sequence, e.g. set PMT duration to its initial value.

        self.has_ion_experiment_set_initial_parameters_run checks whether
        self.set_initial_parameters has run. If it has run, it will not run again.
        It prevents running the function multiple times with multiple inherited child classes.
        """
        try:
            self.has_ion_experiment_set_initial_parameters_run
        except Exception as e:
            self.has_ion_experiment_set_initial_parameters_run = False

        if not self.has_ion_experiment_set_initial_parameters_run:
            self.has_ion_experiment_set_initial_parameters_run = True
            self.pulser.stop_sequence()
            self.pulser.line_trigger_state(False)
            if self.pmt_initial_mode:
                self.pmt.set_mode(self.pmt_initial_mode)

    def _clear_pulser_sequence(self):
        self.pulser.stop_sequence()
        self.pulser.reset_timetags()
        self.pulser.reset_readout_counts()

    def _check_pmt_mode(self):
        try:
            self.pmt = self.cxn.normalpmtflow
        except Exception as e:
            self.pmt = None
            print("NormalPMTFlow server is not on")

        if self.pmt:
            self.pmt_initial_mode = self.pmt.getcurrentmode()
            self.pmt.set_mode("Normal")
        else:
            self.pmt_initial_mode = None

    def _connect(self):
        experiment._connect(self)
        self._connect_datavault()
        self._connect_pulser()

    def _connect_datavault(self):
        try:
            self.dv = self.cxn.servers['Data Vault']
        except KeyError as error:
            error_message = error + '\n' + "DataVault is not running"
            raise KeyError(error_message)

    def _connect_pulser(self):
        try:
            self.pulser = self.cxn.servers['pulser']
        except KeyError as error:
            error_message = error + '\n' + "Pulser is not running"
            raise KeyError(error_message)

    def _get_pulser_attributes(self):
        try:
            from config.pulser.hardwareConfiguration import hardwareConfiguration as _hc
        except ImportError as e:
            from pydux.lib.config.pulser.hardwareConfiguration import hardwareConfiguration as _hc
        self.pulser_time_resolution = _T.Value(float(_hc.timeResolution), "s")
        self.pulser_max_switch_num = _hc.maxSwitches
        self.pulser_max_sequence_length = _T.Value(_hc.sequenceTimeRange[1], "s")
        self.pulser_max_timetags = 32767
        self.pulser_max_readouts = 1023
        self.pulse_minimum_start_time = _T.Value(40, "ns")

    def setup_datavault(self, xdata, ydatas):
        """Initializes experiment data file and sets the data file variable information.

        Sets numbers of dependent and independent variables and variables' units.

        Args:
            xdata: list of 2-tuples. example: [('ML_AOM_Frequency', 'MHz')],
                where the first entry in the 2-tuple is the xdata name and second
                the unit of data.
            ydatas: list of 3-tuples. example:
                [('', 'PMT1 MOT', 'Cts/sec'), ('', 'PMT2 Vapor', 'Cts/sec')],
                where the first entry is the label, second the legend and third the
                unit. The label is intended to be an axis label that can be shared among
                plots, while legend is a legend entry that should be unique for
                each plot.
        """
        self.dv = self.cxn.data_vault
        folder_name = self.name
        path = _utility.base_path_list()  # Date information.
        path.append(folder_name)
        self.dv.cd(path, True)

        if type(xdata) != list:
            xdata = [xdata]
        if type(ydatas) != list:
            ydatas = [ydatas]
        self.dataset = self.dv.new(self.name, xdata, ydatas)

        return self.dataset

    def add_datavault_parameters(self):
        self.dv.add_parameter('start_time', time.time())

        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter])

        self.header_name = "measurement"
        self._add_dds_parameters_to_datavault()
        self._add_wavemeter_frequencies_to_datavault()

    def _add_wavemeter_frequencies_to_datavault(self):
        from config.multiplexerclient_config import multiplexer_config
        chaninfo = multiplexer_config.info
        wavemeterIP = multiplexer_config.ip
        password = os.environ['LABRADPASSWORD']
        try:
            cxnwlm = labrad.connect(wavemeterIP,
                                    name=self.name,
                                    password=password)
            self.wm_server = cxnwlm.multiplexerserver
            for chan_name in chaninfo:
                name = "wavemeter_%s" % chan_name.replace(" ", "_")
                chan = chaninfo[chan_name][0]
                freq = _T.Value(self.wm_server.get_frequency(chan), "THz")
                self.dv.add_additional_header(self.header_name, name, freq)
            cxnwlm.disconnect()
        except Exception as e:
            print("Cannot connect to the wavemeter.")

    def _add_dds_parameters_to_datavault(self):
        all_channels = self.pulser.get_dds_channels()
        for chan in all_channels:
            if self.pulser.output(chan):
                freq = self.pulser.frequency(chan)["MHz"]
                power = self.pulser.amplitude(chan)["dBm"]
                self.dv.add_parameter(chan + '_dds', (freq, power))

    def setup_grapher(self, tab):
        self.grapher.plot(self.dataset, tab, False)

    def update_progress(self, progress):
        if progress >= 1.0:
            progress = 1.0
        elif progress <= 0.0:
            progress = 0.0

        should_stop = self.pause_or_stop()
        self.sc.script_set_progress(self.ident, 100*progress)
        return should_stop

    def get_scan_list(self, scan):
        """Returns scanned values for a scan parameter.

        Args:
            scan: 3-tuple (scan_start, scan_end, scan_step).
                scan_start and scan_end can be floats or labrad.types.Value instances.
                The units need to be compatible if they are both labrad.types.Value instances.
                scan_step is an positive integer.
                Parameter vault scan parameter value can be directly used for this argument.

        Returns:
            A list of scanned values.
        """
        if isinstance(scan[0], _T.Value) and isinstance(scan[1], _T.Value):
            if not scan[0].isCompatible(scan[1].units):
                raise ValueError("The units of scan_start and scan_end need to be compatible")
            unit = scan[0].units
            start = scan[0][unit]
            end = scan[1][unit]
        elif isinstance(scan[0], _T.Value) or isinstance(scan[1], _T.Value):
            raise TypeError("Both scan_start and scan_end need to be the same type")
        else:
            start = scan[0]
            end = scan[1]
            unit = None

        num_steps = scan[2]
        scan_list = list(_n.linspace(start, end, num_steps))
        if unit is not None:
            scan_list = [_T.Value(kk, unit) for kk in scan_list]
        return scan_list

    def end_experiment(self, comment=""):
        self.set_initial_parameters()
        if comment != "":
            raise Exception(comment)
        else:
            raise Exception("Unknown exception")

    def program_pulse_sequence(self, pulse_sequence):
        self.pulser.new_sequence()
        ttl_pulses = pulse_sequence.programmable_ttl_pulses()
        dds_pulses = pulse_sequence.programmable_dds_pulses()
        self.pulser.add_dds_pulses(dds_pulses)
        self.pulser.add_ttl_pulses(ttl_pulses)
        self.pulser.program_sequence()

    def check_stop(self):
        if self.pause_or_stop():
            self.end_experiment("Experiment stopped prematurely.")

    def sleep(self, timer):
        """Sleep function that checks whether experiment is stopped during the sleep.

        This is equivalent to time.sleep function with self.check_stop called every 0.5 s
        during the sleep.

        Args:
            timer: Value of s, sleep time.
        """
        try:
            timer = timer["s"]
        except Exception as e:
            print("timer should have a unit in second, but float is also accepted")
        if timer < 1:
            time.sleep(timer)
            self.check_stop()
        else:
            time_start = time.time()
            sleep_step = 0.5
            while time.time() - time_start < timer:
                time.sleep(sleep_step)
                self.check_stop()

    def repeat_run_with_readouts(self, num_of_runs, counts_per_run=1, max_runs_per_readout=-1,
                                 progress_start=0., progress_end=1., stop_checked=True):
        """Repeats the programmed pulse sequence num_of_runs and saves the readout counts.

        The pulser memory limits the number of counts before each readout.

        Args:
            num_of_runs: int, pulse sequence repetitions.
            counts_per_run: int, number of counts per pulse sequence.
            max_runs_per_readout: int, max number of runs per readout. Default to -1, no max limit.
            progress_start: float, 0. to 1., progress bar position when this function starts.
            progress_end: float, 0. to 1., progress bar position when this function ends.
            stop_checked: bool, whether to check experiment stop signal at every readout.

        Returns:
            A list of ints, all readout counts.
        """
        max_runs = int(self.pulser_max_readouts / counts_per_run)
        if max_runs_per_readout != -1 and max_runs > max_runs_per_readout:
            max_runs = max_runs_per_readout

        progress_bar = progress_start
        progress_bar_per_run = (progress_end - progress_start) / num_of_runs
        counts = []
        while num_of_runs > max_runs:
            self.pulser.start_number(max_runs)
            self.pulser.wait_sequence_done()
            self.pulser.stop_sequence()
            counts += [int(kk) for kk in self.pulser.get_readout_counts()]
            if stop_checked:
                self.check_stop()
            num_of_runs -= max_runs
            progress_bar += p1rogress_bar_per_run * max_runs
            self.update_progress(progress_bar)

        self.pulser.start_number(num_of_runs)
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence()
        counts += [int(kk) for kk in self.pulser.get_readout_counts()],print(counts)
        if stop_checked:
            self.check_stop()
        progress_bar += progress_bar_per_run * num_of_runs
        #self.update_progress(progress_bar)
        return counts

    def repeat_run_with_timetags(self, num_of_runs, num_of_runs_per_timetag_read,
                                 progress_start=0., progress_end=1., stop_checked=True):
        """Repeats the programmed pulse sequence num_of_runs and saves the timetags.

        Args:
            num_of_runs: int, pulse sequence repetitions.
            num_of_runs_per_timetag_read: int, number of repetitions per timetags read.
            progress_start: float, 0. to 1., progress bar position when this function starts.
            progress_end: float, 0. to 1., progress bar position when this function ends.
            stop_checked: bool, whether to check experiment stop signal at every readout.

        Returns:
            A list of floats, all timetags.
        """
        progress_bar = progress_start
        progress_bar_per_run = (progress_end - progress_start) / num_of_runs
        timetags = []
        while num_of_runs > num_of_runs_per_timetag_read:
            self.pulser.start_number(num_of_runs_per_timetag_read)
            self.pulser.wait_sequence_done()
            self.pulser.stop_sequence()

            new_timetags = self.pulser.get_timetags()
            if len(new_timetags) == self.pulser_max_timetags:
                self.end_experiment("Max number of timetags recorded. Experiment failed")
            timetags += list(new_timetags)

            if stop_checked:
                self.check_stop()
            num_of_runs -= num_of_runs_per_timetag_read
            progress_bar += progress_bar_per_run * num_of_runs_per_timetag_read
            self.update_progress(progress_bar)

        self.pulser.start_number(num_of_runs)
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence()

        new_timetags = self.pulser.get_timetags()
        if len(new_timetags) == self.pulser_max_timetags:
            self.end_experiment("Max number of timetags recorded. Experiment failed")
        timetags += list(new_timetags)

        if stop_checked:
            self.check_stop()
        progress_bar += progress_bar_per_run * num_of_runs
        self.update_progress(progress_bar)
        return timetags

    def group_counts(self, counts_list, counts_per_datapoint, independent_list=None):
        """Groups PMT counts in data points.

        Examples:
            >>> group_counts([1, 2, 3, 4, 5, 6], 2)
            [[1, 2], [3, 4], [5, 6]]
            >>> group_counts([1, 2, 3, 4, 5, 6], 2, [7, 8, 9])
            [[7, 1, 2], [8, 3, 4], [9, 5, 6]]
            >>> group_counts([1, 2, 3, 4, 5, 6], 2, 7)
            [[7, 1, 2], [7, 3, 4], [7, 5, 6]]

        Args:
            counts_list: list, 1d list of PMT counts.
            counts_per_datapoint: int, number of counts per data point.
            independent_list: (optional) float, list or None, inserted to the first elements
                of every data point. If it is a list, the elements in the list are inserted
                in the beginning of each data point sequentially. It it is a float, it is
                inserted to the beginning of each data point.

        Returns:
            A 2d np.array of grouped counts with optional independent variables.
        """
        datapoints = int(len(counts_list) / counts_per_datapoint)
        grouped_counts = _n.array(counts_list).reshape((datapoints, counts_per_datapoint))
        if independent_list is None:
            return grouped_counts
        else:
            grouped_counts = _n.array(grouped_counts, dtype=float)
            return _n.insert(grouped_counts, 0, independent_list, 1)

    def set_line_trigger_state(self, state):
        """Sets the pulser line triggering state.

        The pulse sequences are synchronous with the pulser TTL input if line triggering is True.
        Usually used with an ac power triggered TTL signal to reduce impact of the 60 Hz magnetic
        field noise.

        The line triggering state is always set to False at the end of a pulse sequence.

        Args:
            state: bool, line triggering state.
        """
        self.pulser.line_trigger_state(state)
