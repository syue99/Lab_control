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

class LakeShore336Driver(object):

    HEATER_RANGE_OFF = '0'
    HEATER_RANGE_ON  = '1'
    HEATER_RANGE_LOW = '1'
    HEATER_RANGE_MED = '2'
    HEATER_RANGE_HIGH = '3'

    CHANNEL_A = 'A'
    CHANNEL_B = 'B'
    CHANNEL_C = 'C'
    CHANNEL_D = 'D'

    CHANNELS = [CHANNEL_A, CHANNEL_B, CHANNEL_C, CHANNEL_D]

    def __init__(self, protocol):
        assert isinstance(protocol, LakeShore336Protocol)

        self._protocol = protocol

    def query(self, cmd, *data):
        return self._protocol.query(cmd, *data)

    def write(self, cmd, *data):
        self._protocol.write(cmd, *data)

    def get_identification(self):
        return self.query('*IDN?')
    
    def get_temperature(self, channel):
        """
        :param input_channel:
        :return: Returns the temperature of the given channel in float, units being Kelvin
        """
        channel = self.to_str_channel(channel)
        return float(self.query('KRDG?', channel))
    
    def set_control_setpoint(self, output, value):
        output = self.to_int_channel(output)

        self.write('SETP', output, value)

    def get_control_setpoint(self, output):
        output = self.to_int_channel(output)
        return float(self.query('SETP?', output))
    
    def set_pid(self, output, p, i, d):
        output = self.to_int_channel(output)
        if output > 2:
            raise ValueError('Output 1 or 2 are only allowed for PID values')

        self.write('PID', output, p, i, d)
    
    def get_pid(self, output):
        """
        :param output:
        :return: Returns the p, i, d parameter as floats
        """
        output = self.to_int_channel(output)
        response = self.query('PID?', output)
        return list(map(float, response))

    def set_temperature_limit(self, channel, limit):
        channel = self.to_str_channel(channel)
        self.write('TLIMIT', channel, limit)
    
    def get_temperature_limit(self, channel):
        channel = self.to_str_channel(channel)
        return float(self.query('TLIMIT?', channel))
    
    def clear(self):
        self._protocol.clear()
        self.write('*CLS')
        self._protocol.clear()

    def reset(self):
        self.write('*RST')
    
    def set_alarm(self, channel, enabled, high, low, deadband, latch_enabled, audible, visible):
        channel = self.to_str_channel(channel)
        self.write('ALARM', channel, enabled, high, low, deadband, latch_enabled, audible, visible)
                      
    def get_alarm(self, channel):
        channel = self.to_str_channel(channel)
        return self.query('ALARM?', channel)
    
    def get_alarm_status(self, channel):
        channel = self.to_str_channel(channel)
        response = self.query('ALARMST?', channel)
        return list(map(bool, response))
    
    def reset_alarm(self):
        self.write('ALMRST')
    
    def set_input_name(self, channel, name):
        if not(name[0] == '"' and name[-1] == '"'):
            name = '"' + name + '"'

        self.write('INNAME', channel, name)
        
    def get_input_name(self, channel):
        return self.query('INNAME?', channel)
    
    def set_led(self, enable):
        if enable:
            enable = 1
        else:
            enable = 0

        self.write('LEDS', enable)
        
    def get_led(self):
        return bool(int(self.query('LEDS?')))
                                       
    def set_heater_range(self, channel, rng):
        if rng not in [self.HEATER_RANGE_HIGH, self.HEATER_RANGE_LOW, self.HEATER_RANGE_MED, self.HEATER_RANGE_OFF, self.HEATER_RANGE_ON]:
            raise ValueError("Unknown range given")
        channel = self.to_int_channel(channel)
        self.write("RANGE", channel, rng)

    def get_heater_range(self, channel):
        return int(self.query('RANGE?', channel))
                                       
    def get_thermocouple_junction_temperature(self):
        return float(self.query('TEMP?'))

    def is_channel_str(self, channel):
        if not isinstance(channel, basestring):
            return False
        channel = str(channel).upper()
        return channel in self.CHANNELS
    
    def is_channel_int(self, channel):
        return isinstance( channel, (int, long)) and channel <= 4 and channel >= 1
        
    def channel_str_to_int(self, channel):
        switcher = {
            'A': 1,
            'B': 2,
            'C': 3,
            'D': 4
        }
        
        return switcher.get(channel.upper(), 1)
    
    def channel_int_to_str(self, channel):
        switcher = {
            1: 'A',
            2: 'B',
            3: 'C',
            4: 'D',
            '1': 'A',
            '2': 'B',
            '3': 'C',
            '4': 'D'
        }
        return switcher.get(channel, 'A')
    
    def to_int_channel(self, channel):
        if self.is_channel_int(channel):
            return channel
        elif self.is_channel_str(channel):
            return self.channel_str_to_int(channel)
        else:
            raise ValueError("Unknown channel %s" % repr(channel))
        
    def to_str_channel(self, channel):
        if self.is_channel_str(channel):
            return channel.upper()
        elif self.is_channel_int(channel):
            return self.channel_int_to_str(channel)
        else:
            raise ValueError("Unknown channel %s" % repr(channel))
