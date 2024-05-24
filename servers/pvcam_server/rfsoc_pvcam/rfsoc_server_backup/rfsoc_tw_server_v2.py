import sys
# sys.path.insert(0, '../qick_14e9b55/qick_lib/')
sys.path.insert(0, '../qick_edd1210/qick_lib/')

from qick import *
from qick.qick import *

from qick_amo_v4 import *
import _pickle as cPickle
from labrad.server import LabradServer, setting
import numpy as np 
import threading
import socket
from struct import unpack
import select
import time 


class TprocProgramSingle(QickProgram):
    def __init__(self, soccfg, cfg):
        super().__init__(soccfg)
        self.soccfg = soccfg
        self.cfg = cfg 
        
        p = 1
        r_addr = 1
        r_dur = 2
        r_ctrl = 3

        self.regwi(p, r_addr, cfg['addr']) 
        self.regwi(p, r_dur, self.soccfg.us2cycles(cfg['dur']))
        self.regwi(p, r_ctrl, (cfg['qsel'] << 8) + cfg['phrst']) # qsel | ctrl
        self.synci(200) 

        self.set(self.cfg['row_gen'], p, r_addr, r_dur, r_ctrl, 0, 0, 0)
        self.set(self.cfg['col_gen'], p, r_addr, r_dur, r_ctrl, 0, 0, 0)     
 
    def run(self, soc, load_pulses=True):
        self.config_readouts(soc)
        self.config_bufs(soc)
        
        if load_pulses:
            self.load_pulses(soc)

        self.config_gens(soc)
        self.load_program(soc, reset= True)
    
        soc.start_src('internal')
        soc.tproc.start()
        
        
