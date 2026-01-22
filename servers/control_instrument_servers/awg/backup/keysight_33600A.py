import numpy as np
import pyvisa as visa
from labrad.server import LabradServer, setting
import time


class keysight_33600A(LabradServer):
    name = "keysight_33600A"

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

    # @setting(2, "generatePulse", ch=1, width_s=50e-9, period_s=1e-6, vpp=1.0, offset=0.0, rise_s=5e-9, fall_s=5e-9, burst_cycles=1, trigger_source="EXT", output_load="INF")
    def __generatePulse(self, c, ch, width_s, period_s, vpp, offset, rise_s, fall_s, burst_cycles, trigger_source, output_load):
        self._writeCommands(f":OUTP{ch}:STAT OFF") # Turn off output before configuring

        self._writeCommands(f":OUTP{ch}:LOAD {output_load}") # Set output load
        self._writeCommands(f"SOUR{ch}:FUNC PULSE") # Set waveform to pulse
        self._writeCommands(f":SOUR{ch}:PULS:WIDT {width_s}") # Set pulse width
        self._writeCommands(f":SOUR{ch}:PULS:PERI {period_s}") # Set pulse period
        self._writeCommands(f":SOUR{ch}:PULS:RISE {rise_s}") # Set rise time
        self._writeCommands(f":SOUR{ch}:PULS:FALL {fall_s}") # Set fall time
        self._writeCommands(f":SOUR{ch}:VOLT {vpp}") # Set voltage amplitude
        self._writeCommands(f":SOUR{ch}:VOLT:UNIT VPP") # Set voltage unit to Vpp
        self._writeCommands(f":SOUR{ch}:VOLT:OFFS {offset}") # Set voltage offset

        # one shot per trigger
        self._writeCommands(f":SOUR{ch}:BURS:STAT ON") # Enable burst mode
        self._writeCommands(f":SOUR{ch}:BURS:MODE TRIG") # Set burst mode to triggered
        self._writeCommands(f":SOUR{ch}:BURS:NCYC {burst_cycles}") # Set number of burst cycles
        self._writeCommands(f":TRIG{ch}:SOUR {trigger_source}") # Set trigger source

        self._writeCommands(f":OUTP{ch}:STAT ON") # Turn on output


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


if __name__ == "__main__":
    from labrad import util
    import ctypes

    ctypes.windll.kernel32.SetConsoleTitleA("keysight_33600A")
    util.runServer(keysight_33600A())
