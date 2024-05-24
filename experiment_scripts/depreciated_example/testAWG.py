
if __name__ == '__main__':
    import labrad
    from labrad.units import WithUnit
    import timeit
    import numpy as np
    cxn = labrad.connect()

    awg = cxn.keysight_awg

    gate_list = []
    for i in range(30):
        phase = np.random.randint(0,91)
        gate = np.random.randint(0,3)
        if gate==0:
            gate_list.append([WithUnit(i*20,'us'),WithUnit(20,'us'),"phiphi_0_2_1_1"])
        elif gate==1:
            gate_list.append([WithUnit(i*20,'us'),WithUnit(20,'us'),"sigma_"+str(phase)])
        else:
            gate_list.append([WithUnit(i*20,'us'),WithUnit(20,'us'),"blank"])
            
    start = timeit.default_timer()

    time = awg.compile_gates(2,WithUnit(0.1,"V"),1,gate_list)
    stop = timeit.default_timer()
    print(time)
    print('Time: ', stop - start)