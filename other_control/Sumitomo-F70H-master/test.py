import logging
import sys
#sys.path.append('../e21_util/e21_util')
#from serial_connection import Serial
from e21_util.serial_connection import Serial
from sumitomo_f70h.factory import SumitomoF70HFactory
from sumitomo_f70h.message import AsciiMessage, AsciiCommand, AsciiResponse

# Modify this
transport = Serial('COM3', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
logger = logging.getLogger('Sumitomo F70H')

compressor = SumitomoF70HFactory.create(transport, logger)
for i in range(1,5):
    print(compressor.get_temperature(i))
temp_map = compressor.get_all_temperatures()
#compressor.turn_on()
print(set(temp_map))