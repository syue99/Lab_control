import time
import numpy as np
from servers.rfsoc_pvcam.geometry.code_geometry_5x422 import *

fnLUT = {}


def func_register(func):
    fnLUT[func.__name__] = func
    return func


def _ramp_traps(ctrl, config, p1, dur):
    config['p1'] = p1
    config['dur_row'] = dur
    config['dur_col'] = dur
    ctrl.update_move(config['move_ctr'], **config)

    # update params for next move
    config['p0'] = p1
    config['move_ctr'] += 1


def _drag_traps_along_row(ctrl, config, f1_row, dur):
    config['f1_row'] = f1_row
    config['dur_row'] = dur
    config['dur_col'] = dur
    ctrl.update_move(config['move_ctr'], **config)

    # update params for next move
    config['f0_row'] = f1_row
    config['move_ctr'] += 1


def _drag_traps_along_col(ctrl, config, f1_col, dur):
    config['f1_col'] = f1_col
    config['dur_row'] = dur
    config['dur_col'] = dur
    ctrl.update_move(config['move_ctr'], **config)

    # update params for next move
    config['f0_col'] = f1_col
    config['move_ctr'] += 1


def _compare_array_length(a, b):
    if len(a) < len(b):
        return a, b[:len(a)]
    else:
        return a, b


