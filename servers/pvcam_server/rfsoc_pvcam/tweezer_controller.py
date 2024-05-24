import pickle as pickle  # FIXME: revert to _pickle!!
import socket
from struct import pack

import numpy as np


class BufferParser(object):
    """
    Parameters
    ----------
    buff : np.array
        Pre-allocated buffer, needs to be dtype=np.int32
    move_num : int
        The move number -- this where in buff the parameters are written. Given
        NREG parameter registers per DDS tone and n_dds tones per move, the
        element in buff is calculated by (NREG+1)*move_num*n_dds.
    n_dds : int
        The number of DDS channels for this buffer. 
    f_fn : func
        Function with args (f0, f1, dur, n_dds) must return np.array of dim (6, n_dds)
        with 5th order poly coefficients for desired sweep trajectory. 
    f_gain : float
        Frequency modulation gain. 
    a_fn : func
        Function with args (a0, a1, dur, n_dds) must return np.array of dim (4, n_dds)
        with 3th order poly coefficients for desired amplitude trajectory. 
    a_gain : float
        Amplitude modulation gain.
    ch_offset : int
        Offsets added to the DDS channel register; used by DC power regulation child class. 
    """
    def __init__(self, buff, move_num, n_dds, f_fn, f_gain, a_fn, a_gain, ch_offset=0):
        self.fs = 430.08000000000004
        self.dphi = 0.001373291015625
        self.BFREQ = 18
        self.BAMP = 16
        self.NREG = 15
        self.NDDS = 32
        self.BT = 13
        self.ts = 1/self.fs
        # time quantization
        self.SWEEP_TIME_US = self.ts * (2**(self.BT - 1))

        self.f_fn = f_fn
        self.a_fn = a_fn
        self.f_gain = f_gain
        self.a_gain = a_gain
        self.n_dds = n_dds

        # stride is the total number of elements per DDS channel
        stride = self.NREG+1
        # First index of current move
        idx0 = move_num*stride*self.NDDS + ch_offset*stride
        move_buff = buff[idx0:(idx0+stride*n_dds)]

        self.ch_view = move_buff[::stride]
        self.addr_view = move_buff[1::stride]
        self.f0_view = move_buff[2::stride]
        self.f1_view = move_buff[3::stride]
        self.f2_view = move_buff[4::stride]
        self.f3_view = move_buff[5::stride]
        self.f4_view = move_buff[6::stride]
        self.f5_view = move_buff[7::stride]
        self.fmod_g_view = move_buff[8::stride]
        self.a0_view = move_buff[9::stride]        
        self.a1_view = move_buff[10::stride]
        self.a2_view = move_buff[11::stride]
        self.a3_view = move_buff[12::stride]
        self.amod_g_view = move_buff[13::stride]
        self.ph_view = move_buff[14::stride]

        ## Fill in the static entries of the buffer
        #self.ch_view[:] = np.arange(n_dds) + ch_offset
        #self.addr_view[:] = np.ones(n_dds) * move_num

    
    def parse_move(self, f0, f1, a0, a1, phase):
        # Calc coefficients and quantize. 
        f0 = f0/(self.fs/2)
        f1 = f1/(self.fs/2)
        c = self.f_fn(f0, f1, self.n_dds)
        # IL: integer length. Include the sign bit.
        IL = np.clip(np.ceil(np.log2(np.max(np.append(np.abs(c), 1), axis=0))).astype(np.int32) + 1, 1, self.BFREQ)
        FL = self.BFREQ - IL
        c2FL = c * 2**FL

        # Write coefficients into regs 
        self.f0_view[:] = c2FL[0, :]
        self.f1_view[:] = c2FL[1, :]
        self.f2_view[:] = c2FL[2, :]
        self.f3_view[:] = c2FL[3, :]
        self.f4_view[:] = c2FL[4, :]
        self.f5_view[:] = c2FL[5, :]
        
        # Gain Quantization. Output product should be Q6.X, where X is 2*B - 6.
        # Calc the remaining number of bits for gain. 
        ILg = 6 - IL
        FLg = self.BFREQ - ILg
    
        # Write gain into regs structure.
        self.fmod_g_view[:] = self.f_gain*(2**FLg)

        # Calc coefficients and quantize for amplitude poly. 
        c = self.a_fn(a0, a1, self.n_dds)

        # IL: integer length, include the sign bit.
        IL = np.clip(np.ceil(np.log2(np.max(np.append(np.abs(c), 1), axis=0))).astype(np.int32) + 1, 1, self.BAMP)
        AL = self.BAMP - IL
        c2AL = c * 2**AL
        self.a0_view[:] = c2AL[0, :]
        self.a1_view[:] = c2AL[1, :]
        self.a2_view[:] = c2AL[2, :]
        self.a3_view[:] = c2AL[3, :]

        # Gain Quantization. Output product should be Q4.X, where X is 2*B - 4.
        # Calc the remaining number of bits for gain. 
        ILg = 4 - IL
        FLg = self.BAMP - ILg

        self.amod_g_view[:] = self.a_gain*(2**FLg)

        # write phase entry.
        self.ph_view[:] = np.array(np.round(phase/self.dphi), dtype=np.int32) * 180  # Here it's in degree.


