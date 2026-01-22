import sys
import time
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtGui, QtWidgets

import numpy as np

from TraceListWidget import TraceList
sys.path.append("../../config")
import scriptscanner_config as sc_config

from twisted.internet.defer import inlineCallbacks, returnValue
from pyqt4_clients.connection import connection
from twisted.internet.defer import inlineCallbacks



class artistParameters():
    def __init__(self, artist, dataset, index, shown = False):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown
        self.last_update = 0  # update counter in the Dataset object
                              # only redraw if the dataset has a higher
                              # update count




class sequence_plotter_button_widget(QtWidgets.QWidget):
    def __init__(self, script_scanner_gui):
        super(sequence_plotter_button_widget, self).__init__()
        self.sc_gui  = script_scanner_gui
        self.cxn = self.sc_gui.cxn
        #self.pulse_/
        self.artist_ttl_channel= []
        self.artist_ao_channel = []
        self.artists = {}
        self.connect()
        self.setup_layout()
        

    @inlineCallbacks
    def connect(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        self.subscribedScriptScanner = False
        self.subscribedParametersVault = False
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()



    def setup_layout(self):
        # Create a QPushButton
        self.button = QtWidgets.QPushButton('Click me!', self)
        # Figure
        self.figure = Figure(figsize=(100,7.2), dpi=80, facecolor='k')
        self.plotWidget = FigureCanvas(self.figure)     
        
        #scrollbar
        self.scroll = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.axes2 = self.figure.subplots(nrows=1, sharex=True)
        self.axes2.cla()
        
        #tracelist
        self.tracelist = TraceList(self)

        # Connect the tracelist with the function checkbox chnaged
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        
        # Connect the button's clicked signal to a custom slot (function)
        self.button.clicked.connect(self.on_button_click)

        # Set up the layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.plotWidget)
        layout.addWidget(self.scroll)
        hlayout = QtWidgets.QHBoxLayout(self)
        hlayout.addWidget(self.button)
        hlayout.addWidget(self.tracelist)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        # add artist for the channel
        # Name, type(0 ttl, 1 AO), real channel, index for display or not
        # We will load from the config file in lab_control\config\scriptscanner_config.py
        for i in range(0,10):
            self.add_artist("TTL_"+str(i),0,i,0)
        for i in range(2):
            self.add_artist("AO_"+str(i),1,i,0)

#Other functions
    @inlineCallbacks
    def on_button_click(self, script):
        """Function called by the "Run" button."""
        try:
            selected_experiment = self.sc_gui.selected_experiment
            print(selected_experiment)
            self.returned_data =  yield self.get_data(selected_experiment)
            #print(self.returned_data[1][0])
            yield self.make_plot(self.returned_data)
        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print(e)            


    def make_plot(self, data):
        try:
        #Fred
        #recompile data into Cicero style, probably better to be a class later
        #ttk_data is 100ns bins, so this is xCoords for us bins
        #ao_data is 4us bins, we will normalize the ao_data time bin, ao time zone is 40 times larger
        # we only record xCoords where there is a change
        # we will combine the xCoords with TTL and AO, but the AO will listen to the Ao xCoords for displaying shapes
        # on the other hand, TTL data will follow the combined time zone
            ttl_data = data[0]
            
            if len(data[1])==0:
                ao_data = None
                ao_t_list = None

            else:
                ao_data = data[1]
                n_channel = self.artist_ao_channel
                ao_t_list = []
                ao_plot_list = []
                ao_t_list_2 = []
                ao_t_combined_list = []
                for channel in n_channel:
                    #we plan to further fix the ramp data into a line with better use of the roll function
                    #for now we just plot the linear changes
                    ao_t = np.where(np.abs(np.roll(ao_data[channel],1) - ao_data[channel])> 0.2)[0]
                    ao_plotArr = [ao_data[channel][j] for j in ao_t]
                    ao_t = ao_t*40
                    #print(ao_t)
                    ao_t_combined_list = np.unique(np.concatenate((ao_t_combined_list,ao_t)))
                    ao_t_list.append(ao_t)
                    ao_plot_list.append(ao_plotArr)

            xCoords = np.where(np.roll(ttl_data,1) != ttl_data)[0]
            xCoords = np.append(xCoords,len(ttl_data)-1)
            #now let's combine the two data
            xCoords = np.sort(np.unique(np.concatenate((ao_t_combined_list,xCoords)))).astype(int)
            #rewrite ao_t_list_2 to plot data:
            for t in ao_t_list:
                ao_t_list_2.append(np.where(np.in1d(xCoords,t))[0])
            #print(ao_t_list_2)
            plotArr = np.zeros([len(self.artist_ttl_channel), len(xCoords)])
            counter = 0
            #print([ttl_data[j] for j in xCoords])
            for i in self.artist_ttl_channel: 
                chMask = 2 ** i
                plotArr[counter] = [np.sign(chMask & ttl_data[j]) for j in xCoords]
                counter +=1
            #print(plotArr[0])
            xCoords = xCoords/10
            #print(plotArr[0])
            self.data = [plotArr, xCoords, ao_t_list_2, ao_plot_list]
            print(xCoords)
            self.plot_data(self.data[0],self.data[1],self.data[2],self.data[3])

        except self.Error as e:
            self.displayError(e.msg)
        except Exception as e:
            print(e)




    @inlineCallbacks
    def get_data(self, script):
        sc = yield self.cxn.get_server("ScriptScanner")
        ttl = yield self.cxn.get_server('finitedopulses')
        ao = yield self.cxn.get_server('aoserver')
        yield self.sc_gui.reloadExperiments()
        yield sc.new_experiment_sequence(script,context=self.context)
        #Wait for exp seq to complete, now a temp fix
        #use sc.finish_confirmed for the proper version
        time.sleep(0.5)
        ttl_data =  yield ttl.returndata()
        ao_data = yield ao.returndata()
        returnValue([ttl_data,ao_data])

#Use the artist class for selecting the channels to display
#Every time when artist channel changed, we will only redraw with the existing data
#You have to click the clcik me button for get-new data
    def add_artist(self, ident, datatype, index, shown):
        #select a new color
        #new_color = next(self.colorChooser)
        self.datatype = datatype
        self.artists[ident] = artistParameters(None, datatype, index)
        #self.pw.addItem(hist)
        self.tracelist.addTrace(ident, QtGui.QColor("#123456"))
        self.shown = shown
        if self.shown:
            if (self.datatype == 0):
                self.artist_ttl_channel.append(index)
            elif self.datatype ==1:
                self.artist_ao_channel.append(index)
            
    def checkboxChanged(self):
        for ident, item in self.tracelist.trace_dict.items():
            try:
                if item.checkState() and not self.artists[ident].shown:
                    self.artists[ident].shown = 1
                    if (self.artists[ident].dataset == 0):
                        self.artist_ttl_channel.append(self.artists[ident].index)
                        print(self.artist_ttl_channel)
                    elif (self.artists[ident].dataset == 1):
                        self.artist_ao_channel.append(self.artists[ident].index)
                        print(self.artist_ao_channel)
                    self.make_plot(self.returned_data)
                if not item.checkState() and self.artists[ident].shown:
                    self.artists[ident].shown = 0
                    if (self.artists[ident].dataset == 0):
                        self.artist_ttl_channel.remove(self.artists[ident].index)
                    elif (self.artists[ident].dataset == 1):
                        self.artist_ao_channel.remove(self.artists[ident].index)
                    self.make_plot(self.returned_data)
                    #self.display(ident, False)
            except KeyError:  # this means the artist has been deleted.
                pass


    def plot_data(self,ttl_data, t, ao_t = None, ao_data=None):
        self.max = len(t)
        numPlots = 0
        self.axes2.cla()
        for pulse in ttl_data:
            self.axes2.step(range(len(t)),pulse+1.5*numPlots-4,where='post',label="ttl "+str(self.artist_ttl_channel[numPlots]))
            self.axes2.fill_between(x= range(len(t)), y1=1.5*numPlots-4 ,y2=pulse+1.5*numPlots-4,step='post')
            numPlots+=1
        if ao_data != None:
            numPlots = 0
            for counter in range(len(ao_data)):
                self.axes2.step(ao_t[counter],ao_data[counter],where='post',label="ao "+str(self.artist_ao_channel[numPlots]))
                self.axes2.fill_between(x= ao_t[counter],y1=ao_data[counter],y2=0, alpha=0.3, step='post')#interpolate=True)
                numPlots+=1
        
        #self.axes2.plot(t,data)
        self.axes2.set_position([0.02, 0.15, 0.98, 0.7])
        #self.axes.set_position([0.02, 0.15, 0.88, 0.22])
        #self.axes.tick_params(axis='both', color='#ffffff', labelcolor='#ffffff')
        #self.axes2.yaxis.tick_left()
        #self.axes2.set_yticklabels([])
        self.axes2.set_xticks(range(len(t)))
        self.axes2.set_xticklabels([str(i) for i in t])
#If there is no ao data, we will not show yticks of voltage
#Otherwise we will show voltage so that one have a reference for the AO channels
        try:
            #this line could be slow though
            yrange = np.append([0],np.max(ao_data))
            self.axes2.set_yticks(yrange)
        except:
            self.axes2.set_yticks([])
        self.axes2.set_xlabel("time (us)",color='w')
        self.axes2.set_ylabel("Voltage (V)",color='w')
        #self.axes2.set_xticks(np.arange(len(t)),[str(i) for i in t])
        self.axes2.tick_params(axis='both', color='#ffffff', labelcolor='#ffffff')
        self.axes2.grid(color='lightgray', linewidth=.5, linestyle=':')
        self.axes2.legend()
        #self.axes.grid(color='lightgray', linewidth=.5, linestyle=':')
        #self.axes2.yaxis.tick_right()
        #self.axes.autoscale_view()
        self.axes2.autoscale_view()
        #self.axes.set_facecolor('#041105')
        self.axes2.set_facecolor('#041105')
        
        #self.axes.set_xticklabels([mdates.num2date(d).strftime('%b-%d') for d in x])
        #self.axes.set_xticklabels([mdates.num2date(d).strftime('%Y-%m-%d') for d in x])
        #self.axes2.set_xticklabels([mdates.num2date(d).strftime('%Y-%m-%d') for d in x])
        self.plotWidget.draw()
        self.step = 1
        self.setupSlider()


    def setupSlider(self):
        #self.lims = np.array(self.axes2.get_xlim())
        self.lims = np.array([-0.5,25])
        print("limit"+str(self.lims))
        self.scroll.setPageStep(self.step)
        self.scroll.actionTriggered.connect(self.update)
        self.update()

    def update(self, evt=None):
        r = self.scroll.value() /100 *(self.max/25.5-1+0.1)
        #print(r,self.max)
        l1 = self.lims[0] + r * np.diff(self.lims)
        l2 = l1 + np.diff(self.lims) * self.step
        self.axes2.set_xlim(l1, l2)
        #self.axes.set_xlim(l1, l2)
        #print(self.scroll.value(), l1, l2)
        self.figure.canvas.draw_idle()
