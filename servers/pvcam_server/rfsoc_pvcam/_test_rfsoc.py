import labrad
cxn = labrad.connect()
import numpy as np
from parameters import params
import json
from json import JSONEncoder

from common import *

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def jsonize(param):
    return json.dumps(param, cls=NumpyArrayEncoder)


nrow = 11
ncol = 11
n_moves = 1
cxn.pvcamNuvuRfsocServer.init_tweezer_ctrl(n_moves, nrow, ncol)

rowfreq = params['rowFreq0_MHz'] - 3 + 0.55 + np.arange(0, 11 * 0.001640625 * 622 * 487 / 532, 0.001640625 * 622 * 487 / 532)
colfreq = params['colFreq0_MHz'] - 13.5 + 0.55 + np.arange(0, 11 * 0.001640625 * 622 * 487 / 532, 0.001640625 * 622 * 487 / 532)

print(rowfreq)
print(colfreq)
rowphase = np.array([0.6592, 1.505, 5.2616, 0.5677, 6.2036, 4.3736, 2.7856, 6.1901, 0.7864, 0.3084, 0.3])
np.random.seed(111)
colphase = np.random.random(len(rowfreq)) * 2 * np.pi
# rowphase = np.random.random(len(rowfreq)) * 2 * np.pi

num_tones = 1

trapParam = {
        'fn': 'phaseOptimization',
        'args': {
            'type': 'fixedAOD',
            'forceSpacing': True,
            'rowIndex': np.arange(10)[:num_tones],
            'colIndex': np.arange(10)[:num_tones],

            'rowAmps': np.ones(1) * 0.5,  # -38.4dBm for 0.7, -35.3dBm for 1

            'colAmps': np.ones(1) * 0.5,
            'rowFreq_MHz': 80.8 + np.arange(-20, 20, 4.)[:num_tones],
            'colFreq_MHz': 55.9 + np.arange(0, 30, 5.)[:num_tones],
            'rowPhase_rad': np.random.random(10)[:num_tones],
            'colPhase_rad': np.random.random(10)[:num_tones],
            'tweezerPowerRegulation': tweezerPDmWToRFSoC(1000),
            'regPhase': np.pi / 3.0,
            'repetition': 0,
            'time': 2e-3,
            }
        }


cxn.pvcamNuvuRfsocServer.process(jsonize(trapParam))

cxn.rfsoc_tw_server.start_socket_server(n_moves)
state_data = cxn.pvcamNuvuRfsocServer.compileMoves()
cxn.pvcamNuvuRfsocServer.uploadBuffer()  # open a client socket and update all buffers to DDS
# cxn.rfsoc_tw_server.config_exp_internal(state_data)
cxn.rfsoc_tw_server.run_exp_internal(state_data)
cxn.finitedopulses.flipTTL(2 ** 4)