class BufferParserPwr(BufferParser):
    """
    Overload BufferParser for power ramp DDS. This is the same as the normal
    BufferParser but just for a single DDS channel and keeps the freq sweep
    registers zero. 

    Parameters
    ----------
    buff : np.array
        Pre-allocated buffer, needs to be dtype=np.int32
    move_num : int
        The move number -- this where in buff the parameters are written. Given
        NREG parameter registers per DDS tone the element in buff is calculated
        by (NREG+1)*move_num.
    p_fn : func
        Function with args (p0, p1, dur, n_dds) must return np.array of dim (4, n_dds) 
        with 3th order poly coefficients for desired DC power ramp trajectory.  
    p_gain : float
        DC power modulation gain. 
    """
    def __init__(self, buff, move_num, p_fn, p_gain):
        self.NDDS = 32
        self.NREG = 15
        f_fn = None
        f_gain = 0
        pwr_dds = 31

        # setting n_dds = 1 and providing ch_offset means parent init can set DC power reg channel
        super(BufferParserPwr, self).__init__(buff, move_num, 1, f_fn, f_gain, p_fn, p_gain, ch_offset=pwr_dds)

    def parse_move(self, p0, p1):
        # add entries for power modulation -- these are written to amp mod regs of a single DDS 
        c = self.a_fn(p0, p1, self.n_dds)
        # IL: integer length, include the sign bit.
        IL = np.clip(np.ceil(np.log2(np.max(np.append(np.abs(c), 1), axis=0))).astype(np.int32) + 1, 1, self.BAMP)
        AL = self.BAMP - IL
        c2AL = c * 2**AL
        self.a0_view[:] = c2AL[0, :]
        self.a1_view[:] = c2AL[1, :]
        self.a2_view[:] = c2AL[2, :]
        self.a3_view[:] = c2AL[3, :]

        # Gain Quantization. Output product should be Q4.X, where X is 2*B - 4.
        # Calc the remaining number of bits for gain. 
        ILg = 4 - IL
        FLg = self.BAMP - ILg

        self.amod_g_view[:] = self.a_gain*(2**FLg)



