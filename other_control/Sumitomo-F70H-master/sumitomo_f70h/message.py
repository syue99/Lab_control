# Copyright (C) 2019, see AUTHORS.md
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

class AbstractMessage(object):
    DELIMITER = chr(0x2C)  # ,
    START = chr(0x24)  # $
    END = chr(0x0d)  # \r

    @staticmethod
    def compute_checksum(data):
        crcmask = 0xA001
        i = 0
        l = 0
        crc = 0xFFFF
        while l < len(data):
            crc = (0x0000 | (data[l] & 0xFF)) ^ crc
            while (i < 8):
                lsb = crc & 0x1
                crc = crc >> 1
                if lsb == 1:
                    crc = crc ^ crcmask
                i = i + 1
            i = 0
            l = l + 1
        return crc


class AsciiMessage(AbstractMessage):
    def __init__(self, command):
        assert isinstance(command, AsciiCommand)
        self._cmd = command

    def get_raw(self):
        ascii_msg = self.START + self._cmd.get_message()
        raw = map(ord, ascii_msg)
        # This returns the checksum as an integer
        checksum = self.compute_checksum(list(raw))
        # Interpret the checksum as hex, but strip the first two chars (0x1234 -> 1234)
        ascii_checksum = hex(checksum)[2:]
        return (ascii_msg + ascii_checksum + self.END).encode('ascii').upper()


class AsciiCommand(AbstractMessage):
    def __init__(self, command, data=''):
        assert len(command) == 3

        self._cmd = command
        self._data = data

    def get_message(self):
        if len(self._data) > 0:
            return self._cmd + self._data
        else:
            return self._cmd


class AsciiResponse(AbstractMessage):

    def __init__(self, command, data_region, checksum):
        self._cmd = command
        self._data = data_region

        # TODO: check checksum ;)
        self._checksum = checksum

    def get_data(self):
        if len(self._data) == 0:
            return None

        data = self._data.split(self.DELIMITER)

        if len(data) == 1:
            return data[0]

        return data

    def get_cmd(self):
        return self._cmd

    @classmethod
    def from_raw(cls, raw):
        # convert the bytearray to a "string" array ;)
        ascii = list(map(chr, raw))

        # Do not need: start, end: intermediate delimiter (command -> data_region, data_region -> end)
        # start = ascii[0]
        command = "".join(ascii[1:4])
        # raw[4] and raw[-3] are just delimiter
        data_region = "".join(ascii[5:-6])
        # end = ascii[-1]
        checksum = "".join(ascii[-5:-1])

        return cls(command, data_region, checksum)
