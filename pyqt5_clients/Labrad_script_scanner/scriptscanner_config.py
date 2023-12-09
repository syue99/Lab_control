import sys
sys.path.append('../../experiment_scripts/')
class config(object):

    # list in the format (import_path, class_name)
    scripts = [
               ('test_experiment',
                'NIcard_scan'),
                ]

    allowed_concurrent = {
    }

    launch_history = 1000
