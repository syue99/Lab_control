import labrad
from labrad.units import WithUnit
import numpy as _np
from matplotlib import pyplot

kinetic_number = 100
identify_exposure = WithUnit(0.001, 's')
start_x = 1
#stop_x = 1600
stop_x = 200
start_y = 1
#stop_y = 200
stop_y = 16

horizontalBinning, verticalBinning = 2, 2
#image_region = (1, 1, start_x, stop_x, start_y, stop_y)
image_region = (horizontalBinning, verticalBinning, start_x, stop_x, start_y, stop_y)

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

cam.set_trigger_mode('External')
cam.start_acquisition()
print('waiting, needs to get TTLs to proceed with each image')

proceed = cam.wait_for_kinetic()
while not proceed:
    proceed = cam.wait_for_kinetic()
print('proceeding to analyze')

image = _np.array(cam.get_acquired_data(kinetic_number))
print(image.shape, image.dtype, max(image))
image = image.astype(_np.int16)
print(image.shape, image.dtype, max(image))
image = _np.reshape(image, (kinetic_number, pixels_y//verticalBinning, pixels_x//horizontalBinning))
_np.save("images.npy", image)

#for num, current in enumerate(image):
    #_np.savetxt(str(num)+".txt",current)
#    _np.save(str(num)+".npy",current)
#for num, current in enumerate(image):
#    pyplot.imsave(str(num)+".jpeg", current)
#    pyplot.figure(num)
#    pyplot.imshow(current)
#_np.savetxt("test.csv",image)

cam.set_trigger_mode('Internal')
cam.set_exposure_time(initial_exposure)
cam.set_image_region(initial_region)
cam.start_live_display()
pyplot.imshow(_np.mean(image, axis=0))
pyplot.show()
