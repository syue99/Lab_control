from labrad.units import WithUnit
class hardwareConfiguration(object):
    model = "M3201A"
    chassis = 1
    slot = 2
    channel_list = [1,2,3,4]
    channel_freq = [WithUnit(0,"MHz"),WithUnit(0,"MHz"),WithUnit(340,"MHz"),WithUnit(0,"MHz")]
    channel_amp = [WithUnit(0,"V"),WithUnit(0,"V"),WithUnit(340,"V"),WithUnit(0,"V")]
    channel_amp_thres = [0.95,0.95,1.5,1.5]
    channel_awg_amp_thres = [0.95,0.95,1.5,1.5]