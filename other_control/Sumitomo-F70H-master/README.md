# Sumitomo-F70H
Python implementation of the Sumitomo F-70H serial interface

# Usage
You can use the following code to create the driver for the compressor. 
```python
import logging

from e21_util.serial_connection import Serial
from sumitomo_f70h.factory import SumitomoF70HFactory

# Modify this
transport = Serial('/dev/ttyUSBx', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
logger = logging.getLogger('Sumitomo F70H')

compressor = SumitomoF70HFactory.create(transport, logger)
# compressor is an instance of SumitomoF70HDriver
print(compressor.get_temperature(1))
```
