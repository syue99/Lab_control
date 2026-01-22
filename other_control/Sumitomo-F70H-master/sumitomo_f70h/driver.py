# Copyright (C) 2016, see AUTHORS.md
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sumitomo_f70h.protocol import SumitomoF70HProtocol
from sumitomo_f70h.message import AsciiMessage, AsciiCommand, AsciiResponse

class SumitomoF70HDriver(object):

    def __init__(self, protocol):
        assert isinstance(protocol, SumitomoF70HProtocol)

        self._protocol = protocol

    def _execute(self, cmd):
        return self._protocol.execute(AsciiMessage(cmd))

    def clear(self):
        self._protocol.clear()

    def get_all_temperatures(self):
        response = self._execute(AsciiCommand('TEA'))
        return map(float, response.get_data())

    def get_temperature(self, id):
        if not id in range(1, 5):
            raise ValueError("Unknown id")

        response = self._execute(AsciiCommand('TE' + str(id)))
        return float(response.get_data())

    def get_all_pressures(self):
        response = self._execute(AsciiCommand('PRA'))
        return map(float, response.get_data())

    def get_pressure(self, id):
        if not id in range(1, 3):
            raise ValueError("Unknown id")

        response = self._execute(AsciiCommand('PR' + str(id)))
        return float(response.get_data())

    def turn_on(self):
        self._execute(AsciiCommand('ON1'))

    def turn_off(self):
        self._execute(AsciiCommand('OFF'))

    def reset(self):
        self._execute(AsciiCommand('RS1'))

    def cold_head_run(self):
        self._execute(AsciiCommand('CHR'))

    def cold_head_pause(self):
        self._execute(AsciiCommand('CHP'))

    def cold_head_pause_off(self):
        self._execute(AsciiCommand('POF'))

    def get_status(self):
        response = self._execute(AsciiCommand('STA'))
        return int(response.get_data(), 16)

    def get_on(self):
        status = self.get_status()
        # local on and system on.
        return status & 0x1 and (status >> 9) & 0x1

    def get_identifier(self):
        response = self._execute(AsciiCommand('ID1'))
        return str(response.get_data()[0])

    def get_operating_hours(self):
        response = self._execute(AsciiCommand('ID1'))
        return float(response.get_data()[1])