@func_register
def rearrange_code_config_shortcut(args):
    ctrl = args['tweezer_ctrl']
    start_idx = args['move_start_idx']
    state_idx = args['state_idx']
    # print('rearr state_idx = ', state_idx)

    rampTime = args['rampTime']
    dragTime = args['dragTime']
    dragTimeY = args['dragTimeY']
    rearrangeTimeX2 = args['rearrangeTimeX2']
    rearrangeTime = args['rearrangeTime']
    nrowmax = args['nRowMax']
    totalMoves = args['nMovesRequired']

    dummyLoad = np.array(args['dummyLoad'])

    moveOutFreq = args['moveOutFreq_MHz']
    rowAmps, colAmps = args['rowAmps'], args['colAmps']
    aod_freqs = np.array(args['freqArrXY_MHz'])

    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    resDict, conditionImage, conditionFnIdx = args['currentResultDict'], args['conditionImageInfo']['index'], args[
        'conditionAnalysisName']
    conditionCamera = args['conditionImageInfo']['cam']

    load_all = resDict[conditionCamera][conditionImage][conditionFnIdx]
    # load_all = dummyLoad
    locid = args['locid']
    load_lst, load_lst_col_order = get_load_lst(load_all, locid)
    targ_lst = [locid['cols_idx'][kk] for kk in range(3)]

    targ_lst, _ = compare_load_targ_shortcut(load_lst, load_lst_col_order, targ_lst, nrowmax)

    dump_freq = np.linspace(1, 13, 26)

    for i in range(3):
        load_lst[i] = load_lst[i][:nrowmax]

    power_off = args['tweezerPowerZero']
    power_on = args['tweezerPowerRegulation']

    # ------------------------------------------------
    i = 1
    load = load_lst[i]
    targ = targ_lst[i]
    fcol_start = np.array([aod_freqs[locid['cols_idx'][i], 0].mean()])
    fcol_mid = fcol_start + moveOutFreq
    fcol_end = np.array([aod_freqs[locid['cols_idx'][0], 0].mean()])

    frow_start = np.concatenate(
        (aod_freqs[load, 1], aod_freqs[locid['cols_idx'][i][-1], 1] + dump_freq[:nrowmax - len(load)])
    )
    frow_end = np.concatenate(
        (aod_freqs[targ, 1], aod_freqs[locid['cols_idx'][i][-1], 1] + dump_freq[:nrowmax - len(targ)])
    )
    # Define intital config state. The ramp traps/drag traps functions update the next move to sweep to the target state.
    # The parameter that's swept is determined by whether its the ramp or drag col/row function. After writing a sweep,
    # the config is updated to the target state so that it can be directly used by the next ramp/drag function. The move
    # number to be updated is included in the config dict an incremented by +1 by each function, so that consecutive
    # ramp/drag fns automatically update a contiguous block of moves.
    config = {'f0_row': frow_start,
              'f1_row': frow_start,
              'f0_col': fcol_start,
              'f1_col': fcol_start,
              'a0_row': rowAmps,
              'a1_row': rowAmps,
              'a0_col': colAmps,
              'a1_col': colAmps,
              'p0': power_off,
              'p1': power_off,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': rampTime,
              'dur_col': rampTime,
              'move_ctr': start_idx}

    _ramp_traps(ctrl, config, power_on, rampTime)

    # drag off grid/ drag along col
    _drag_traps_along_col(ctrl, config, fcol_mid, dragTime)

    # rearrange atoms/ drag along row
    _drag_traps_along_row(ctrl, config, frow_end, rearrangeTime)

    # drag back on grid/ drag along col
    _drag_traps_along_col(ctrl, config, fcol_end, dragTime)

    # drop/ ramp down
    _ramp_traps(ctrl, config, power_off, rampTime)

    # ------------------------------------------------
    i = 2
    load = load_lst[i]
    targ = targ_lst[i]
    fcol_start = np.array([aod_freqs[locid['cols_idx'][i], 0].mean()])
    fcol_end = np.array([aod_freqs[locid['cols_idx'][0], 0].mean()])
    fcol_mid = fcol_start + moveOutFreq

    frow_start = np.concatenate(
        (aod_freqs[load, 1], aod_freqs[locid['cols_idx'][i][-1], 1] + dump_freq[:nrowmax - len(load)])
    )
    frow_end = np.concatenate(
        (aod_freqs[targ, 1], aod_freqs[locid['cols_idx'][i][-1], 1] + dump_freq[:nrowmax - len(targ)])
    )
    frow_mid = frow_end - 0.95 * moveOutFreq

    # reset config dict, but keep count of moves
    idx = config['move_ctr']
    config = {'f0_row': frow_start,
              'f1_row': frow_start,
              'f0_col': fcol_start,
              'f1_col': fcol_start,
              'a0_row': rowAmps,
              'a1_row': rowAmps,
              'a0_col': colAmps,
              'a1_col': colAmps,
              'p0': power_off,
              'p1': power_off,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': rampTime,
              'dur_col': rampTime,
              'move_ctr': idx}

    # grab/ ramp up
    _ramp_traps(ctrl, config, power_on, rampTime)

    # drag off grid/ drag along col
    _drag_traps_along_col(ctrl, config, fcol_mid, dragTime)

    # rearrange atoms/ drag along row
    _drag_traps_along_row(ctrl, config, frow_mid, rearrangeTime)

    # drag along col to col 0
    _drag_traps_along_col(ctrl, config, fcol_end, rearrangeTimeX2)

    # drag along Y/row
    _drag_traps_along_row(ctrl, config, frow_end, dragTimeY)

    # drop/ ramp down
    _ramp_traps(ctrl, config, power_off, rampTime)

    # remove atoms in gate zone
    f_row_gatezone = np.concatenate(
        (aod_freqs[locid['cols_idx'][3], 1],
         aod_freqs[locid['cols_idx'][3][-1], 1] + dump_freq[:nrowmax - len(locid['cols_idx'][3])])
    )

    f_col_gatezone = np.array([aod_freqs[locid['cols_idx'][3], 0].mean()])
    f_col_off_gatezone = f_col_gatezone + 1

    # reset config dict, but keep count of moves
    idx = config['move_ctr']
    config = {'f0_row': f_row_gatezone,
              'f1_row': f_row_gatezone,
              'f0_col': f_col_gatezone,
              'f1_col': f_col_gatezone,
              'a0_row': rowAmps,
              'a1_row': rowAmps,
              'a0_col': colAmps,
              'a1_col': colAmps,
              'p0': power_off,
              'p1': power_off,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': rampTime,
              'dur_col': rampTime,
              'move_ctr': idx}

    # grab/ ramp up
    _ramp_traps(ctrl, config, power_on, rampTime)
    # drag to dump zone
    _drag_traps_along_col(ctrl, config, f_col_off_gatezone, dragTime)
    # drop/ ramp down
    _ramp_traps(ctrl, config, power_off, 1)  # The duration should always be >= 1, to avoid division of zero.

    # push data we've just added to the ctrl buffer to rfsoc
    n_moves_to_update = config['move_ctr'] - start_idx
    t0 = time.time()
    ctrl.send_data_socket(state_idx, n_moves_to_update)
    print('takes {:.10f} ms to update data for rearrangement...'.format((time.time() - t0) * 1e3))
    return 0


