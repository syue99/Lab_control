import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMainWindow,QVBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
import datetime
from matplotlib.dates import num2date, date2num
#from mpl_finance import candlestick_ochl as candlestick
import numpy as np
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import pylab as pl
from TraceListWidget import TraceList

import labrad
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


class sequence_plotter_widget(object):
    artist_channel= []
    artists = {}
    def add_artist(self, ident, dataset, index, shown):
        #select a new color
        #new_color = next(self.colorChooser)
        self.dataset = dataset
        self.artists[ident] = artistParameters(None, dataset, index)
        #self.pw.addItem(hist)
        self.tracelist.addTrace(ident, QtGui.QColor("#123456"))
        self.shown = shown
        if self.shown:
            self.artist_channel.append(dataset)



    def setup_code_serarch(self, MainWindow):
        self.tracelist = TraceList(self)
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 340)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")


        
        #plot graph
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(17, 10, 1000, 300))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.figure = Figure(figsize=(100,7.2), dpi=80, facecolor='k')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.draw()

        #scroobar
        self.scroll = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.axes, self.axes2 = self.figure.subplots(nrows=2, sharex=True)


        self.verticalLayout.addWidget(self.canvas)
        self.verticalLayout.addWidget(self.scroll)
        self.verticalLayout.addWidget(self.tracelist)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        for i in range(0,10):
            self.add_artist(str(i),i,i,0)

    def checkboxChanged(self):
        for ident, item in self.tracelist.trace_dict.items():
            try:
                if item.checkState() and not self.artists[ident].shown:
                    self.artist_channel.append(self.artists[ident].dataset)
                    self.artists[ident].shown = 1
                    print(self.artist_channel)
                    ui.plot_data(*ui.get_data())
                if not item.checkState() and self.artists[ident].shown:
                    self.artists[ident].shown = 0
                    self.artist_channel.remove(self.artists[ident].dataset)
                    ui.plot_data(*ui.get_data())
                    #self.display(ident, False)
            except KeyError:  # this means the artist has been deleted.
                pass


    def get_data(self, cxn=None):
        if cxn == None:
            self.cxn = labrad.connect()
        else:
            self.cxn = cxn


        self.data = self.cxn.finitedopulses.returnData()

        #Fred
        #recompile data into Cicero style, probably better to be a class later
        # data is 100ns bins, so this is xCoords for us bins
        # we only record xCoords where there is a change
        xCoords = np.where(np.roll(self.data,1) != self.data)[0]
        xCoords = np.append(xCoords,len(self.data)-1)
        plotArr = np.zeros([len(self.artist_channel), len(xCoords)])
        counter = 0
        for i in self.artist_channel: 
            chMask = 2 ** i
            plotArr[counter] = [np.sign(chMask & self.data[j]) for j in xCoords]
            counter +=1
        xCoords = xCoords/10
        #print(plotArr,xCoords)
        return plotArr, xCoords

    def plot_data(self,data,t):
        self.max = len(t)
        numPlots = 0
        #print(t)
        self.axes2.cla()
        for pulse in data:
            #print(pulse)
            self.axes2.step(range(len(t)),pulse+1.5*numPlots,where='post',label=self.artist_channel[numPlots])
            self.axes2.fill_between(x= range(len(t)), y1=1.5*numPlots ,y2=pulse+1.5*numPlots,step='post')
            #self.axes2.plot(t,np.tile(pulse+1.5*numPlots,1),label=numPlots)
            numPlots+=1
        self.axes2.set_position([0.02, 0.37, 0.88, 0.6])
        #self.axes.set_position([0.02, 0.15, 0.88, 0.22])
        #self.axes.tick_params(axis='both', color='#ffffff', labelcolor='#ffffff')
        #self.axes.yaxis.tick_right()
        self.axes2.set_yticklabels([])
        self.axes2.set_xticks(range(len(t)))
        self.axes2.set_xticklabels([str(i) for i in t])
        self.axes2.set_xlabel("time (us)",color='w')
        #self.axes2.set_xticks(np.arange(len(t)),[str(i) for i in t])
        self.axes2.tick_params(axis='both', color='#ffffff', labelcolor='#ffffff')
        self.axes2.grid(color='lightgray', linewidth=.5, linestyle=':')
        self.axes2.legend()
        #self.axes.grid(color='lightgray', linewidth=.5, linestyle=':')
        self.axes2.yaxis.tick_right()
        #self.axes.autoscale_view()
        self.axes2.autoscale_view()
        #self.axes.set_facecolor('#041105')
        self.axes2.set_facecolor('#041105')
        
        #self.axes.set_xticklabels([mdates.num2date(d).strftime('%b-%d') for d in x])
        #self.axes.set_xticklabels([mdates.num2date(d).strftime('%Y-%m-%d') for d in x])
        #self.axes2.set_xticklabels([mdates.num2date(d).strftime('%Y-%m-%d') for d in x])
        self.canvas.draw()
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 246, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.step = 1
        self.setupSlider()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

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



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = sequence_plotter_widget()
    ui.setup_code_serarch(MainWindow)
    ui.plot_data(*ui.get_data())
    MainWindow.show()
    sys.exit(app.exec_())