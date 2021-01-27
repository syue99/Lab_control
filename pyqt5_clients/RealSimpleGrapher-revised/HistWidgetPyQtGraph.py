import sys
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
from TraceListWidget import TraceList
from RecentFilesListWidget import RecentFilesListWidget
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
import itertools
import queue
import GUIConfig

class artistParameters():
    def __init__(self, artist, dataset, index, shown):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown
        self.last_update = 0  # update counter in the Dataset object
                              # only redraw if the dataset has a higher
                              # update count

                              
class Hist_PyQtGraph(QtWidgets.QWidget):
    def __init__(self, config, reactor, cxn=None, parent=None):
        super(Hist_PyQtGraph, self).__init__(parent)
        self.cxn = cxn
        self.pv = self.cxn.parametervault
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        self.name = config.name
        self.vline_name = config.vline
        self.vline_param = config.vline_param

        self.opacityhex = 'B2'
        
        self.dataset_queue = queue.Queue(config.max_datasets)

        self.live_update_loop = LoopingCall(self.update_figure)
        self.live_update_loop.start(0)

        self.colorChooser = itertools.cycle([color + self.opacityhex for color in GUIConfig.GLOBALCOLORS])
        self.initUI()

    @inlineCallbacks
    def initUI(self):
        self.tracelist = TraceList(self)
        self.pw = pg.PlotWidget()
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
        self.coords = QtWidgets.QLabel('')
        self.title = QtWidgets.QLabel(self.name)
        frame = QtGui.QFrame()
        splitter = QtGui.QSplitter()

        # reorganized layout for recent files
        leftSideWidget = QtWidgets.QWidget()
        leftSideVerticalBox = QtGui.QVBoxLayout()
        overallHbox = QtGui.QHBoxLayout()
        graphVbox = QtGui.QVBoxLayout()
        graphVbox.addWidget(self.title)
        graphVbox.addWidget(self.pw)
        graphVbox.addWidget(self.coords)
        frame.setLayout(graphVbox)

        leftSideVerticalBox.addWidget(self.tracelist)
        leftSideVerticalBox.setStretch(0, 1.4)
        leftSideVerticalBox.addWidget(RecentFilesListWidget(self))
        leftSideVerticalBox.setStretch(0, 1)
        
        leftSideWidget.setLayout(leftSideVerticalBox)
        splitter.addWidget(leftSideWidget)
        splitter.addWidget(frame)

        overallHbox.addWidget(splitter)
        self.setLayout(overallHbox)
        # end reorganizing

        #self.legend = self.pw.addLegend()
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.plot([],[])
        vb = self.pw.plotItem.vb
        self.img = pg.ImageItem()
        vb.addItem(self.img)
        if self.vline_name:
            vb.addItem(self.inf)
            self.inf.sigPositionChangeFinished.connect(self.vline_changed)

        self.pw.scene().sigMouseMoved.connect(self.mouseMoved)
        self.pw.sigRangeChanged.connect(self.rangeChanged)

    def getItemColor(self, color):
        color_dict = {}

        for hexColor in GUIConfig.GLOBALCOLORS:
            color_dict[hexColor + self.opacityhex] = QtGui.QColor(hexColor + self.opacityhex)
        return color_dict[color + self.opacityhex]

    def update_figure(self):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    ds = params.dataset
                    index = params.index
                    current_update = ds.updateCounter
                    if params.last_update < current_update:
                        x = ds.data[:,0]
                        x = list(x) + [x[-1] + 1]
                        y = ds.data[:,index+1]
                        params.last_update = current_update
                        params.artist.setData(x,y)
                except: pass

    def add_artist(self, ident, dataset, index, no_points = False):
        '''
        no_points is an override parameter to the global show_points setting.
        It is to allow data fits to be plotted without points
        '''
        new_color = next(self.colorChooser)
        hist = pg.PlotCurveItem([0,1],[1], stepMode=True, fillLevel=0, brush=new_color, pen=None)
        self.artists[ident] = artistParameters(hist, dataset, index, True)
        self.pw.addItem(hist)
        self.tracelist.addTrace(ident, new_color)

    def remove_artist(self, ident):
        try:
            artist = self.artists[ident].artist
            self.pw.removeItem(artist)
            self.tracelist.removeTrace(ident)
            self.artists[ident].shown = False
            try:
                del self.artists[ident]
            except KeyError:
                pass
        except:
            print("remove failed")

    def display(self, ident, shown):
        try:
            artist = self.artists[ident].artist
            if shown:
                self.pw.addItem(artist)
                self.artists[ident].shown = True
            else:
                self.pw.removeItem(artist)
                self.artists[ident].shown = False
        except KeyError:
            raise Exception('404 Artist not found')

    def checkboxChanged(self):
        for ident, item in self.tracelist.trace_dict.items():
            try:
                if item.checkState() and not self.artists[ident].shown:
                    self.display(ident, True)
                if not item.checkState() and self.artists[ident].shown:
                    self.display(ident, False)
            except KeyError:  # this means the artist has been deleted.
                pass

    def rangeChanged(self):

        lims = self.pw.viewRange()
        self.pointsToKeep = lims[0][1] - lims[0][0]
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

    @inlineCallbacks
    def remove_dataset(self, dataset):
        labels = yield dataset.getLabels()
        for label in labels:
            self.remove_artist(label)

    def set_xlimits(self, limits):
        self.pw.setXRange(limits[0], limits[1])
        self.current_limits = limits

    def set_ylimits(self, limits):
        self.pw.setYRange(limits[0], limits[1])

    def mouseMoved(self, pos):
        pnt = self.img.mapFromScene(pos)
        string = '(' + str(pnt.x()) + ' , ' + str(pnt.y()) + ')'
        self.coords.setText(string)

    @inlineCallbacks
    def get_init_vline(self):
        init_vline = yield self.pv.get_parameter(self.vline_param[0],
                                                 self.vline_param[1])
        print(init_vline)
        returnValue(init_vline)

    @inlineCallbacks
    def vline_changed(self, sig):
        val = self.inf.value()
        val = int(round(val))
        yield self.pv.set_parameter(self.vline_param[0],
                                    self.vline_param[1], val)