class TprocProgramExt(QickProgram): 
    """
    Specification
    -------------

    This tproc program is implemented as a state machine. 
    
    Data that defines what happens when the next input trigger is received:
        * m_state tproc memory location -- the index of the next state to be
        played. This is initialized to 0, but can be overwritten using the
        socket interface.
        * m_next_state memory location -- the next state that will be executed if
        there are two consecutive triggers. This will automatically be
        incremented by +1 just before the state exits, but the socket interface
        provides an opportunity to overwrite this before the next trigger. 
        * n_moves_lookup memory location -- number of moves to make for the next
        trigger; which memory location is checked is determined by m_state. Just
        like with other parameters, pushing data via the socket interface
        updates this for the relevant state.  
    
    This enables dividing the program into a 'static' and 'dynamic' portion,
    where the static portion is pre-programmed and allows for multiple triggers
    whereas the dynamic part can be written using real-time operations. While
    somewhat articfical, this distinction is necessary since if everything is
    pre-programmed using unique states, it's easy to run out of program memory.
    """
    def __init__(self, soccfg, cfg):
        super().__init__(soccfg)
        self.soccfg = soccfg
        self.cfg = cfg
        self.states = cfg['states']

        self.m_state = 0
        self.m_next_state = 1

        # addr_lookup contains the address of the first step in each state
        self.addr_lookup = np.cumsum([0] + [s['len'] for s in self.states])  
        
        # dur_idx_lookup_* points to the location in memory containing the
        # up-to-date dur value for the first step in each state. Ditto for
        # n_step_idx_lookup.
        # NOTE: if these locations are changed you must update the idx_calc
        # method of RFSoCProgramServer, since these locations are hard-coded
        # and can be globally updated via idx_calc.  
        self.dur_idx_lookup_row = np.cumsum([0] + [s['len'] for s in self.states]) + 2  # +2 offset due to m_state and m_next_state
        self.dur_idx_lookup_col = np.cumsum([0] + [s['len'] for s in self.states]) + 2 + cfg['max_moves']
        self.n_moves_idx_lookup = np.arange(len(self.states)) + 2 + 2 * cfg['max_moves']
        # The memory buffer should be arranged like: [state, next_state, max_moves x (durations for row movements), max_moves x (durations for col movements), *(list of n_moves)]

        p = 1
        r_addr = 1
        r_ctrl = 2
        r_state = 3
        r_moves_idx = 4
        r_moves = 5
        r_dur_idx_row = 6
        r_dur_idx_col = 7
        r_dur_row = 8
        r_dur_col = 9
        r_work = 10
        r_state_idx = 11
        r_work2 = 12

        # self.waiti(p, 0)
        self.memri(p, r_state, self.m_state)

        #self.regwi(p, r_phrst, 0)
        #self.regwi(p, r_ctrl, (2 << 8))
        #self.math(p, r_ctrl, r_ctrl, '+', r_phrst)
        self.regwi(p, r_ctrl, int(((self.cfg['qsel']) << 8) + ((self.cfg['sat']) << 1) + self.cfg['phrst'])) 

        # give processor some time to configure pulses
        self.synci(self.soccfg.us2cycles(cfg['trg_wait']))  

        for state_idx in range(cfg['nstates']):
            self.regwi(p, r_state_idx, state_idx)
            self.condj(p, r_state, '==', r_state_idx, "STATE%i_JMP" % state_idx)
        
        for state_idx in range(cfg['nstates']):
            self.label("STATE%i_JMP" % state_idx)            

            # write r_addr value and the memory location for r_dur and r_moves specific to state_idx
            self.regwi(p, r_addr, self.addr_lookup[state_idx]) 
            self.regwi(p, r_dur_idx_row, self.dur_idx_lookup_row[state_idx])
            self.regwi(p, r_dur_idx_col, self.dur_idx_lookup_col[state_idx])

            self.regwi(p, r_moves_idx, self.n_moves_idx_lookup[state_idx])

            self.memr(p, r_moves, r_moves_idx)
            # Decrement r_moves by one, since stop condition is r_moves==0 checked only after set command is executed.
            self.mathi(p, r_moves, r_moves, '-', 1)
            
            self.label("LOOP%i" % state_idx)
            self.memr(p, r_dur_row, r_dur_idx_row)
            self.memr(p, r_dur_col, r_dur_idx_col)

            #self.regwi(p, r_ctrl, (2 << 8))
            #self.math(p, r_ctrl, r_ctrl, '+', r_phrst)
            
            self.trigger(pins=[0], t=0)
            # we don't need the phase reset since the phases are random right now
            self.set(self.cfg['row_gen'], p, r_addr, r_dur_row, r_ctrl, 0, 0, 0)
            self.set(self.cfg['col_gen'], p, r_addr, r_dur_col, r_ctrl, 0, 0, 0)

            # increment r_addr and lookup location for r_dur_* as we loop through moves
            self.mathi(p, r_addr, r_addr, '+', 1) 
            self.mathi(p, r_dur_idx_row, r_dur_idx_row, '+', 1)
            self.mathi(p, r_dur_idx_col, r_dur_idx_col, '+', 1)

            # make sure r_dur_row contains max(r_dur_row, r_dur_col) for sync below
            self.condj(p, r_dur_row, '>=', r_dur_col, "DUR%i_JMP" % state_idx)
            self.mathi(p, r_dur_row, r_dur_col, '+', 0)
            self.label("DUR%i_JMP" % state_idx)

            # dur index = 0 corresponds to 1 quantization cycle in DDS, so add
            # one to calculate corresponding sync time
            self.mathi(p, r_dur_row, r_dur_row, '+', 1) 
            self.mathi(p, r_dur_row, r_dur_row, '*', int(self.cfg['dds2tproc_cycles'])) 
            
            self.sync(p, r_dur_row)
            self.loopnz(p, r_moves, "LOOP%i" % state_idx)
            self.condj(p, 0, '==', 0, 'END_JMP')

        self.label('END_JMP')

        self.memri(p, r_work, self.m_next_state)
        self.regwi(p, r_work2, len(self.states))
        self.condj(p, r_work, '<', r_work2, 'RST_r_work')
        self.regwi(p, r_work, 0)
        self.label('RST_r_work')
        
        self.memwi(p, r_work, self.m_state)
        self.mathi(p, r_work, r_work, '+', 1)
        self.memwi(p, r_work, self.m_next_state)

        
    def run(self, soc, load_pulses=True, mode='external'):
        """
        Execute the pulse sequence
        """
        self.config_readouts(soc)
        self.config_bufs(soc)
        
        if load_pulses:
            self.load_pulses(soc)
        self.config_gens(soc)
        self.load_program(soc, reset=True)

        soc.tproc.single_write(self.m_state, 0)
        soc.tproc.single_write(self.m_next_state, 1)
        
#         for i in range(5):
#             print('mem ', i, ' = ', soc.tproc.single_read(i))
#         for i in range(258, 258 + 3):
#             print('mem ', i, ' = ', soc.tproc.single_read(i))
#         for i in range(258 + 256, 258 + 256 + 3):
#             print('mem ', i, ' = ', soc.tproc.single_read(i))

        soc.start_src(mode)
        if mode=='internal':
            soc.tproc.start()


