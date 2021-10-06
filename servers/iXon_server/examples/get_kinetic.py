import labrad
from labrad.units import WithUnit
import numpy as _np
from matplotlib import pyplot

kinetic_number = 4
identify_exposure = WithUnit(0.2, 's')
start_x = 1
stop_x = 1600
start_y = 1
stop_y = 200
image_region = (1, 1, start_x, stop_x, start_y, stop_y)

pixels_x = (stop_x - start_x + 1)
pixels_y = (stop_y - start_y + 1)


cxn = labrad.connect()
cam = cxn.andor_server

cam.abort_acquisition()
initial_exposure = cam.get_exposure_time()
cam.set_exposure_time(identify_exposure)
initial_region = cam.get_image_region()
cam.set_image_region(*image_region)
cam.set_acquisition_mode('Kinetics')
cam.set_number_kinetics(kinetic_number)

cam.start_acquisition()
cam.wait_for_kinetic()

image = cam.get_acquired_data(kinetic_number)
image = _np.reshape(image, (kinetic_number, pixels_y, pixels_x))

for num, current in enumerate(image):
    pyplot.figure(num)
    pyplot.contour(current)

cam.set_exposure_time(initial_exposure)
cam.set_image_region(initial_region)
cam.start_live_display()

pyplot.show()
