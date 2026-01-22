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

from protocol import LakeShore336Protocol
from driver import LakeShore336Driver
from e21_util.transport import Serial
from e21_util.log import get_sputter_logger
from e21_util.ports import Ports


class LakeShore336Factory:
    def get_logger(self):
        return get_sputter_logger('Lake Shore Model 336', 'lakeshore336.log')

    @staticmethod
    def create(transport, logger):
        return LakeShore336Driver(LakeShore336Protocol(transport, logger=logger))
