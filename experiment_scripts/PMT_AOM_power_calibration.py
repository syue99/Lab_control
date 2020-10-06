"""
### BEGIN EXPERIMENT INFO
[info]
name = PMTAOMPowerCalibration
load_into_scriptscanner = False
allow_concurrent = []
### END EXPERIMENT INFO
"""

import labrad
from labrad.units import WithUnit
from ion_experiment import IonExperiment
import time
import numpy as np


class PMTAOMPowerCalibration(IonExperiment):
    """Calibrates the AOM rf power using a PMT."""

    name = "PMT AOM Power Calibration"

    exp_parameters = []
    exp_parameters.append(('PMT_AOM_power_calibration', 'aom_ch'))
    exp_parameters.append(('PMT_AOM_power_calibration', 'aom_calibrate_freqs'))
    exp_parameters.append(('PMT_AOM_power_calibration', 'aom_power_max'))
    exp_parameters.append(('PMT_AOM_power_calibration', 'aom_power_min'))
    exp_parameters.append(
        ('PMT_AOM_power_calibration', 'aom_power_coarse_step'))
    exp_parameters.append(('PMT_AOM_power_calibration', 'target_precision'))
    exp_parameters.append(('PMT_AOM_power_calibration', 'wait_time'))
    exp_parameters.append(('PMT_AOM_power_calibration',
                           'target_kilocounts_per_second'))
    exp_parameters.append(('PMT_AOM_power_calibration', 'collect_time'))

    def initialize(self, cxn, context, ident):
        IonExperiment.initialize(self, cxn, context, ident)
        self.sigmas = 5

        try:
            self.pmt = self.cxn.normalpmtflow
            if self.pmt.isrunning():
                self.pmt.stoprecording()
        except Exception as e:
            print(e)

    def run(self, cxn, context):
        self.setup_parameters()

        self.save_initial_parameters()
        self.pulser.set_collection_time(self.collect_time, "Normal")
        self.target_counts = self.collect_time / \
            WithUnit(1, "s") * self.target_counts_per_second

        aom_freqs = np.linspace(self.aom_calibrate_freq_range[0],
                                self.aom_calibrate_freq_range[1],
                                num=self.aom_calibrate_freq_steps)

        to_datavault = []

        self.total_measurements = self.aom_calibrate_freq_steps
        self.measurement_counter = 0

        for aom_freq in aom_freqs:
            self.pulser.frequency(self.aom_ch, WithUnit(aom_freq, "MHz"))
            amp = self.find_aom_power()
            to_datavault.append([aom_freq, amp])

            self.update_experiment_progress()

        self.setup_datavault([('AOM Frequency', 'MHz')],
                             [('', 'AOM Power', 'dBm')])
        self.add_datavault_parameters()
        self.dv.add(to_datavault)
        self.update_progress(1.0)

    def aom_power_fine_tune(self, fine_tune_range, counts, iteration=1):
        """Tests the counts at the rf power of the mid point of fine_tune_range.

        It is called recursively to find the rf power producing counts
        closest to the target counts.

        Args:
            fine_tune_range: tuple (v["dBm"], v["dBm"]), The range of fine tune.
            counts: tuple (float, float), Counts at the lower and upper bound
                of the range.
            iterations: int, How many times has aom_power_fine_tune iterated

        Returns:
            The AOM rf power outputing closest counts to target_counts.
        """

        lower_bound = fine_tune_range[0]
        upper_bound = fine_tune_range[1]

        mid_amp = (lower_bound + upper_bound) / 2
        lower_bound_counts = counts[0]
        upper_bound_counts = counts[1]

        self.pulser.amplitude(self.aom_ch, mid_amp)
        time.sleep(self.wait_time["s"])

        if_good, counts = self.get_counts()
        if if_good:
            return mid_amp["dBm"]
        else:
            new_iteration = iteration + 1
            if iteration >= 12:
                raise Exception("AOM fine tune failed")
            elif self.check_fine_tune(counts, lower_bound_counts):
                return self.aom_power_fine_tune((lower_bound, mid_amp),
                                                (lower_bound_counts, counts),
                                                new_iteration)
            elif self.check_fine_tune(counts, upper_bound_counts):
                return self.aom_power_fine_tune((mid_amp, upper_bound),
                                                (counts, upper_bound_counts),
                                                new_iteration)
            else:
                raise Exception("AOM fine tune failed")

    def check_exceptions(self):
        if self.aom_calibrate_freq_steps < 1:
            self.end_experiment(
                "Scan steps must be larger than 0. Experiment failed.")
        dds_chs = self.pulser.get_dds_channels()
        if self.aom_ch not in dds_chs:
            self.end_experiment(
                ("AOM channel not in available DDS channels. "
                 "Experiment failed."))
        if self.aom_power_max["dBm"] < self.aom_power_min["dBm"]:
            self.end_experiment(
                ("Maximum AOM power must be larger than minimum AOM power. "
                 "Experiment failed."))

    def check_fine_tune(self, counts, last_counts):
        """Returns whether the target counts is between the two input counts."""

        if last_counts == -1:
            return False

        counts_diff = counts - self.target_counts
        last_counts_diff = last_counts - self.target_counts

        return counts_diff * last_counts_diff <= 0

    def find_aom_power(self):
        if_skip_fine_tune, fine_tune_range, fine_tune_counts = self.get_fine_tune_range()
        if not if_skip_fine_tune:
            try:
                amp = self.aom_power_fine_tune(fine_tune_range, fine_tune_counts)
                if_retry = False
            except Exception as e:
                print(("Fine tune failed. "
                       "Try to get a fine tune range and do fine tune again"))
                if_retry = True
        else:
            amp = fine_tune_range["dBm"]

        if if_retry:
            if_skip_fine_tune, fine_tune_range, fine_tune_counts = self.get_fine_tune_range()
            if not if_skip_fine_tune:
                amp = self.aom_power_fine_tune(fine_tune_range, fine_tune_counts)
            else:
                amp = fine_tune_range["dBm"]
        return amp

    def get_fine_tune_range(self):
        """Sweeps AOM rf power in coarse steps.

        Returns:
            The AOM power range with PMT counts close to the target counts.
        """

        fine_tune_range = []
        amp = self.aom_power_min
        last_counts = -1

        while amp <= self.aom_power_max:
            self.pulser.amplitude(self.aom_ch, amp)
            time.sleep(self.wait_time["s"])

            if_skip_fine_tune, counts = self.get_counts()
            if if_skip_fine_tune:
                fine_tune_range = amp
                counts = counts
                break
            if self.check_fine_tune(counts, last_counts):
                fine_tune_range = [last_amp, amp]
                counts = [last_counts, counts]
                break
            else:
                last_amp = amp
                last_counts = counts

            amp += self.aom_power_coarse_step

        if fine_tune_range == []:
            raise Exception(
                "Coarse tuning could not find specified optical power.")

        return if_skip_fine_tune, fine_tune_range, counts

    def get_counts(self):
        """Gets Counts.

        Returns:
            First: bool, If the counts are in the allowed uncertainty
            Second: float, The averaged counts.
        """

        self.pulser.reset_fifo_normal()
        counts = []
        if_good, if_stop = self.counts_check(counts)
        while not if_stop and not if_good:
            self.check_stop()

            time.sleep(self.collect_time["s"])
            for pmt_counts in self.pulser.get_pmt_counts():
                counts.append(pmt_counts[0] * 1000 * self.collect_time["s"])
            if_good, if_stop = self.counts_check(counts)
        return if_good, float(sum(counts)) / len(counts)

    def counts_check(self, counts):
        """Checks counts.

        Returns:
            First: bool, Whether the total possible error is
                inside of the allowed uncertainty.
            Second: bool, Whether the uncertainty is small enough so we know
                measured counts is larger/smaller than the target_counts.
        """

        if len(counts) == 0:
            return False, False
        allowed_uncertainty = self.target_counts * self.target_precision
        total_counts = float(sum(counts))
        uncertainty = np.sqrt(total_counts) / len(counts)
        average = total_counts / len(counts)
        total_possible_error = np.sqrt(
            (uncertainty * self.sigmas)**2 + (average - self.target_counts)**2)

        return allowed_uncertainty > total_possible_error, \
            abs(average - self.target_counts) > uncertainty * self.sigmas

    def set_initial_parameters(self):
        IonExperiment.set_initial_parameters(self)
        if self.init_freq:
            self.pulser.frequency(self.aom_ch, self.init_freq)
        if self.init_amp:
            self.pulser.amplitude(self.aom_ch, self.init_amp)

    def save_initial_parameters(self):
        self.init_freq = self.pulser.frequency(self.aom_ch)
        self.init_amp = self.pulser.amplitude(self.aom_ch)

    def setup_parameters(self):
        self.aom_ch = self.p.PMT_AOM_power_calibration.aom_ch

        self.aom_calibrate_freq_range = (
            self.p.PMT_AOM_power_calibration.aom_calibrate_freqs[0],
            self.p.PMT_AOM_power_calibration.aom_calibrate_freqs[1])
        self.aom_calibrate_freq_steps = int(
            round(self.p.PMT_AOM_power_calibration.aom_calibrate_freqs[2]))

        self.wait_time = WithUnit(
            self.p.PMT_AOM_power_calibration.wait_time, "s")
        self.collect_time = WithUnit(
            self.p.PMT_AOM_power_calibration.collect_time, "s")

        self.aom_power_max = WithUnit(
            self.p.PMT_AOM_power_calibration.aom_power_max, "dBm")
        self.aom_power_min = WithUnit(
            self.p.PMT_AOM_power_calibration.aom_power_min, "dBm")

        self.aom_power_coarse_step = WithUnit(
            self.p.PMT_AOM_power_calibration.aom_power_coarse_step, "dBm")

        self.target_counts_per_second = \
            self.p.PMT_AOM_power_calibration.target_kilocounts_per_second
        self.target_counts_per_second *= 1000
        self.target_precision = \
            self.p.PMT_AOM_power_calibration.target_precision

        self.check_exceptions()

    def update_experiment_progress(self):
        self.measurement_counter += 1
        progress = float(self.measurement_counter) / self.total_measurements
        if progress < 1.0:
            self.update_progress(progress)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = PMTAOMPowerCalibration(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
