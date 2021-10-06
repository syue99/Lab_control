import numpy as np
from time import localtime, strftime
import labrad
from labrad.units import WithUnit
import sys
sys.path.append("../servers/script_scanner/")
import time
from experiment import experiment


class test_image(experiment):
    """Used to repeat an experiment multiple times."""
    parameter= {
    'RFpower':WithUnit(-16,'dBm'),
    'DC':WithUnit(1.5,'V'),
    'TicklingPow':WithUnit(-25,'dBm'),
    'number_of_ions':2,
    }
    def __init__(self):
        super(test_image, self).__init__("Test")
        


    def initialize(self, cxn, context, ident):
        self.navigate_data_vault(cxn, self.parameter, context)
        
    def get_kinetic_external(self, cxn, kinetic_number=10):
        identify_exposure = WithUnit(0.001, 's')
        start_x = 1
        stop_x = 200
        start_y = 1
        stop_y = 16

        horizontalBinning, verticalBinning = 2, 2
        image_region = (horizontalBinning, verticalBinning, start_x, stop_x, start_y, stop_y)

        pixels_x = (stop_x - start_x + 1)
        pixels_y = (stop_y - start_y + 1)

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

        image = np.array(cam.get_acquired_data(kinetic_number))
        print(image.shape, image.dtype, max(image))
        image = image.astype(np.int16)
        print(image.shape, image.dtype, max(image))
        image = np.reshape(image, (kinetic_number, pixels_y//verticalBinning, pixels_x//horizontalBinning))
        np.save("images.npy", image)
        
        avg_image = np.mean(image, axis=0)

        
        cxn.data_vault.add(avg_image, context=context)
        
        cam.set_trigger_mode('Internal')
        cam.set_exposure_time(initial_exposure)
        cam.set_image_region(initial_region)
        cam.start_live_display()


    def run(self, cxn, context):
        
        # self.get_kinetic_external(cxn)
        
        for i in range(100):
            readout = np.random.rand(8, 100) * 256
            time.sleep(0.5)
            print("PMT actual readout counts:")
            print(readout)
            readout = np.array(readout)
            avg_count = np.average(readout)
            print("averaged readout counts")
            print(avg_count)
            print(' ')
            cxn.data_vault.add(readout, context=context)
        return 0
            
            
#pass array of independent and dependent as ["name","unit"]
#Revised by Fred by adding parameter
    def navigate_data_vault(self, cxn, parameter, context):
        dv = cxn.data_vault
        local_time = localtime()
        dataset_name = self.name + strftime("%Y%b%d_%H%M_%S", local_time)
        directory = ['ScriptScanner']
        directory.extend([strftime("%Y%b%d", local_time), strftime("%H%M_%S", local_time)])
        #need this directory to save raw_data
        for text in directory:
            self.dirc=self.dirc+text+'.dir/'
        dv.cd(directory, True, context=context)
        dv.newmatrix(dataset_name, (8,100), 'f', context=context)
        dv.add_parameter('plotLive', True, context=context)
        for para in parameter.keys():
            dv.add_parameter(para, parameter[para], context=context)


    def finalize(self, cxn, context):
        print("finalize")


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    ###: you set the scan freqeuncy and data points needed here
    exprt = test_image()
    ident = scanner.register_external_launch("test_image")
    exprt.execute(ident)