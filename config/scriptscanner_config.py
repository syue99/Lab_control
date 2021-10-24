import sys
sys.path.append('../../experiment_scripts/')
class config(object):

    # list in the format (import_path, class_name)
    scripts = [('PMT_AOM_power_calibration',
                'PMTAOMPowerCalibration'), 
                ('Raman_microwave_scan_coherence',
                'microwave_scan')
                ]

    allowed_concurrent = {
    }

    launch_history = 1000