class RFSoCProgramServer(LabradServer):
    name = 'rfsoc_tw_server'
    
    def initServer(self):
        # hard coded generator numbers for row and col specific to this firmware
        self.row_gen_id = 2
        self.col_gen_id = 3

        self.rfsoc_ip = '10.0.1.8'
        self.sock_port = 50001
        self.sock_alive = False
        self.sock_select_timeout = 0.3
        self.load_bitstream()
        np.set_printoptions(threshold=sys.maxsize)
        self.block_exec = False
        
        return None
    
    def load_bitstream(self):
        self.soc = QickAmoSoc(bitfile='./qick_amo_v4.bit', force_init_clks=False)
        dac_locked = [self.soc.rf.dac_tiles[tile].PLLLockStatus == 2 for tile in self.soc.dac_tiles]
        adc_locked = [self.soc.rf.adc_tiles[tile].PLLLockStatus == 2 for tile in self.soc.adc_tiles]

        if all(dac_locked + adc_locked):
            print("RFSoC initialized and all DACs/ADCs locked")
        else: 
            print("RFSoC DACs/ADCs unlocked")
        
        self.row_gen = self.soc.gens[self.row_gen_id]
        self.col_gen = self.soc.gens[self.col_gen_id]
        
    @setting(1)
    def reset_RFSoc(self, c):
        self.load_bitstream()
        
    
    @setting(11, pdata='y')
    def run_exp(self, c, pdata):
        data = cPickle.loads(pdata)
        self.states = data['tproc_states']
        if self.max_moves != data['max_moves']:
            raise RuntimeError('The max_moves in the tweezer controller (=%d) is not equal to the max_moves in the RFSoC server (=%d)!' % (data['max_moves'], self.max_moves))
        config = {
            'max_moves': self.max_moves,
            'states' : self.states,
            'nstates' : len(self.states),
            'qsel' : 2,
            'phrst' : 0,
            'sat' : 1,
            'trg_wait' : 0.5, # [us] wait after trig before executing the move; should be at least a few hundred ns 
            'row_gen' : self.row_gen_id,
            'col_gen' : self.col_gen_id, 
            # FIXME: double check exact time quant value... 
            'dds2tproc_cycles' : 3675, # 10.5 us/0.0028571714288571455 us ~3675, round up so tproc always takes a bit longer
            }
        time.sleep(50e-3)
        prog = TprocProgramExt(self.soc, config)
        prog.config_all(self.soc)
        prog.run(self.soc, mode='external')
        
        self.prog = prog
        print(prog)
        return None
    
        
    @setting(13, pdata='y')    
    def run_exp_internal(self, c, pdata='y'):
        data = cPickle.loads(pdata)
        self.states = data['tproc_states']
        if self.max_moves != data['max_moves']:
            raise RuntimeError('The max_moves in the tweezer controller (=%d) is not equal to the max_moves in the RFSoC server (=%d)!' % (data['max_moves'], self.max_moves))
        config = {
            'max_moves': self.max_moves,
            'states' : self.states,
            'nstates' : len(self.states),
            'qsel' : 2,
            'phrst' : 0,
            'sat' : 1,
            'trg_wait' : 0.5, # [us] wait after trig before executing the move; should be at least a few hundred ns 
            'row_gen' : self.row_gen_id,
            'col_gen' : self.col_gen_id, 
            # FIXME: double check exact time quant value... 
            'dds2tproc_cycles' : 3675, # 10.5 us/0.0028571714288571455 us ~3675, round up so tproc always takes a bit longer
            }
#         time.sleep(0.05)
        prog = TprocProgramExt(self.soc, config)
        self.prog = prog
        self.prog.config_all(self.soc)
        time.sleep(0.002)
        while self.block_exec:
            print("Waiting on block_exec to lift; is your socket data transfer stuck?")
            time.sleep(0.002)
            
        self.prog.run(self.soc, mode='internal')
        return None
        

    @setting(14, returns='y')
    def get_cfg(self, c):
        cfg = {
        'NDDS' : self.row_gen.NDDS,
        'MEM_LENGTH' : self.row_gen.MEM_LENGTH,
        'FMOD_MIN_ORDER' : self.row_gen.FMOD_MIN_ORDER,
        'FMOD_MAX_ORDER' : self.row_gen.FMOD_MAX_ORDER,
        'BFREQ' : self.row_gen.BFREQ,
        'BAMP' : self.row_gen.BAMP,
        'dphi' : self.row_gen.dphi,
        'NREG' : self.row_gen.NREG,
        }
        cfg.update(self.row_gen.cfg)
        pcfg = cPickle.dumps(cfg)

        return pcfg
    
    @setting(15)
    def get_ctr(self,c):
        return self.prog.get_ctr()
    
    @setting(19)
    def get_reset(self,c):
        return self.prog.get_reset()
    
    def parse_socket_data(self, conn, buff, addr, read_len, bytes_remaining):
        
        view = memoryview(buff)[addr:(addr+read_len)]
        while bytes_remaining:
            nbytes = 0
            nbytes = conn.recv_into(view, bytes_remaining) 
            view = view[int(nbytes/4):]
            # print('size of the emty buffer in bytes:', 4*len(view.tolist()))
            bytes_remaining -= nbytes


    def socket_server(self):
        self.socket_list = [self.server]
        self.sock_alive = True
        print('socket is running')
        while self.sock_alive:
            t0 = time.time()
            read_socks, write_socks, error_socks = select.select(self.socket_list, [], [], self.sock_select_timeout)