class Move:
    """ 
    Sweep freqs from f0 to f1 and amp a0 to a1 for row and col generators.
    
    Use functional form f_fn (ie, min_jerk) for position ramp.  Use functioanl
    form a_fn (ie, 'linear') for amplitude ramp.
    
    force_even = 'start', 'end', 'none', 'both' specifies wether frequencies
    should be coerced to a grid
     
    The key idea of abstracting into a class is that you can have the default
    behavior of the class handle the kind of moves that you want to do most of
    the time which does not necessarily use the full expressivity of the RFSoC
    but then if you want to do something very complicated for one step, you can
    just overload the class.
    
    Parameters
    ----------
    kwargs:
    
    Dictionary of sweep parametwers. The mandatory parameters are:
    * dur_row, the duration in units of DDS time quantization for the row generator;
    * dur_col, the duration in units of DDS time quantization for the column
    generator;
    * f0_row, f1_row, f0_col and f1_col, each vectors of length n_dds containing
    the initial and final row and column frequencies;
    * a0_row, a1_row, a0_col and a1_col, each vectors of length n_dds containing
    the initial and final row and column amplitudes;
    * p0_row, p1_row, p0_col and p1_col, each vectors of length n_dds containing
    the initial and final row and column aux DC power output;
    * phase_row, vector of length n_dds specifing the initial phase values for row gen. 
    * phase_col, vector of length n_dds specifing the initial phase values for col gen. 
    """

    # kwarg lists used for automatic padding of vectors to nrow_dds/ncol_dds
    row_kwargs = ['f0_row', 'f1_row', 'a0_row', 'a1_row', 'phase_row']
    col_kwargs = ['f0_col', 'f1_col', 'a0_col', 'a1_col', 'phase_col']

    def __init__(self, **kwargs):
 
        required_params = ['f0_row', 'f1_row', 'f0_col', 'f1_col', 'a0_row',
        'a1_row', 'a0_col', 'a1_col', 'p0', 'p1', 'phase_row', 'phase_col', 'dur_row', 'dur_col']

        if any([p not in kwargs for p in required_params]):
            raise RuntimeError("Missing parameter in sweep_params; double check required param list.")

        self.params = {}
        self.ctrl = None
        self.idx = -1
        self.params.update(kwargs)

        def min_jerk_fn(f0, f1, n_dds):
            df = f1 - f0
            c = np.zeros([6, n_dds])
            c[0, :] = f0
            c[3, :] = df * 10
            c[4, :] = df * -15
            c[5, :] = df * 6

            return c

        def linear_amp_fn(a0, a1, n_dds):
            c = np.zeros([4, n_dds])
            c[0, :] = a0
            c[1, :] = a1 - a0

            return c

        # Freq poly fn
        self.f_gain = 0.99  # Recommend < 1 to avoid rounding problem.
        self.f_fn = min_jerk_fn

        # Amplitude 3rd order poly fn
        self.a_gain = 0.99  # Recommend < 1 to avoid rounding problem.
        self.a_fn = linear_amp_fn

        # Power ramp fn
        self.p_gain = 0.99  # Keep this = 0.99. If changed, recalibrate the laser power regulation!
        # Recommend < 1 to avoid rounding problem.
        self.p_fn = linear_amp_fn

    def init_buffers(self, ctrl, idx):
        self.ctrl = ctrl 
        self.idx = idx

        self.parser_row = BufferParser(ctrl.row_buff, idx, ctrl.n_row_dds, self.f_fn, self.f_gain, self.a_fn, self.a_gain)
        self.parser_col = BufferParser(ctrl.col_buff, idx, ctrl.n_col_dds, self.f_fn, self.f_gain, self.a_fn, self.a_gain)
        # row gen is used for DC power regulation output, using a single DDS output (hardcoded in BufferParserPwr) 
        self.parser_pwr = BufferParserPwr(ctrl.row_buff, idx, self.p_fn, self.p_gain)

        self.update(**self.params)


    def update(self, **kwargs):
        """
        pad out all iterable kwargs to match the size we need based on how many row/col dds were specified during init.
        """
        n_tones_row = len(kwargs['f0_row'])
        n_tones_col = len(kwargs['f0_col'])

        for k in self.row_kwargs:
            if hasattr(kwargs[k], '__iter__'):
                kwargs[k] = np.pad(kwargs[k], (0, self.ctrl.n_row_dds-len(kwargs[k])), mode='constant', constant_values=0)
        for k in self.col_kwargs:
            if hasattr(kwargs[k], '__iter__'):
                kwargs[k] = np.pad(kwargs[k], (0, self.ctrl.n_col_dds-len(kwargs[k])), mode='constant', constant_values=0)

        self.ctrl.dur_row_buff[self.idx] = kwargs['dur_row']
        self.ctrl.dur_col_buff[self.idx] = kwargs['dur_col']
        sqrt_ntones_col = np.sqrt(n_tones_col)
        sqrt_ntones_row = np.sqrt(n_tones_row)
        self.parser_col.parse_move(kwargs['f0_col'], kwargs['f1_col'], kwargs['a0_col']/sqrt_ntones_col,
                                   kwargs['a1_col']/sqrt_ntones_col, kwargs['phase_col'])
        self.parser_row.parse_move(kwargs['f0_row'], kwargs['f1_row'], kwargs['a0_row']/sqrt_ntones_row,
                                   kwargs['a1_row']/sqrt_ntones_row, kwargs['phase_row'])
        self.parser_pwr.parse_move(kwargs['p0'], kwargs['p1'])


