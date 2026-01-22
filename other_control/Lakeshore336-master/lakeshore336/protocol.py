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

from e21_util.error import CommunicationError
from e21_util.interface import Loggable
from e21_util.serial_connection import AbstractTransport, SerialTimeoutException

class LakeShore336Protocol(Loggable):
    def __init__(self, transport, logger):
        super(LakeShore336Protocol, self).__init__(logger)
        assert isinstance(transport, AbstractTransport)

        self.terminal = "\r\n"
        self.separator = ","
        self.encoding = "ascii"

        self._transport = transport

    def clear(self):
        with self._transport:
            try:
                while True:
                    self._transport.read_bytes(5)
            except SerialTimeoutException:
                return

    def create_message(self, header, *data):
        if data is None:
            data = []

        data = map(str, data)

        if not header[-1] == " ":
            header = header + " "

        msg = [header] + data + [self.terminal]

        return ''.join(msg).encode(self.encoding)

    def parse_response(self, response, header):
        resp = response.decode(self.encoding).split(self.separator)

        if len(resp) == 1:
            return resp[0]

        return resp
    
    def query(self, header, *data):
        with self._transport:
            message = self.create_message(header, *data)
            self._logger.debug('Query: %s', repr(message))
            self._transport.write(message)
            response = self._transport.read_until(self.terminal.encode(self.encoding))
            self._logger.debug('Response: %s', repr(response))
            return self.parse_response(response, header)

    def write(self, header, *data):
        with self._transport:
            message = self.create_message(header, *data)
            self._logger.debug('Write: %s', repr(message))
            self._transport.write(message)
