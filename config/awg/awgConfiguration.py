from labrad.units import WithUnit
class hardwareConfiguration(object):
    model = "M3202A"
    chassis = 0
    slot = 2
    channel_list = [1,2,3,4]
    channel_freq = [WithUnit(0,"MHz"),WithUnit(0,"MHz"),WithUnit(204,"MHz"),WithUnit(0,"MHz")]
    channel_amp = [WithUnit(0,"V"),WithUnit(0,"V"),WithUnit(0,"V"),WithUnit(0,"V")]
    channel_amp_thres = [1.07,1.51,1.51,1.51]
    channel_awg_amp_thres = [1.51,1.51,1.51,1.51]
    coherent_channel = 2 #usually this value is 2 for coherent raman gate operation. we change it to 3 for microwave spin echo
