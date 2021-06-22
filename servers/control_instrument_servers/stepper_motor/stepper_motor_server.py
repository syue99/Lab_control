"""
### BEGIN NODE INFO
[info]
name = stepper_motor
version = 1.0
description = 
instancename = stepper_motor

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
###This is a temperarory Motor server for automating the ablation
###Will be replaced by the proper device server (comes from the YeSr lab code)
import sys

from labrad.server import LabradServer, Signal, setting
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.wrappers import connectAsync

#from device_server import DeviceServer

UPDATE_ID = 698021

class StepperMotorServer(LabradServer):
    update = Signal(UPDATE_ID, 'signal: update', 's')
    name = 'stepper_motor'

    serial_server_name = 'desktop-22520i9_serial'
    serial_address = "COM4"
    serial_timeout = 0.5

    @inlineCallbacks
    def initServer(self):
        connection_name = ''#{} - {}'.format(self.device_server_name, self.name)
        self.cxn = yield connectAsync(name=connection_name)
        self.serial_server = yield self.cxn[self.serial_server_name]
        yield self.serial_server.select_interface(self.serial_address)
        #print(type(bytes('/1m30h10R\r'.encode())))
        # set current
        yield self.serial_server.write(bytes('/1m30h10R\r'.encode()))
        ans = yield self.serial_server.read_line()

        # set velocity and acceleration
        yield self.serial_server.write(bytes('/1V1000L500R\r'.encode()))
        ans = yield self.serial_server.read_line()

        # set step resolution
        yield self.serial_server.write(bytes('/1j256o1500R\r'.encode()))
        ans = yield self.serial_server.read_line()
    
    @inlineCallbacks
    def move_absolute_motor(self, position):
        command = '/1A{}R\r'.format(position)
        print (command)
        yield self.serial_server.write(command)
        ans = yield self.serial_server.read_line()
        self.position = position

    @inlineCallbacks
    def toggle_absolute_motor(self,position1, position2):
        command = '/1gH04A{}H14A{}G0R\r'.format(position1, position2)
        yield self.serial_server.write(command)
        ans = yield self.serial_server.read_line()
        
    @setting(10, 'move absolute', position='i', returns='i')
    def move_absolute(self, c, position=None):
        if position is not None:
            yield self.move_absolute_motor(position)
        returnValue(position)

    @setting(11, position1='i', position2='i')
    def toggle_absolute(self, c, position1=None, position2=None):
        if (position1 is not None) and (position2 is not None):
            yield self.toggle_absolute_motor(position1, position2)
        else:
            raise Exception('must specify two positions')

if __name__ == "__main__":
    from labrad import util
    util.runServer(StepperMotorServer())