class TweezerController:
    """
    Interface to the RFSoC tweezer controller. Keeps track of Move objects on
    the control computer side, manages the underlying register buffer, and
    enables pushing real time data to the RFSoC. Some functionallity, such as
    pushing the initial move data generated with the `generate_tproc_state`
    method to the RFSoC, requires use of the labrad interface.

    Parameters
    ----------
    max_moves : int
        The maximum number of moves that the user anticipates needing accross all states. 
    n_row : int
        Number of tones for the row generator. 
    n_col : int
        Number of tones for the column generator. 
    """
    def __init__(self):

        self.rfsoc_ip = '10.0.1.8'
        self.rfsoc_socket_port = 50001
        self.NDDS = 32
        self.MEM_LENGTH = 256
        self.FMOD_MIN_ORDER = 1
        self.FMOD_MAX_ORDER = 5
        self.BFREQ = 18
        self.BAMP = 16
        self.dphi = 0.001373291015625
        self.NREG = 15
        self.fs = 430.08000000000004
        self.df = 0.001640625

        self.row = 2
        self.col = 3


    def init_buffers(self, max_moves, n_row, n_col):
        self.socket_open = False
        self.max_moves = max_moves
        self.n_row_dds = n_row
        self.n_col_dds = n_col
        #v2Scale_calibration = np.load('I:/thompsonlab/AMO/Daily/2308/230825/RFSoc_DC_calibration.npz')
        #self.tweezerPD_V2Scale = interp1d(v2Scale_calibration['voltage'], v2Scale_calibration['scale'])

        self.row_buff = np.zeros((self.NDDS * (self.max_moves) * (self.NREG + 1),), dtype=np.int32)
        self.col_buff = np.zeros((self.NDDS * (self.max_moves) * (self.NREG + 1),), dtype=np.int32)

        # Initialize the ch register for all elements in the buffer.  stride is
        # the total number of elements per DDS channel (+1 to keep NREG defn
        # consistent with Leo's usage)
        stride = self.NREG+1
        for move in range(max_moves):
            idx0 = move*stride*self.NDDS
            ch_buff_row = self.row_buff[idx0:(idx0+stride*self.NDDS)][::stride]
            addr_buff_row = self.row_buff[idx0:(idx0+stride*self.NDDS)][1::stride]
            ch_buff_row[:] = np.arange(self.NDDS)
            addr_buff_row[:] = move
            ch_buff_col = self.col_buff[idx0:(idx0+stride*self.NDDS)][::stride]
            addr_buff_col = self.col_buff[idx0:(idx0+stride*self.NDDS)][1::stride]
            ch_buff_col[:] = np.arange(self.NDDS)
            addr_buff_col[:] = move

        self.dur_row_buff = np.zeros((max_moves,), dtype=np.int32)
        self.dur_col_buff = np.zeros((max_moves,), dtype=np.int32)

        # global dict of all the moves, with keys corresponding to the move_idx.
        self.moves = {}
        # list that records the number of movers for each state.
        self.moves_per_state = []
        # list that keeps track of all the moves associated with a state.
        self.state_list = []
        # global counter that's incremented every time a Move object is instantiated.
        self.move_ctr = 0


    def append_state(self, move_list):
        """
        When the RFSoC receives a trigger it executes a specific 'state', which
        consists of several moves. A move is defined as a single sweep of all
        the tweezer tones.
        
        This method is used to append new states, composed of one or more Move
        objects, to the tweezer interface. Move parameters, such as the initial
        and final frequency, can me modified using the update_move method only
        after they have been added as part of a state.
        
        The order in which move objects are created is important and determines
        the order in which moves will be played. It additionally determines
        where in memory the move is stored, both locally and on the RFSoC, hence
        determining the execution order.

        Parameters
        ----------
        move_list : list
            A list of Move objects. 
        """
        self.state_list += [move_list]
        self.moves_per_state += [len(move_list)]
        for move in move_list:
            if move.idx in self.moves:
                raise RuntimeError("Move object in move_list was used twice/already used "
                                   "with a different state; this is not supported.")
            
            idx = self.alloc_move_idx()
            move.init_buffers(self, idx)
            self.moves[idx] = move

        state_idx = len(self.state_list) - 1
        return state_idx

    def update_move(self, idx, **kwargs):
        self.moves[idx].update(**kwargs)

    
    def allocate_blank_moves(self, n_moves):
        """
        Allocate a block of moves that are all initialized to zeros and append
        as a single state. This can be used for instances where you want to
        dynamically update moves by their index and need to pre-allocate a block of
        the address space.
        """

        # These are dummy parameters that are only for buffer allocation, and don't have real meaning.
        config = {'f0_row': np.array([0]), 'f1_row': np.array([0]), 'f0_col': np.array([0]), 'f1_col': np.array([0]),
                  'a0_row': np.array([0]), 'a1_row': np.array([0]), 'a0_col': np.array([0]), 'a1_col': np.array([0]),
                  'p0': np.array([0]), 'p1': np.array([0]), 'phase_row': np.array([0]), 'phase_col': np.array([0]),
                  'dur_row': 1, 'dur_col': 1}

        move_list = [Move(**config) for _ in range(n_moves)]
        self.append_state(move_list)
        move_indices = [move.idx for move in move_list]
        state_idx = len(self.state_list) - 1

        return state_idx, move_indices
    
    
    def open_socket(self):
        # if self.socket_open:
        #      print("Socket connection already open.")
        # else:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.connect((self.rfsoc_ip, self.rfsoc_socket_port))
        self.socket_open = True


    def send_data_socket(self, state_idx, n_moves, subsequent_state=-1, update_state_idx=True):
        """
        This method is used for selecting what will play next and updating DDS data on RFSoC.

        Parameters
        ----------
        state_idx : int
            Selects what state will be played next and pushes data associated
            with that state. The index is determined by the order in which this
            state was created by calling the append_state method.
        n_moves : int
            Number of moves that should be executed. This enables restricting
            execution to only the first n_moves moves that were added using the
            append_state method. The primary use case for this is rearrangement:
            by allocating the maximum number of moves one would like to execute
            for a single trigger, the state can be re-run with a different
            subset of n_moves with frequency/amplitude data dynamically re-written. 
        subsequent_state : int, optional
            Sets the state that the RFSoC will run if there's an additional
            trigger after the state specified by state_idx has finished
            executing. If omitted, it will simply execute the next state in the
            order they were added using append_state.
        """
        # index of the first move in this state
        move_idx = self.state_list[state_idx][0].idx
        # Initial addr and length in terms for the complete parameter buffer 
        addr = move_idx * (self.NREG + 1) * self.NDDS
        length = n_moves * (self.NREG + 1) * self.NDDS

        # header specifies state index, global move index, number of moves, and
        # next state that will be executed if two triggers are received without
        # an interleaved send_socket_data
        if not update_state_idx:
            state_idx = -1
        data = pack('hhhh', state_idx, move_idx, n_moves, subsequent_state)

        self.socket.sendall(data)
        # addr here corresponds to the first param in the data buffer of move with index = move_idx. 
        self.socket.sendall(memoryview(self.row_buff)[addr:(addr + length)])
        self.socket.sendall(memoryview(self.col_buff)[addr:(addr + length)])
        self.socket.sendall(memoryview(self.dur_row_buff)[move_idx:(move_idx + n_moves)])
        self.socket.sendall(memoryview(self.dur_col_buff)[move_idx:(move_idx + n_moves)])


    def generate_tproc_states(self):
        """
        This method should be executed after the user has finished adding all
        states/moves. It returns data formatted to be sent to RFSoC via the
        run_exp or config_exp_internal labrad function, which will generate and
        load the tproc program.
        """
        tproc_states = []
        move_idx = 0
        for n_moves in self.moves_per_state:
            dur_list_row = self.dur_row_buff.tolist()[move_idx:move_idx+n_moves]
            dur_list_col = self.dur_col_buff.tolist()[move_idx:move_idx+n_moves] 

            tproc_states += [{
                'len': n_moves,
                'dur_list_row': dur_list_row,
                'dur_list_col': dur_list_col
            }]
            move_idx += n_moves

        data = pickle.dumps(
            {
                'tproc_states': tproc_states,
                'max_moves': self.max_moves
            }
        )
        return data
    

    def alloc_move_idx(self):
        if self.move_ctr >= self.MEM_LENGTH:
            raise RuntimeError("Exceeding the memory length; the maximum number of moves you can add is %i.")
        move_idx = self.move_ctr
        self.move_ctr += 1
        return move_idx