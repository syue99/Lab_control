import labrad
from labrad.units import WithUnit
import numpy as _np
from matplotlib import pyplot
import matplotlib.image as im
import time
import sys
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/pvcam_server/rfsoc_pvcam")
from PvcamDriver import PvcamDriver


identify_exposure = WithUnit(0.2, 's')
start_x = 1
stop_x = 1920
start_y = 1
stop_y = 3000
image_region = (1, 1, start_x, stop_x, start_y, stop_y)

pixels_x = int((stop_x - start_x + 1))
pixels_y = int((stop_y - start_y + 1))

# cxn = labrad.connect()
# cam = cxn.andor_server
cam = PvcamDriver().cam

# cam.abort_acquisition()
# initial_exposure = cam.get_exposure_time()
# cam.set_exposure_time(identify_exposure)
# initial_region = cam.get_image_region()
# cam.set_image_region(*image_region)
# cam.set_shutter_mode('Open')
# cam.set_acquisition_mode('Run till abort')
# cam.start_acquisition()
# cam.wait_for_acquisition()
# image = cam.get_most_recent_image()
image = cam.get_frame(exp_time=1)
# cam.abort_acquisition()
# cam.set_shutter_mode('Close')

image = _np.reshape(image, (pixels_y, pixels_x))
_np.save('sample', image)


pyplot.imshow(image)


# cam.set_exposure_time(initial_exposure)
# cam.set_image_region(initial_region)
# cam.start_live_display()


pyplot.show()
