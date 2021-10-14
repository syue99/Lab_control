import sys
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
from TraceListWidget import TraceList
from RecentFilesListWidget import RecentFilesListWidget
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
import itertools
from Dataset import Dataset
import queue

import numpy as np

import GUIConfig

class artistParameters():
    def __init__(self, artist, dataset, index, shown):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown
        self.last_update = 0 # update counter in the Dataset object
                             # only redraw if the dataset has a higher
                             # update count

class CameraWidgetGraph(QtWidgets.QWidget):
    def __init__(self, config, reactor, cxn = None, parent=None):
        super(CameraWidgetGraph, self).__init__(parent)
        from labrad.units import WithUnit as U
        self.U = U
        self.cxn = cxn
        self.pv = self.cxn.parametervault
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        self.name = config.name
        self.vline_name = config.vline
        self.vline_param = config.vline_param
        self.hline_name = config.hline
        self.hline_param = config.hline_param
        self.show_points = config.show_points
        self.grid_on = config.grid_on
        self.scatter_plot = config.scatter_plot

        self.dataset_queue = queue.Queue(config.max_datasets)

        self.live_update_loop = LoopingCall(self.update_figure)
        self.live_update_loop.start(0)

        self.colorChooser = itertools.cycle(GUIConfig.GLOBALCOLORS)
        self.fitColorChooser = itertools.cycle(GUIConfig.GLOBALFITCOLORS)
        self.initUI()

    @inlineCallbacks
    def initUI(self):
        self.tracelist = TraceList(self)
        self.pw = pg.ImageView(view = pg.ViewBox(enableMenu=True, lockAspect=4.0))
        self.height = 50
        self.data = np.ones((200,50))*255
        self.data[0,0] = 0
        #self.data = np.random.rand(200,100)
        #print(self.data)
        colors =[
            (0, 0, 0),
            (0, 255, 0),
            (255, 255, 255),
        ]
        cm = pg.ColorMap(pos=np.linspace(0.0, 1.0, 3), color=colors)
        self.pw.setColorMap(cm)
        #size
        #self.pw.resize(100,100)

        
        self.pw.setImage(self.data)
        # self._set_axes_font(20)
        #self._set_axes_label(self.dataset)
        if self.vline_name:
            self.inf = pg.InfiniteLine(movable=True, angle=90,
                                       label=self.vline_name + '{value:0.0f}',
                                       labelOpts={'position': 0.9,
                                                  'color': (200, 200, 100),
                                                  'fill': (200, 200, 200, 50),
                                                  'movable': True})
            init_value = yield self.get_init_vline()
            self.inf.setValue(init_value)
            self.inf.setPen(width=5.0)

        if self.hline_name:
            self.inf = pg.InfiniteLine(movable=True, angle=0,
                                       label=self.hline_name + '{value:0.0f}',
                                       labelOpts={'position': 0.9,
                                                  'color': (200, 200, 100),
                                                  'fill': (200, 200, 200, 50),
                                                  'movable': True})
            init_value = yield self.get_init_hline()
            self.inf.setValue(init_value)
            self.inf.setPen(width=5.0)
            
        self.pw2 = pg.PlotWidget()
        #size
        #self.pw2.resize(2,2)
        
        self.coords = QtGui.QLabel('')
        self.title = QtGui.QLabel(self.name)
        frame = QtGui.QFrame()
        splitter = QtGui.QSplitter()

        # reorganized layout for recent files
        leftSideWidget = QtWidgets.QWidget()
        leftSideVerticalBox = QtGui.QVBoxLayout()
        overallHbox = QtGui.QHBoxLayout()
        graphVbox = QtGui.QVBoxLayout()
        graphVbox.addWidget(self.title)
        graphVbox.addWidget(self.pw2)
        graphVbox.addWidget(self.pw)
        
        graphVbox.addWidget(self.coords)
        frame.setLayout(graphVbox)

        leftSideVerticalBox.addWidget(self.tracelist)
        #leftSideVerticalBox.setStretch(0, 1.4)

        
        searchBarlayout = QtWidgets.QHBoxLayout()
        self.searchInput = QtWidgets.QLineEdit()
        searchButton = QtWidgets.QPushButton('Filter')
        searchButton.clicked.connect(self.filter)
        searchBarlayout.addWidget(self.searchInput)
        searchBarlayout.addWidget(searchButton)
        leftSideVerticalBox.addLayout(searchBarlayout)

        self.recentFilesListWidget = RecentFilesListWidget(self)
        leftSideVerticalBox.addWidget(self.recentFilesListWidget)
        
        maxHeightLayout = QtWidgets.QHBoxLayout()
        self.maxHeightInput = QtWidgets.QLineEdit()
        maxHeightButton = QtWidgets.QPushButton('Change Max Height')
        maxHeightButton.clicked.connect(self.changeHeight)
        self.maxHeightInput.setText(str(self.height))
        maxHeightLayout.addWidget(self.maxHeightInput)
        searchButton.clicked.connect(self.filter)
        maxHeightLayout.addWidget(maxHeightButton)
        leftSideVerticalBox.addLayout(maxHeightLayout)

        leftSideWidget.setLayout(leftSideVerticalBox)
        splitter.addWidget(leftSideWidget)
        splitter.addWidget(frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        overallHbox.addWidget(splitter)
        self.setLayout(overallHbox)
        # end reorganizing

        self.tracelist.itemChanged.connect(self.checkboxChanged)


    def filter(self):
        self.recentFilesListWidget.filter(self.searchInput.text())

    def changeHeight(self):
        if(self.maxHeightInput.text()):
            try:
                self.height = int(self.maxHeightInput.text())
            except:
                pass
        print(self.height)
        print(self.pw.getView().getAspectRatio())
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    ds = params.dataset
                    index = params.index
                    current_update = ds.updateCounter
                    params.last_update = current_update
                    self.pw.setImage(self.process_data(ds.data))
                except: pass

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.filter()
            self.changeHeight()
        event.accept()

    def _set_axes_font(self, font_size):
        font = QtGui.QFont()
        font.setPixelSize(font_size)
        left_axis = self.pw.plotItem.getAxis("left")
        left_axis.tickFont = font
        left_axis.setWidth(font_size * 7)
        left_axis.setStyle(tickTextOffset=int(font_size/2))
        left_axis.setStyle(textFillLimits=[(0, 0.6), (2, 0.4),(4, 0.2), (6, 0.0)])
        bottom_axis = self.pw.plotItem.getAxis("bottom")
        bottom_axis.tickFont = font
        bottom_axis.setHeight(font_size * 2)
        bottom_axis.setStyle(tickTextOffset=int(font_size/2))
        bottom_axis.setStyle(textFillLimits=[(0, 0.6), (2, 0.4),(4, 0.2), (6, 0.0)])
    
    @inlineCallbacks    
    def set_axis_label(self,dataset):
        axis_labels = yield dataset.getAxesLabels()
        left_axis = self.pw.plotItem.getAxis("left")
        left_axis.setLabel(text=axis_labels[1])
        bottom_axis = self.pw.plotItem.getAxis("bottom")
        bottom_axis.setLabel(text=axis_labels[0])
       
    def getItemColor(self, color):
        color_dict = {}
        for hexColor in GUIConfig.GLOBALCOLORS:
            color_dict[hexColor] = QtGui.QColor(hexColor)
        for hexColor in GUIConfig.GLOBALFITCOLORS:
            color_dict[hexColor] = QtGui.QColor(hexColor)
        return color_dict[color]

    def update_figure(self):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    ds = params.dataset
                    index = params.index
                    current_update = ds.updateCounter
                    if params.last_update < current_update:
                        params.last_update = current_update
                        self.pw.setImage(self.process_data(ds.data))
                except:
                    pass
                x = np.linspace(0,len(ds.data)-1,len(ds.data))
                
                collapsed_data = np.sum(ds.data,axis=1)/len(ds.data)
                self.pw2.clear()
                line = self.pw2.plot(x, collapsed_data, symbol='o')


    def _check_artist_exist(self, ident):
        if ident in self.artists.keys():
            counter = 1
            while ident + str(counter) in self.artists.keys():
                counter += 1
            ident += str(counter)
        return ident

    def add_artist(self, ident, dataset, index, no_points = False):
        '''
        no_points is an override parameter to the global show_points setting.
        It is to allow data fits to be plotted without points
        '''
        if not no_points:
            new_color = next(self.colorChooser)
        else:
            new_color = next(self.fitColorChooser)
        ident = self._check_artist_exist(ident)

        self.artists[ident] = artistParameters('', dataset, index, True)
        self.tracelist.addTrace(ident, new_color)
        
        collapsed_data = np.sum(dataset.data,axis=1)/len(dataset.data)
        #print(collapsed_data)
        self.pw2.clear()
        line = self.pw2.plot(np.linspace(0,len(dataset.data)-1,len(dataset.data)), collapsed_data)



    def remove_artist(self, ident):
        try:
            artist = self.artists[ident].artist
            self.pw.data = None
            self.tracelist.removeTrace(ident)
            self.artists[ident].shown = False
            try:
                del self.artists[ident]
            except KeyError:
                pass
        except:
            print("remove artist failed")

    def display(self, ident, shown):
        try:
            artist = self.artists[ident].artist
            if shown:
                self.pw.data = self.process_data(self.artists[ident].dataset.data)
                self.artists[ident].shown = True
            else:
                #cameraWidget should allow only one graph at a time
                #self.pw.removeItem(artist)
                #self.legend.removeItem(ident)
                self.artists[ident].shown = False
        except KeyError:
            raise Exception('404 Artist not found')

    def checkboxChanged(self):
        for ident, item in self.traceFlist.trace_dict.items():
            try:
                if item.checkState() and not self.artists[ident].shown:
                    self.display(ident, True)
                if not item.checkState() and self.artists[ident].shown:
                    self.display(ident, False)
            except KeyError: # this means the artist has been deleted.
                pass

    def rangeChanged(self):
        lims = self.pw.viewRange()
        self.pointsToKeep =  lims[0][1] - lims[0][0]
        self.current_limits = [lims[0][0], lims[0][1]]

    @inlineCallbacks
    def add_dataset(self, dataset):
        try:
            self.dataset_queue.put(dataset, block=False)
        except queue.Full:
            remove_ds = self.dataset_queue.get()
            self.remove_dataset(remove_ds)
            self.dataset_queue.put(dataset, block=False)
        labels = yield dataset.getLabels()
        for i, label in enumerate(labels):
            self.add_artist(label, dataset, i)

        # process data, so that it grows vertically downwards
        #self.process_data(dataset.data)
        self.pw.setImage(self.process_data(dataset.data))
        # self.set_axis_label(dataset)
        
    def process_data(self, data):
        data = np.asarray(data)
        rows, cols = data.shape
        if rows < self.height:
            data = np.vstack((data, [[255] * cols for _ in range(self.height - rows)]))
        else:
            data = data[rows - self.height:]
        data = np.rot90(data, 1)
        return data

    @inlineCallbacks
    def remove_dataset(self, dataset):
        labels = yield dataset.getLabels()
        for label in labels:
            self.remove_artist(label)

    def set_xlimits(self, limits):
        self.pw.setXRange(limits[0], limits[1])
        self.current_limits = limits

    def set_ylimits(self, limits):
        self.pw.setYRange(limits[0],limits[1])

    def mouseMoved(self, pos):
        pnt = self.img.mapFromScene(pos)
        string = '(' + str(pnt.x()) + ' , ' + str(pnt.y()) + ')'
        self.coords.setText(string)

    @inlineCallbacks
    def get_init_vline(self):
        init_vline = yield self.pv.get_parameter(self.vline_param[0],
                                                 self.vline_param[1])
        returnValue(init_vline)

    @inlineCallbacks
    def get_init_hline(self):
        init_hline = yield self.pv.get_parameter(self.hline_param[0],
                                                 self.hline_param[1])
        returnValue(init_hline)

    @inlineCallbacks
    def vline_changed(self, sig):
        val = self.inf.value()
        param = yield self.pv.get_parameter(self.vline_param[0], self.vline_param[1])
        units = param.units
        val = self.U(val, units)
        yield self.pv.set_parameter(self.vline_param[0], self.vline_param[1], val)

    @inlineCallbacks
    def hline_changed(self, sig):
        val = self.inf.value()
        param = yield self.pv.get_parameter(self.hline_param[0], self.hline_param[1])
        units = param.units
        val = self.U(val, units)
        yield self.pv.set_parameter(self.hline_param[0], self.hline_param[1], val)