@func_register
def replace_erasure_qubit_422(args):
    ctrl = args['tweezer_ctrl']
    start_idx = args['move_start_idx']
    state_idx = args['state_idx']
    # print('cond state_idx = ', state_idx)

    rampTime = args['rampTime']
    dragTime = args['dragTime']
    dragTimeY = args['dragTimeY']
    nTweezers = args['nTwz']
    nMovesRequired = args['nMovesRequired']

    moveOutFreq = args['moveOutFreq_MHz']

    rowAmps, colAmps = args['rowAmps'], args['colAmps']
    aod_freqs = np.array(args['freqArrXY_MHz'])
    row_phase, col_phase = args['rowPhase_rad'], args['colPhase_rad']

    dummyOccupancy = args['dummyOccupancy']

    resDict, conditionImage, conditionFnIdx = args['currentResultDict'], args['conditionImageInfo']['index'], args[
        'conditionAnalysisName']
    conditionCamera = args['conditionImageInfo']['cam']
    # occupancy = resDict[conditionCamera][conditionImage][conditionFnIdx]
    occupancy = np.array(dummyOccupancy)

    locid = args['locid']

    # FIXME: THE MID-CIRCUIT DECISION FUNCTION IS A DUMMY HERE!
    dest_idx = mid_circuit_func(occupancy=occupancy, locid=locid)
    subs_idx = locid['cols_idx'][0][0]

    power_off = args['tweezerPowerZero']
    power_on = args['tweezerPowerRegulation']

    dummy_freq = aod_freqs[locid['cols_idx'][0][-1], 1] + 1 + 0.5 * np.arange(nTweezers - 1)

    if dest_idx == None:
        frow_start = np.concatenate(([aod_freqs[locid['cols_idx'][2][0], 1]], dummy_freq))
        frow_end = np.concatenate(([aod_freqs[locid['cols_idx'][2][0], 1]], dummy_freq))
        fcol_start = np.array([aod_freqs[locid['cols_idx'][2][0], 0]])
        fcol_end = np.array([aod_freqs[locid['cols_idx'][2][0], 0]])

    else:
        frow_start = np.concatenate(([aod_freqs[subs_idx, 1]], dummy_freq))
        frow_end = np.concatenate(([aod_freqs[dest_idx, 1]], dummy_freq))
        fcol_start = np.array([aod_freqs[subs_idx, 0]])
        fcol_end = np.array([aod_freqs[dest_idx, 0]])

    # print('dest_idx', dest_idx)
    # print('dummy_occu', np.where(occupancy)[0])



    config = {'f0_row': frow_start,
              'f1_row': frow_start,
              'f0_col': fcol_start,
              'f1_col': fcol_start,
              'a0_row': rowAmps,
              'a1_row': rowAmps,
              'a0_col': colAmps,
              'a1_col': colAmps,
              'p0': power_off,
              'p1': power_off,
              'phase_col': col_phase,
              'phase_row': row_phase,
              'dur_row': rampTime,
              'dur_col': rampTime,
              'move_ctr': start_idx}

    _ramp_traps(ctrl, config, power_on, rampTime)
    _drag_traps_along_col(ctrl, config, fcol_start + moveOutFreq, dragTime)
    _drag_traps_along_row(ctrl, config, frow_end, dragTimeY)
    _drag_traps_along_col(ctrl, config, fcol_end, dragTime)
    _ramp_traps(ctrl, config, power_off, rampTime)

    # push data we've just added to the ctrl buffer to RFSoC
    t0 = time.time()
    ctrl.send_data_socket(state_idx, nMovesRequired, update_state_idx=False)
    print('takes {:.10f} ms to update data'.format((time.time() - t0) * 1e3))
    return 0


def getFn(key):
    try:
        fn = fnLUT[key]
        return fn
    except KeyError:
        print(key + ' does not exist in:\n' + __file__)
