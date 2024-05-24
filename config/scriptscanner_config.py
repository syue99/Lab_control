import sys
sys.path.append('../../experiment_scripts/')
class config(object):

    # list in the format (import_path, class_name)
    scripts = [
               ('test_experiment',
                'NIcard_scan'),
    
                ('test_experiment_phase',
                'rydberg_experiment'),
                ]

    allowed_concurrent = {
    }

    launch_history = 1000
