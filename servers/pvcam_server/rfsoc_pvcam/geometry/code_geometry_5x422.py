import numpy as np


def get_load_lst(loading, locid):
    load_lst = []
    load_lst_col_order = []
    for i in range(3):
        index = np.where(loading[locid['cols_idx'][i]])[0]
        temp_arr = np.array(locid['cols_idx'][i])
        load_lst.append(temp_arr[index])
        load_lst_col_order.append(index)
    return load_lst, load_lst_col_order  # this is in order of all sites


def compare_load_targ(load_lst, targ_lst, nrowmax=26):
    # assume load_lst is a list of 1d-array
    # targ_lst here is a list of 1d-array
    nsites_assigned = 0
    new_targ_lst = []
    success = True
    for i, load in enumerate(load_lst):
        # nsites_assigned = 0
        start = nsites_assigned
        end = np.min([nsites_assigned + len(load), len(targ_lst[i]), nsites_assigned + nrowmax])
        new_targ_lst.append(targ_lst[i][start:end])
        nsites_assigned = end
    if nsites_assigned < len(targ_lst[0]):
        print('Rearrangement failed: initial loading rate is too low.')
        success = False
    return new_targ_lst, success  # list of 1d-array, array can be empty, meaning do not need it


def compare_load_targ_shortcut(load_lst, load_lst_col_order, targ_lst, nrowmax=26):
    # assume load_lst is a list of 1d-array
    # targ_lst here is a list of 1d-array
    new_targ_lst = []
    success = True
    sites_assigned = np.array(load_lst[0])
    sites_unassigned = np.delete(np.array(targ_lst[0]), load_lst_col_order[0])

    # col 0 stay where it loads, it's useless, but we write here
    new_targ_lst.append(load_lst[0])

    # col 1,2 tetris
    for i in [1, 2]:
        ntweezers = np.min([nrowmax, len(load_lst[i]), len(targ_lst[0]) - len(sites_assigned)])
        new_targ_lst.append(sites_unassigned[:ntweezers])
        sites_assigned = np.append(sites_assigned, new_targ_lst[i])
        sites_assigned.sort()
        sites_unassigned = sites_unassigned[ntweezers:]

    if len(sites_assigned) < len(targ_lst[i]):
        print('Rearrangement failed: initial loading rate is too low.')
        success = False
    return new_targ_lst, success  # list of 1d-array, array can be empty, meaning do not need it


def mid_circuit_func(occupancy, locid):
    occupancy_home = occupancy[locid['cols_idx'][0]]
    idx_home_lst = np.where(occupancy_home)[0]
    if len(idx_home_lst) > 0:
        idxHome = idx_home_lst[0]
        return locid['cols_idx'][0][idxHome]
    else:
        return None

