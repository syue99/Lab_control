class AndorConfig(object):
    
    '''
    path to atmcd32d.dll SDK library
    '''
    path_to_dll = ('C:\\Program Files\\Andor SOLIS\\atmcd64d_legacy.dll')
    #default parameters
    set_temperature = -10 #degrees C
    read_mode = 'Image'
    acquisition_mode = 'Single Scan'
    trigger_mode = 'Internal'
    exposure_time = 0.100 #seconds
    binning = [1, 1] #numbers of pixels for horizontal and vertical binning
    image_path = ('C:\\Users\\funin\\Desktop')
    save_in_sub_dir = True
    save_format = "tsv"
    save_header = True