#             print("select.select time:", (time.time()-t0))
            # t0 = time.time()
            for s in read_socks:
                if s == self.server:
                    conn, _ = s.accept()
                    self.socket_list.append(conn)
                else:
                    # grab header data, corresponding to buffer address and length (number of moves per trigger).
                    try:
                        data = s.recv(8)
                    except socket.error as msg:
                        '-------------'
                        print('socket exception. msg:', msg)
                        data=False
                    
                    if data:
                        self.block_exec = True
                        t0 = time.time()
                        # header data received, contains first state idx, the
                        # absolute move index, number of moves for this state, 
                        # and the next state. To forgo overwriting next state, 
                        # use next_state = -1. 
                        state_idx, move_idx, n_moves, next_state = unpack('hhhh', data)
                        
                        # data is written to buffer objects for both row and col gen, consisting of 4 bytes per buffer elemnt (int 32) 
                        buff_idx = move_idx * (self.row_gen.NREG + 1) * self.row_gen.NDDS
                        len_total = n_moves * self.len_per_move

                        self.parse_socket_data(s, self.row_buff, buff_idx, len_total, len_total * 4)
                        self.parse_socket_data(s, self.col_buff, buff_idx, len_total, len_total * 4)
                        
                        self.row_gen.write_buff(self.row_buff)
                        self.col_gen.write_buff(self.col_buff)
                        
                        # Parse and write m_dur_lookup segments of tproc data memory. 
                        self.parse_socket_data(s, self.dur_buff_row, move_idx, n_moves, n_moves*4)
                        self.write_buff_dma(self.dur_buff_row, self.dur_buff_row_start, n_moves)
                        self.parse_socket_data(s, self.dur_buff_col, move_idx, n_moves, n_moves*4)
                        self.write_buff_dma(self.dur_buff_col, self.dur_buff_col_start, n_moves)
                        
                        # write m_state and m_next_state to data memory via DMA. 
                        if state_idx != -1:
                            # Write n_moves specific to current state. Each state has
                            # one entry in m_n_moves_lookup, so we can just add state
                            # to n_moves_buff_start. 
                            self.aux_buff[0] = n_moves
                            self.write_buff_dma(self.aux_buff, self.n_moves_buff_start + state_idx, 1)
                            
                            self.aux_buff[0] = state_idx
                            self.write_buff_dma(self.aux_buff, self.m_state_buff_start, 1)
                    
                        if next_state != -1:
                            self.aux_buff[0] = next_state
                            self.write_buff_dma(self.aux_buff, self.m_next_state_buff_start, 1) 
                            
                        self.block_exec = False
                    else:
                        s.close()
                        self.socket_list.remove(s)
        
    
    def write_buff_dma(self, buff, addr, length):
        self.soc.tproc.mem_mode_reg = 1
        self.soc.tproc.mem_addr_reg = addr
        self.soc.tproc.mem_len_reg = length
        # Start operation on block.
        self.soc.tproc.mem_start_reg = 1
        self.soc.tproc.dma.sendchannel.transfer(buff)
        self.soc.tproc.dma.sendchannel.wait()
        # Set block back to single mode.
        self.soc.tproc.mem_start_reg = 0
       

    def init_buffers(self):
        if self.row_gen.NREG != self.col_gen.NREG:
            raise RuntimeError("NREG for row and col generators does not match; it's assumed for buffer allocs these are equal.")
        if self.row_gen.NDDS != self.col_gen.NDDS:
            raise RuntimeError("NDDS for row and col generators does not match; it's assumed for buffer allocs these are equal.")
        
        self.n_reg = self.row_gen.NREG+1
        self.len_per_move = (self.row_gen.NREG+1)*self.row_gen.NDDS 

        m_state_idx, m_next_state_idx, dur_idx_row, dur_idx_col, n_moves_idx = self.idx_calc()
        self.m_state_buff_start = m_state_idx
        self.m_next_state_buff_start = m_next_state_idx
        self.dur_buff_row_start = dur_idx_row
        self.dur_buff_col_start = dur_idx_col
        self.n_moves_buff_start = n_moves_idx

        self.row_buff = allocate(shape=(self.len_per_move * self.max_moves,), dtype=np.int32)
        self.col_buff = allocate(shape=(self.len_per_move * self.max_moves,), dtype=np.int32)
        self.dur_buff_row = allocate(shape=(self.max_moves,), dtype=np.int32)
        self.dur_buff_col = allocate(shape=(self.max_moves,), dtype=np.int32)

        # alloc buffer for transferring aux data to tproc data memory. When
        # profiled, DMA was considerably faster than mmio via single_write. This
        # will be used for m_state, m_next_state and one element of n_moves_lookup.
        self.aux_buff = allocate(shape=(1,), dtype=np.int32)

        # Need to initialize the ch register for all elements in the buffer. 
        for move in range(self.max_moves):
            idx0 = move*self.n_reg*self.row_gen.NDDS
            
            ch_buff_row = self.row_buff[idx0:(idx0+self.n_reg*self.row_gen.NDDS)][::self.n_reg]
            addr_buff_row = self.row_buff[idx0:(idx0+self.n_reg*self.row_gen.NDDS)][1::self.n_reg]
            ch_buff_row[:] = np.arange(self.row_gen.NDDS)
            addr_buff_row[:] = move

            ch_buff_col = self.col_buff[idx0:(idx0+self.n_reg*self.col_gen.NDDS)][::self.n_reg]
            addr_buff_col = self.col_buff[idx0:(idx0+self.n_reg*self.col_gen.NDDS)][1::self.n_reg]
            ch_buff_col[:] = np.arange(self.col_gen.NDDS)
            addr_buff_col[:] = move

        self.dur_buff_row[:] = np.zeros(self.max_moves, dtype=np.int32)
        self.dur_buff_col[:] = np.zeros(self.max_moves, dtype=np.int32)

        
    def idx_calc(self):
        # Hard coded memory locations in tproc program. This function must be updated if the tproc memory
        # locations are changed! 
        m_state_idx = 0
        m_next_state_idx = 1
        # dur memory, +2 for m_state and m_next_state
        dur_idx_row = 2
        dur_idx_col = dur_idx_row + self.max_moves
        n_moves_idx = dur_idx_col + self.max_moves

        return (m_state_idx, m_next_state_idx, dur_idx_row, dur_idx_col, n_moves_idx)
    

    @setting(16, max_moves="i")
    def start_socket_server(self, c, max_moves):
        """
        Parameters
        ----------
        n_moves : int 
            The total number of moves to be executed. 
        """
        self.max_moves = max_moves
        
        if self.sock_alive:
            print('Socket server already running. Stop socket server and free buffers before re-intitializing.')
            self.sock_alive = False
            self.thread.join()
            for s in self.socket_list[::-1]:
                if s is not self.server:
                    s.close()
                    self.socket_list.remove(s)
            self.server.close()
            
            self.row_buff.freebuffer()
            self.col_buff.freebuffer()
            self.dur_buff_row.freebuffer()
            self.dur_buff_col.freebuffer()
            self.aux_buff.freebuffer()

#             self.init_buffers()
#             for s in self.socket_list:
#                 if s is not self.server:
#                     s.close()
#                     self.socket_list.remove(s)
#         else:
        print('Run socket server and alloc buffers')

        self.init_buffers()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.rfsoc_ip, self.sock_port))
        self.server.listen(5535) #65535
        self.thread = threading.Thread(target=self.socket_server)
        self.thread.start()

    @setting(17)
    def stop_socket_server(self, c):
        self.sock_alive = False
        self.thread.join()
        for s in self.socket_list[::-1]:
            s.close()
            self.socket_list.remove(s)
        self.row_buff.freebuffer()
        self.col_buff.freebuffer()
        self.dur_buff_row.freebuffer()
        self.dur_buff_col.freebuffer()
        self.aux_buff.freebuffer()

    @setting(18,'dummy',a='v')
    def dummy(self, c,a):
        print(1)

__server__ = RFSoCProgramServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
