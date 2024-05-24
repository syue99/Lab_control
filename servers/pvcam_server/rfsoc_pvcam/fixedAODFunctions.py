import numpy as np
from servers.rfsoc_pvcam.tweezer_controller import *
import numbers

fnLUT = {}


def func_register(func):
    fnLUT[func.__name__] = func
    return func


@func_register
def phaseOptimization(args):
    config = {
        'f0_row': np.array(args['rowFreq_MHz']),
        'f1_row': np.array(args['rowFreq_MHz']),
        'f0_col': np.array(args['colFreq_MHz']),
        'f1_col': np.array(args['colFreq_MHz']),
        'a0_row': np.array(args['rowAmps']),
        'a1_row': np.array(args['rowAmps']),
        'a0_col': np.array(args['colAmps']),
        'a1_col': np.array(args['colAmps']),
        'p0': args['tweezerPowerRegulation'],
        'p1': args['tweezerPowerRegulation'],
        'phase_row': np.array(args['rowPhase_rad']),
        'phase_col': np.array(args['colPhase_rad']),
        'dur_row': 1,  # Dummy length (cannot be zero because if will be a denominator)
        'dur_col': 1,  # Dummy length (cannot be zero because if will be a denominator)
    }
    hold = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [hold]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabAtoms(args):
    """
    grab and drag atom away.
    """
    ramp_time = args['rampTime']
    drag_time = args['dragTime']
    hold_time = args['holdTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    col_start = args['colFreq0_MHz']
    col_out = args['colFreq0_MHz'] + args['moveOutFreq_MHz']
    row_start = args['rowFreq0_MHz'] + np.arange(0, len(row_amps) * args['rowSpacingFreq_MHz'],
                                                 args['rowSpacingFreq_MHz'])

    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']
    power_low = 0
    power_high = args['tweezerPowerRegulation']

    config = {
        'f0_row': row_start,
        'f1_row': row_start,
        'f0_col': col_start,
        'f1_col': col_start,
        'a0_row': row_amps,
        'a1_row': row_amps,
        'a0_col': col_amps,
        'a1_col': col_amps,
        'p0': power_low,
        'p1': power_high,
        'phase_col': col_phase,
        'phase_row': row_phase,
        'dur_row': ramp_time,
        'dur_col': ramp_time
    }
    ramp_up = Move(**config)

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_out,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_out,
              'f1_col': col_out,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': hold_time,
              'dur_col': hold_time}
    hold = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, hold]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabAndDropByIdxSameCol(args):
    """
    grab and drop atoms specified by site indices. The start and end sites must lie along the same column.
    """
    startIdx = args['startIdx']
    endIdx = args['endIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_end_arr = np.array([aod_freqs[endIdx, 0]])
    if col_end_arr.max() - col_end_arr.min() > 0.1:
        raise ValueError('End indices %s are not in the same column.' % str(endIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = np.array([col_end_arr.mean()])
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = np.append(np.array(aod_freqs[endIdx, 1]), dummpy_row)
    power_low = 0
    power_high = args['tweezerPowerRegulation']

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    # ______ drag atoms out from the SLM_________
    config = {'f0_row': row_start,
              'f1_row': row_end,
              'f0_col': col_start,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, ramp_down]
    state_index = tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def rampUpAndHoldAndRampDown(args):
    """
    grab and drag atom away.
    """
    ramp_time = args['rampTime']
    hold_time = args['holdTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    col_start = args['colFreq_MHz']
    row_start = args['rowFreq_MHz']

    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']
    power_low = 0
    power_high = args['tweezerPowerRegulation']

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': hold_time,
              'dur_col': hold_time}
    hold = Move(**config)

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, hold, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def staticArrayByIdxSameCol(args):
    '''
        grab and drop atoms specified by site indices. The start and end sites must lie along the same column.
        '''
    idx = args['idx']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_arr = np.array([aod_freqs[idx, 0]])
    if col_arr.max() - col_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(idx))

    col_start = np.array([col_arr.mean()])
    row_start = np.array(aod_freqs[idx, 1])
    power_high = args['tweezerPowerRegulation']

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': 1,
              'dur_col': 1}
    hold = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [hold]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabAndThrowAwayByIdxSameCol(args):
    '''
    grab and drop atoms specified by site indices. The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = 0
    power_high = args['tweezerPowerRegulation']

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    # ______ drag atoms out from the SLM_________
    config = {'f0_row': row_start,
              'f1_row': row_end,
              'f0_col': col_start,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabAndReturnByIdxSameCol(args):
    '''
    grab and drop atoms specified by site indices. The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = args['tweezerPowerZero']
    power_high = args['tweezerPowerRegulation']

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    # ______ drag atoms out from the SLM_________
    config = {'f0_row': row_start,
              'f1_row': row_end,
              'f0_col': col_start,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    # ______ return atoms back to the SLM_________
    config = {'f0_row': row_end,
              'f1_row': row_start,
              'f0_col': col_end,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_back = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, drag_back, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabHoldReturnByIdxSameCol(args):
    '''
    grab and drop atoms specified by site indices. The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']
    hold_time = args['holdTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = args['tweezerPowerZero']
    power_high = args['tweezerPowerRegulation']

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    # ______ drag atoms out from the SLM_________
    config = {'f0_row': row_start,
              'f1_row': row_end,
              'f0_col': col_start,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    # ______ hold atoms in AOD _________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': hold_time,
              'dur_col': hold_time}
    hold = Move(**config)

    # ______ return atoms back to the SLM_________
    config = {'f0_row': row_end,
              'f1_row': row_start,
              'f0_col': col_end,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_back = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, hold, drag_back, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabMoveoutByIdxSameCol(args):
    '''
    grab atoms and move out of SLM traps specified by site indices.
    The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']
    hold_time = args['holdTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = args['tweezerPowerZero']
    power_high = args['tweezerPowerRegulation']

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    # ______ drag atoms out from the SLM_________
    config = {'f0_row': row_start,
              'f1_row': row_end,
              'f0_col': col_start,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    # ______ hold in AOD _________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': hold_time,
              'dur_col': hold_time}
    hold = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, hold]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def returnByIdxSameCol(args):
    '''
    Start with atoms in AOD traps, and move them back to SLM traps. Can be used in pair with grabMoveoutByIdxSameCol.
    The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']
    hold_time = args['holdTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = args['tweezerPowerZero']
    power_high = args['tweezerPowerRegulation']

    # ______ hold in AOD _________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': hold_time,
              'dur_col': hold_time}
    hold = Move(**config)

    # ______ drag atoms back to the SLM_________
    config = {'f0_row': row_end,
              'f1_row': row_start,
              'f0_col': col_end,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_back = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [hold, drag_back, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def grabMoveoutRampByIdxSameCol(args):

    '''
    grab atoms, move out of SLM traps, ramp AOD power specified by site indices.
    The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = args['tweezerPowerZero']
    power_high = args['tweezerPowerRegulation']
    power_hold = args['tweezerPowerHold']

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    # ______ drag atoms out from the SLM_________
    config = {'f0_row': row_start,
              'f1_row': row_end,
              'f0_col': col_start,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_out = Move(**config)

    # ______ ramp AOD _________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_hold,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, drag_out, ramp]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def rampReturnByIdxSameCol(args):
    '''
    Start with atoms in AOD traps, ramp AOD power and move them back to SLM traps.
    Can be used in pair with grabMoveoutByIdxSameCol.
    The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    ramp_time = args['rampTime']
    drag_time = args['dragTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    col_end = col_start + args['colFreqDrag_MHz']
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    row_end = row_start + args['rowFreqDrag_MHz']
    power_low = args['tweezerPowerZero']
    power_high = args['tweezerPowerRegulation']
    power_hold = args['tweezerPowerHold']

    # ______ ramp AOD _________
    config = {'f0_row': row_end,
              'f1_row': row_end,
              'f0_col': col_end,
              'f1_col': col_end,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_hold,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp = Move(**config)

    # ______ drag atoms back to the SLM_________
    config = {'f0_row': row_end,
              'f1_row': row_start,
              'f0_col': col_end,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': drag_time,
              'dur_col': drag_time}
    drag_back = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp, drag_back, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def rampUpAOD(args):
    """
    grab and drag atom away.
    """
    ramp_time = args['rampTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    col_start = args['colFreq_MHz']
    row_start = args['rowFreq_MHz']

    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']
    power_low = 0
    power_high = args['tweezerPowerRegulation']

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_up = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def trapModulationByIdxSameCol(args):
    '''
    trap modulation specified by site indices.
    The start and end sites must lie along the same column.
    '''
    startIdx = args['startIdx']
    period = args['period']
    modDepth = args['modDepth']  # relative value, ranging from 0 to 1
    if period % 2 == 1:
        raise ValueError('Period must by even number!')

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    nTwz = args['nTwz']
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    aod_freqs = np.array(args['freqArrXY_MHz'])
    col_start_arr = np.array([aod_freqs[startIdx, 0]])
    if col_start_arr.max() - col_start_arr.min() > 0.1:
        raise ValueError('Start indices %s are not in the same column.' % str(startIdx))

    col_start = np.array([col_start_arr.mean()])
    dummpy_row = np.max(aod_freqs[:, 1]) + np.arange(nTwz - len(startIdx)) + 2
    row_start = np.append(np.array(aod_freqs[startIdx, 1]), dummpy_row)
    power_low = args['tweezerPowerRegulation'] * (1 - modDepth)
    power_high = args['tweezerPowerRegulation'] * (1 + modDepth)

    # ______ ramp AOD power up_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_low,
              'p1': power_high,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': period//2,
              'dur_col': period//2}
    ramp_up = Move(**config)

    # ______ ramp AOD power down_________
    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': period // 2,
              'dur_col': period // 2}
    ramp_down = Move(**config)


    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_up, ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def rampDownAOD(args):
    """
    grab and drag atom away.
    """
    ramp_time = args['rampTime']

    row_amps, col_amps = args['rowAmps'], args['colAmps']
    col_start = args['colFreq_MHz']
    row_start = args['rowFreq_MHz']

    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']
    power_low = 0
    power_high = args['tweezerPowerRegulation']

    config = {'f0_row': row_start,
              'f1_row': row_start,
              'f0_col': col_start,
              'f1_col': col_start,
              'a0_row': row_amps,
              'a1_row': row_amps,
              'a0_col': col_amps,
              'a1_col': col_amps,
              'p0': power_high,
              'p1': power_low,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': ramp_time,
              'dur_col': ramp_time}
    ramp_down = Move(**config)

    tweezer_ctrl = args['tweezer_ctrl']
    move_list = [ramp_down]
    tweezer_ctrl.append_state(move_list)
    move_indices = [move.idx for move in move_list]

    return move_indices


@func_register
def arbitrarySegmentsByIdxSameCol(args):
    """
    Do arbitrary movements in segments. The start and end sites must lie along the same column.
    f_delta_row, f_delta_col: AOD freq delta relative to start index frequency.
        Single number or list of length n_segments - 1. If single value, use same freq for all segments.
    power, dur_row, dur_col: power, durations of each segment. Single value or list of length n_segments - 1.
        If single number, use same value for all segments.
    At least one of {f_delta_row, f_delta_col, power, dur_row, dur_col} must be a list.
    """
    def singleValue2list(x, length):
        # if x is a single number, make it list of size length. If x is a list, check if it has the correct length.
        if isinstance(x, numbers.Number):
            return [x] * length
        else:
            assert(len(x) == length)
    segmentParamsList = ['f_delta_row', 'f_delta_col', 'power', 'dur_row', 'dur_col']

    length = 0  # get the maximum length of segment params
    for i in segmentParamsList:
        if isinstance(args[i], numbers.Number):
            continue
        if len(args[i]) > length:
            length = len(args[i])
    start_idx = args['start_idx']
    f_delta_row = args['f_delta_row']
    f_delta_col = args['f_delta_col']
    a_row = args['a_row']
    a_col = args['a_col']
    power = args['power']
    phase_row = args['phase_row']
    phase_col = args['phase_col']
    dur_row = args['dur_row']
    dur_col = args['dur_col']

    n_segments = len(f_delta_col)-1



    # 'f1_col': col_start,
    # 'a0_row': row_amps,
    # 'a1_row': row_amps,
    # 'a0_col': col_amps,
    # 'a1_col': col_amps,
    # 'p0': power_high,
    # 'p1': power_low,
    # 'phase_col': col_phase,
    # 'phase_row': row_phase,
    # 'dur_row': ramp_time,
    # 'dur_col': ramp_time


def getFn(key):
    try:
        fn = fnLUT[key]
        return fn
    except KeyError:
        print(key + ' does not exist in fixedAODFunctions.py')
