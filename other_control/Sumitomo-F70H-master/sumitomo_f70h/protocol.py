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

from sumitomo_f70h.message import AsciiMessage, AsciiResponse

class SumitomoF70HProtocol(Loggable):
    def __init__(self, transport, logger):
        super(SumitomoF70HProtocol, self).__init__(logger)
        assert isinstance(transport, AbstractTransport)

        self._transport = transport

    def clear(self):
        with self._transport:
            try:
                while True:
                    self._transport.read_bytes(5)
            except SerialTimeoutException:
                return

    def _send(self, message):
        raw = message.get_raw()
        self._logger.debug("Sending message '{}'".format(repr(raw)))
        self._transport.write(raw)

    def _read_response(self):
        raw_response = self._transport.read_until(AsciiMessage.END)
        self._logger.debug("Received message '{}'".format(repr(raw_response)))
        response = AsciiResponse.from_raw(raw_response)

        if response.get_cmd() == '???':
            raise CommunicationError("Unknown message send to device. Device did not understand.")

        return response

    def execute(self, message):
        assert isinstance(message, AsciiMessage)
        with self._transport:
            self._send(message)
            return self._read_response()


