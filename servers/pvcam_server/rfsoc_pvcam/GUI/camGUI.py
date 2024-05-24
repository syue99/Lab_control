# 20220728
# test and time GUI that draw image in real time
# update 3 images and 3 line plots takes 3ms
# created by Pai Peng

# time budge;
# for images with 512 * 512 pixels w/ 50 * 50 sites, updating imshow takes 0.26s, histogram takes 0.12s,
# lines takes 0.04s, backend data takes 0.03s
import warnings

warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
import os
import json
import copy
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, QtCore, uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import numpy as np
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
sys.path.append("C://Users/Cryo_rdyberg/Documents/Codebase/Lab_control/servers/pvcam_server/rfsoc_pvcam/")
from analysisFunctions import scaleImage

np.seterr(divide='ignore')


class RectItem(pg.GraphicsObject):
    # draw rectangles for atom region
    def __init__(self, rect, parent=None):
        super().__init__(parent)
        self._rect = rect
        self.picture = QtGui.QPicture()

        self.colored = (214, 0, 0, 100)
        self.noColor = (0, 0, 0, 0)
        self.color = self.colored

        self._generate_picture()

    @property
    def rect(self):
        return self._rect

    def _generate_picture(self):
        painter = QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen(self.color))
        # painter.setBrush(pg.mkBrush("g"))
        painter.drawRect(self.rect)
        painter.end()

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

    def show(self):
        self.color = self.colored
        painter = QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen(self.color))
        # painter.setBrush(pg.mkBrush("g"))
        painter.drawRect(self.rect)
        painter.end()

    def hide(self):
        self.color = self.noColor
        painter = QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen(self.color))
        # painter.setBrush(pg.mkBrush("g"))
        painter.drawRect(self.rect)
        painter.end()

    def resetRect(self, rect):
        self._rect = rect


class resultsQueue:
    def __init__(self, Nhistory=100):
        self.Nhistory = Nhistory
        self.resQueue = []  # a queue that stores the past results

    def update(self, newResults):
        self.resQueue.append(newResults)
        if len(self.resQueue) > self.Nhistory:
            self.resQueue.pop(0)

    def getNimagesInExp(self):
        return len(self.resQueue[-1]['imageQueue'])

    def getFnNames(self, imageIndex):
        return self.resQueue[-1][imageIndex].keys()

    def getResultsMatrix(self, imageIndex, fnName):
        """return a matrix of dimension (Nhistory x Nsites),
        containing the historical resutls of the imageIndex and fnName.
        For certain loops that the imageIndex or fnName does not exist, fill in with None"""
        mat = []
        for res in self.resQueue:
            if imageIndex not in res.keys():
                mat.append(None)
            elif fnName not in res[imageIndex].keys():
                mat.append(None)
            else:
                mat.append(np.array(res[imageIndex][fnName]))
        return mat


class editHistDialog(QDialog):
    def __init__(self, histIndex, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join('GUI', 'editHist.ui'), self)
        self.histIndex = histIndex
        # initialize lineedits of Image
        self.imageEdit = self.findChild(QLineEdit, "BinImageEdit")
        texttemp = parent.histImage[self.histIndex]
        self.imageEdit.setText(f'{texttemp}')
        # initialize lineedits of bins
        self.binEdits = [self.findChild(QLineEdit, "BinStartEdit"),
                         self.findChild(QLineEdit, "BinEndEdit"),
                         self.findChild(QLineEdit, "BinNumberEdit")]
        for i in range(3):
            texttemp = parent.bins[i]
            self.binEdits[i].setText(f'{texttemp}')
        self.setTabOrder(self.imageEdit, self.binEdits[0])
        self.setTabOrder(self.binEdits[0], self.binEdits[1])
        self.setTabOrder(self.binEdits[1], self.binEdits[2])
        self.binDataType = [float, float, int]
        self.newBins = [None, None, None]
        self.histImage = parent.histImage
        self.myHistogram = parent.myHistogram
        self.bins = parent.bins
        self.Nsites = parent.Nsites
        self.Nhistory = parent.Nhistory
        self.threshold = parent.threshold
        self.histFigure = parent.histFigure
        self.histTransformation = parent.histTransformation
        self.hist = parent.hist

    def accept(self):
        # check which image to display histogram
        if len(self.imageEdit.displayText()) > 0:
            self.histImage[self.histIndex] = int(self.imageEdit.displayText())

        # check if bins has been changed from UI
        for i in range(3):
            if len(self.binEdits[i].displayText()) > 0:
                self.newBins[i] = self.binDataType[i](self.binEdits[i].displayText())

        for i in range(3):
            if self.newBins[i] is None:
                self.newBins[i] = self.bins[i]
        if self.newBins[1] <= self.newBins[0]:
            print('Bin start value must be smaller than bin end value!')
            return
        else:
            self.bins[:] = self.newBins
        self.myHistogram[self.histIndex] = myHistogram(self.bins, self.Nsites, self.Nhistory)
        self.histTransformation.translate(0, self.bins[0])
        self.hist[self.histIndex].setTransform(self.histTransformation)
        self.close()


class editAnalysisDialog(QDialog):
    def __init__(self, i, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join('GUI', 'editAnalysis.ui'), self)
        self.lineEditDict = {}
        for tName in ['X', 'fnName', 'images', 'imagesNormTo']:
            currLineEdit = self.findChild(QLineEdit, tName)
            if tName in parent.lineOpts[i]:
                currLineEdit.setText(str(parent.lineOpts[i][tName]))
            self.lineEditDict.update({tName: currLineEdit})
            # currLineEdit.setTabChangesFocus(True)
        self.OKbutton = self.findChild(QDialogButtonBox, "buttonBox")
        # self.OKbutton.accepted.connect(self.accept)
        self.lineOpts = parent.lineOpts
        self.myLinePlot = parent.myLinePlot
        self.resultsQueue = parent.resultsQueue
        self.updateLinePlot = parent.updateLinePlot
        self.analysisIndex = i

    def accept(self):
        updatedLineOpt = {}
        updatedLineOpt.update({'X': self.lineEditDict['X'].text()})
        updatedLineOpt.update({'fnName': self.lineEditDict['fnName'].text()})
        updatedLineOpt.update({'images': json.loads(self.lineEditDict['images'].text())})  # str to list
        if isinstance(updatedLineOpt['images'], int):
            updatedLineOpt['images'] = [updatedLineOpt['images']]
        if len(self.lineEditDict['imagesNormTo'].text()) > 0:
            updatedLineOpt.update({'imagesNormTo': json.loads(self.lineEditDict['imagesNormTo'].text())})
            if isinstance(updatedLineOpt['imagesNormTo'], int):
                updatedLineOpt['imagesNormTo'] = [updatedLineOpt['imagesNormTo']]
        self.lineOpts[self.analysisIndex].clear()
        self.lineOpts[self.analysisIndex] = updatedLineOpt
        self.myLinePlot[self.analysisIndex] = myLinePlot(self.resultsQueue, imageGUI=self.parent, **updatedLineOpt)
        self.updateLinePlot(self.analysisIndex)
        self.close()


class myHistogram:
    def __init__(self, bins, Nsites, Nhistory):
        self.bins = bins
        self.Nsites = Nsites
        self.counts = []
        self.Nhistory = Nhistory
        self.hist = np.zeros((self.bins[2], self.Nsites)).astype('int')

    def update_count(self, newcount):
        newcount = np.array(newcount)
        if len(newcount) != self.Nsites:
            raise ValueError('New count length unequal to Nsites')

        self.counts.append(newcount)
        if len(self.counts) > self.Nhistory:
            oldcount = copy.copy(self.counts[0])
            self.counts.pop(0)
            # decrease hist for the removed entries
            oldIdxBins = self.getIdxBins(oldcount)
            for i in range(self.Nsites):
                self.hist[oldIdxBins[i], i] -= 1
        # increase hist for the new entries
        newIdxBins = self.getIdxBins(newcount)
        for i in range(self.Nsites):
            self.hist[newIdxBins[i], i] += 1

    def getIdxBins(self, value):
        # get the index of bins for a given value
        binwidth = (self.bins[1] - self.bins[0]) / self.bins[2]
        IdxBins = ((value - self.bins[0]) / binwidth)
        roundIdxBins = np.round(IdxBins)
        IdxBins[np.abs(IdxBins - roundIdxBins) < 1e-6] = roundIdxBins[np.abs(IdxBins - roundIdxBins) < 1e-6]
        IdxBins = IdxBins.astype(int)
        IdxBins[IdxBins >= self.bins[2]] = self.bins[2] - 1
        IdxBins[IdxBins < 0] = 0
        return IdxBins


class myLinePlot:
    def __init__(self, resultsQueue, X, fnName, images, imageGUI, imagesNormTo=None):
        self.X = X
        self.fnName = fnName
        self.images = images
        self.imagesNormTo = imagesNormTo
        self.resultsQueue = resultsQueue
        self.imageGUI = imageGUI

    def getPlotData(self):
        # return xList, yList for the data to plot. xList and yList should be lists whose length = number of curves in
        # the lineplot.
        yList = []
        xList = []

        # if plotting background counts, get data from self.imageGUI.backgroundCounts
        if self.fnName == 'backgroundCounts':
            for imageIndex in self.images:
                yList.append(self.imageGUI.backgroundCounts[imageIndex])
                xList.append(np.arange(self.imageGUI.backgroundCounts[imageIndex]))
            return xList, yList

        # if not background counts, get the data from resultsQueue
        if self.X == 'time':
            for imageIndex in self.images:
                mat = self.resultsQueue.getResultsMatrix(imageIndex, self.fnName)
                yTemp = []
                for arr in mat:
                    if arr is None:
                        yTemp.append(None)
                    else:
                        yTemp.append(np.mean(arr))  # append site-averaged data
                yList.append(np.array(yTemp))

            if self.imagesNormTo is None:
                for i, y in enumerate(yList):
                    filterList = np.logical_not(y == None)
                    xList.append(np.arange(len(y))[filterList])  # skip indices that y==None
                    yList[i] = y[filterList]
                return xList, yList
            else:
                yNormToList = []
                for imageIndex in self.imagesNormTo:
                    mat = self.resultsQueue.getResultsMatrix(imageIndex, self.fnName)
                    yTemp = []
                    for arr in mat:
                        if arr is None:
                            yTemp.append(None)
                        else:
                            yTemp.append(np.mean(arr))
                    yNormToList.append(np.array(yTemp))

                for idx, (y, yNormTo) in enumerate(zip(yList, yNormToList)):
                    filterList = np.logical_and(np.logical_not(y == None), np.logical_not(yNormTo == None))
                    xList.append(np.arange(len(y))[filterList])
                    yList[idx] = y[filterList] / yNormTo[filterList]
                return xList, yList

        if self.X == 'site':
            for imageIndex in self.images:
                yTemp = None
                count = 0  # counts not-None historical images
                mat = self.resultsQueue.getResultsMatrix(imageIndex, self.fnName)
                for arr in mat:
                    if arr is not None:
                        count += 1
                        if yTemp is None:
                            yTemp = arr
                        else:
                            yTemp += arr
                if yTemp is None:
                    yList.append(np.array([]))
                    xList.append(np.array([]))
                else:
                    yList.append(yTemp / count)
                    xList.append(np.arange(len(yTemp)))
            if self.imagesNormTo is None:
                return xList, yList
            else:
                yNormToList = []
                for imageIndex in self.imagesNormTo:
                    yTemp = None
                    count = 0
                    mat = self.resultsQueue.getResultsMatrix(imageIndex, self.fnName)
                    for arr in mat:
                        if arr is not None:
                            count += 1
                            if yTemp is None:
                                yTemp = arr
                            else:
                                yTemp += arr
                    if yTemp is None:
                        yList.append(np.array([]))
                    else:
                        yNormToList.append(yTemp / count)
                for idx, (y, yNormTo) in enumerate(zip(yList, yNormToList)):
                    if len(y) == 0 or len(yNormTo) == 0:  # if one of the image doesn't exist, don't plot
                        yList[idx] = []
                        xList[idx] = []
                    else:
                        yList[idx] = y / yNormTo
                return xList, yList


class ImageGUI(QtWidgets.QMainWindow):
    def __init__(self, detectionParam, imgdata, newdatain, results, *args, **kwargs):
        super(ImageGUI, self).__init__(*args, **kwargs)
        # input: imgdata points to the shared memery where the image is stored;
        # newdatain points to the shared memery where the flag of new data coming in is stored
        self.open = True
        self.threshold = {}
        self.position = {}
        self.bgExcludeRegion = {}
        for cam in detectionParam:
            self.threshold[cam] = np.array(detectionParam[cam]['thresholds'])
            self.position[cam] = detectionParam[cam]['positions']
            self.bgExcludeRegion[cam] = detectionParam[cam]['bgExcludeRegion']
        self.imgdata = imgdata
        self.newdatain = newdatain
        self.results = results
        # initializing parameters for plots
        self.Nsites = len(self.position['pvcam'])
        self.Nhistory = 100
        self.resultsQueue = resultsQueue(self.Nhistory)

        self.bins = [-20., 60., 20]
        self.rAtom = 2
        self.NimagesInExp = 0
        self.showWhichImage = [0, 1, 2]

        self.fontSize = 12  # default
        self.font = QtGui.QFont()
        self.font.setPixelSize(self.fontSize)

        # load the UI page
        uic.loadUi(os.path.join('GUI', 'camGUI.ui'), self)

        # list of names of layouts, used for set showButtons:
        # showButtons are named as [name]ShowButton; the layout it controls is named as [name]Layout,
        # see findWidgetHandles for usage
        self.layoutList = ['Image', 'Analysis', 'Hist']
        self.findWidgetHandles()
        self.setButtons()

        # initialize lineedit of Nhistory
        self.NhistoryEdit = self.findChild(QLineEdit, "NhistoryEdit")
        self.NhistoryEdit.setText(f'{self.Nhistory}')
        self.NhistoryEdit.textChanged.connect(self.NhistoryUpdate)
        self.newNhistory = None
        self.setNhistoryButton = self.findChild(QPushButton, "setNhistoryButton")
        self.setNhistoryButton.pressed.connect(self.setNhistory)

        # line options:
        # 'X': x variable name
        # 'fnName': y variable name
        # 'images': which images to plot
        # 'imagesNormTo' (optional): plot Y(images)/Y(imagesNormTo), must be the same length as 'images'
        self.lineOpts = [{'X': 'site', 'fnName': 'getOccupancy', 'images': [0, 1]},
                         {'X': 'time', 'fnName': 'getCounts', 'images': [0]},
                         {'X': 'time', 'fnName': 'getOccupancy', 'images': [1, 2], 'imagesNormTo': [0, 1]},
                         {'X': 'site', 'fnName': 'getOccupancy', 'images': [1, 2], 'imagesNormTo': [0, 1]}]
        self.myLinePlot = [myLinePlot(self.resultsQueue, imageGUI=self, **lineOpt) for lineOpt in self.lineOpts]
        self.myHistogram = [myHistogram(self.bins, self.Nsites, self.Nhistory) for _ in range(self.Nhist)]
        self.histImage = [0]  # which image to show histogram, must be same length as Nhist
        self.histCam = [None]

        self.initImages()
        self.initHist()
        self.initLinePlots()

        self.show()

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_image)
        timer.start(100)

    def findWidgetHandles(self):
        # initialize all plots
        self.imageFigure = [self.findChild(PlotWidget, "Image{:d}".format(i)) for i in range(3)]
        self.histFigure = [self.findChild(PlotWidget, "Hist{:d}".format(i)) for i in [0]]
        self.lineFigure = [self.findChild(PlotWidget, "Analyze{:d}".format(i)) for i in range(4)]
        self.runNumber = self.findChild(QLabel, "RunNumber")
        self.params = self.findChild(QLabel, "Params")

        self.Nimage = len(self.imageFigure)  # total number of images
        self.Nhist = len(self.histFigure)  # number of images to calculate histogram
        self.Nline = len(self.lineFigure)  # number of lines plots

        self.editButtons = [self.findChild(QPushButton, "EditButton{:d}".format(i)) for i in range(self.Nline)]
        self.imageCombos = [self.findChild(QComboBox, "Image{:d}_combo".format(i)) for i in range(self.Nimage)]
        self.histButton = [self.findChild(QPushButton, "EditButtonHist{:d}".format(i)) for i in range(self.Nhist)]

        self.showButtons = {}

        for layoutName in self.layoutList:
            self.showButtons[layoutName] = {'button': self.findChild(QPushButton, layoutName + "ShowButton"),
                                            'layout': self.findChild(QLayout, layoutName + "Layout")}
        self.circleButton = self.findChild(QPushButton, "CircleButton")

        self.backGroundCounts = [[] for _ in range(self.Nimage)]

    def setButtons(self):
        for i in range(len(self.editButtons)):
            self.editButtons[i].pressed.connect(self.popUpEditAnalysisWrapper(i))
            self.editButtons[i].setIcon(QIcon(os.path.join('GUI', 'gear.png')))

        for i in range(len(self.imageCombos)):
            self.imageCombos[i].activated.connect(self.imageComboUpdateWrapper(i))

        for i in range(len(self.histButton)):
            self.histButton[i].pressed.connect(self.popUpEditHistWrapper(i))
            self.histButton[i].setIcon(QIcon(os.path.join('GUI', 'gear.png')))

        for layoutName in self.layoutList:
            self.showButtons[layoutName]['button'].pressed.connect(
                self.hideShowFuncWrapper(self.showButtons[layoutName]['button'],
                                         self.showButtons[layoutName]['layout']))

        self.circleButton.pressed.connect(self.showHideCircles)

    def hideShowWidgetFromLayout(self, myItem):
        """ Recursively hide or show all widgets in a layout"""
        # print('myItem is {:s}'.format(myItem.objectName()))
        if isinstance(myItem, QWidgetItem):  # if myItem is a widget, hide or show it
            myWidget = myItem.widget()
            if 'Title' in myWidget.objectName() or 'ShowButton' in myWidget.objectName():
                return
            myWidget.setVisible(not myWidget.isVisible())
            print('myWidget is {:s}'.format(myWidget.objectName()))
        elif isinstance(myItem, QLayoutItem):  # if myItem is a layout, hide or show its children
            # print('myItem is {:s}'.format(myItem.objectName()))
            for idx in range(myItem.count()):
                child = myItem.itemAt(idx)
                self.hideShowWidgetFromLayout(child)

    def hideShowFunc(self, myButton, parentLayout):
        if myButton.text() == ' Show':
            myButton.setText(' Hide')
        elif myButton.text() == ' Hide':
            myButton.setText(' Show')
        self.hideShowWidgetFromLayout(parentLayout)

    def hideShowFuncWrapper(self, myButton, parentLayout):
        return lambda: self.hideShowFunc(myButton, parentLayout)

    def initImages(self):
        # initialize images
        self.image = [pg.ImageItem() for _ in range(self.Nimage)]
        self.areCirclesShown = False
        self.allRects = [[] for _ in range(self.Nimage)]
        # self.tweezerPosScatterPlot = [pg.ScatterPlotItem(size=5, brush=pg.mkBrush(0, 0, 0, 100)) for _ in
        #                               range(self.Nimage)]

        for i in range(self.Nimage):
            self.imageFigure[i].setAspectLocked()
            self.imageFigure[i].setBackground('w')
            self.imageFigure[i].addItem(item=self.image[i])
            #self.image[i].setLookupTable()
                #pg.colormap.get('cubehelix', source='matplotlib', skipCache=True).getLookupTable(nPts=256))
            self.imageFigure[i].getViewBox().invertY(True)
            # self.imageFigure[i].addItem(self.tweezerPosScatterPlot[i])
            self.imageFigure[i].getAxis('left').setTextPen('k')
            self.imageFigure[i].getAxis('bottom').setTextPen('k')
            self.imageFigure[i].getAxis("left").setStyle(tickFont=self.font)
            self.imageFigure[i].getAxis("bottom").setStyle(tickFont=self.font)

    def initHist(self):
        # initialize histograms
        self.hist = [pg.ImageItem() for _ in range(self.Nhist)]
        self.histTransformation = QTransform()  # prepare ImageItem transformation:
        self.histTransformation.translate(0, self.bins[0])  # move 3x3 image to locate center at axis origin
        self.thresholdLine = [[] for _ in range(self.Nhist)]
        # setTransform(tr)  # assign transform
        for i in range(self.Nhist):
            self.histFigure[i].setBackground('w')
            # self.hist[i].setTransform(self.histTransformation)
            self.histFigure[i].addItem(item=self.hist[i])
            #self.histFigure[i].addColorBar(self.hist[i])#,
                                           #colorMap=pg.colormap.get('gray_r', source='matplotlib', skipCache=True),
                                           #interactive=False, pen='k')
            self.histFigure[i].setLabel('bottom', text='site', **{'color': '#000', 'font-size': f'{self.fontSize}pt'})
            # self.histFigure[i].setTitle(f'Histogram {i}', **{'color': '#000', 'size': '20pt'})
            self.histFigure[i].getAxis('left').setTextPen('k')
            self.histFigure[i].getAxis("left").setStyle(tickFont=self.font)
            self.histFigure[i].getAxis('bottom').setTextPen('k')
            self.histFigure[i].getAxis("bottom").setStyle(tickFont=self.font)
            for pAtom in range(self.Nsites):
                pThresholdLine = pg.PlotDataItem(pen='r')
                self.histFigure[i].addItem(pThresholdLine)
                self.thresholdLine[i].append(pThresholdLine)

    def initLinePlots(self):
        # initialize line plots
        self.cm = 'krbg'
        self.line = []
        for pLine in range(self.Nline):
            linetemp = []
            for IdxImage in range(len(self.lineOpts[pLine]['images'])):
                pImage = self.lineOpts[pLine]['images'][IdxImage]
                name = f'Im{pImage}'
                if 'imagesNormTo' in self.lineOpts[pLine]:
                    pImage_norm_to = self.lineOpts[pLine]['imagesNormTo'][IdxImage]
                    name = name + f'/Im{pImage_norm_to}'
                linetemp.append(pg.PlotDataItem(name=name, pen=pg.mkPen(color=self.cm[IdxImage], width=2)))
            self.line.append(linetemp)
        for i in range(self.Nline):
            legend_i = self.lineFigure[i].addLegend(offset=QtCore.QPointF(-150, 1), brush='w', labelTextColor='k')
            legend_i.anchor(itemPos=(0, 0), parentPos=(0, 0), offset=(2, 2))
            for p in self.line[i]:
                self.lineFigure[i].addItem(p)
            if self.lineOpts[i]['fnName'][:3] == 'get':
                yLabel = self.lineOpts[i]['fnName'][3:]
            else:
                yLabel = self.lineOpts[i]['fnName']
            self.lineFigure[i].setLabel('left', text=yLabel, **{'color': '#000', 'font-size': f'{self.fontSize}pt'})
            self.lineFigure[i].setLabel('bottom', text=self.lineOpts[i]['X'],
                                        **{'color': '#000', 'font-size': f'{self.fontSize}pt'})
            self.lineFigure[i].setBackground('w')
            self.lineFigure[i].getAxis('left').setTextPen('k')
            self.lineFigure[i].getAxis("left").setStyle(tickFont=self.font)
            self.lineFigure[i].getAxis('bottom').setTextPen('k')
            self.lineFigure[i].getAxis("bottom").setStyle(tickFont=self.font)
            self.lineFigure[i].setMouseEnabled(x=False, y=False)

            if self.lineOpts[i]['fnName'] == 'getOccupancy':
                self.lineFigure[i].disableAutoRange(axis='y')
                self.lineFigure[i].setYRange(min=0, max=1)
            elif self.lineOpts[i]['fnName'] == 'getCounts':
                self.lineFigure[i].disableAutoRange(axis='y')
                self.lineFigure[i].setYRange(min=0, max=100)
            else:
                self.lineFigure[i].enableAutoRange(axis='y')

    def allCamIdx2camWiseIdx(self, imageUqeue, allCamIdx):
        return int(np.sum([cam == imageUqeue[allCamIdx] for cam in imageUqeue[:allCamIdx]]))

    def orderResDict(self, resDict):
        orderedResDict = {}
        for idx in range(len(resDict['imageQueue'])):
            cam = resDict['imageQueue'][idx]
            orderedResDict[idx] = resDict[cam][self.allCamIdx2camWiseIdx(resDict['imageQueue'], idx)]
        orderedResDict['imageQueue'] = resDict['imageQueue']
        return orderedResDict

    def updateLinePlot(self, i):
        linetemp = []
        for IdxImage in range(len(self.lineOpts[i]['images'])):
            pImage = self.lineOpts[i]['images'][IdxImage]
            name = f'Im{pImage}'
            if 'imagesNormTo' in self.lineOpts[i]:
                pImage_norm_to = self.lineOpts[i]['imagesNormTo'][IdxImage]
                name = name + f'/Im{pImage_norm_to}'
            linetemp.append(pg.PlotDataItem(name=name, pen=pg.mkPen(color=self.cm[IdxImage], width=2)))
        self.line[i] = linetemp

        self.lineFigure[i].clear()
        for p in self.line[i]:
            self.lineFigure[i].addItem(p)
        if self.lineOpts[i]['fnName'][:3] == 'get':
            yLabel = self.lineOpts[i]['fnName'][3:]
        else:
            yLabel = self.lineOpts[i]['fnName']
        self.lineFigure[i].setLabel('left', text=yLabel, **{'color': '#000', 'font-size': f'{self.fontSize}pt'})
        self.lineFigure[i].setLabel('bottom', text=self.lineOpts[i]['X'],
                                    **{'color': '#000', 'font-size': f'{self.fontSize}pt'})
        if self.lineOpts[i]['fnName'] == 'getOccupancy':
            self.lineFigure[i].disableAutoRange(axis='y')
            self.lineFigure[i].setYRange(min=0, max=1)
        elif self.lineOpts[i]['fnName'] == 'getCounts':
            self.lineFigure[i].disableAutoRange(axis='y')
            self.lineFigure[i].setYRange(min=0, max=100)
        else:
            self.lineFigure[i].enableAutoRange(axis='y')

    def udpateBackgroundCounts(self, img, cam, index):
        # update index_th background counts using img
        # if img is None, append np.nan
        if img is None:
            self.backGroundCounts[index].append(np.nan)
            if len(self.backGroundCounts[index]) > self.Nhistory:
                self.backGroundCounts[index].pop(0)
            return
        bgExcludeRegion = self.bgExcludeRegion[cam]
        imgBgExcludeRegion = img[bgExcludeRegion[0][1]:bgExcludeRegion[1][1],
                             bgExcludeRegion[0][0]:bgExcludeRegion[1][0]]
        countsInBgRegion = np.sum(img) - np.sum(imgBgExcludeRegion)
        pxsInBgRegion = img.size - imgBgExcludeRegion.size
        self.backGroundCounts[index].append(countsInBgRegion / pxsInBgRegion)
        if len(self.backGroundCounts[index]) > self.Nhistory:
            self.backGroundCounts[index].pop(0)

    def update_image(self):
        if self.newdatain.value:
            self.runNumber.setText(self.results['runNumber'].capitalize())
            self.params.setText(', '.join(self.results['fileName'].split(',')))

            for i in range(3):
                if self.showWhichImage[i] is not None:
                    if self.showWhichImage[i] < len(self.results['imageQueue']):
                        cam = self.results['imageQueue'][self.showWhichImage[i]]
                        camWiseIdx = self.allCamIdx2camWiseIdx(self.results['imageQueue'], self.showWhichImage[i])
                        newImage = copy.deepcopy(self.imgdata[cam][camWiseIdx])
                        newImage = scaleImage(newImage.T, cameraType=cam)
                        self.udpateBackgroundCounts(newImage.T, cam, i)
                    else:
                        newImage = np.zeros((10, 10))
                        self.udpateBackgroundCounts(None, None, i)
                else:
                    newImage = np.zeros((10, 10))
                    self.udpateBackgroundCounts(None, None, i)

                # update current images
                self.image[i].setImage(newImage)
                if self.showWhichImage[i] < len(self.results['imageQueue']):
                    cam = self.results['imageQueue'][self.showWhichImage[i]]
                    if cam == 'nuvu':
                        pass
                        # self.image[i].setLevels([0, 50])
                    else:
                        self.image[i].setLevels([0, 20])

            newResults = self.orderResDict(copy.deepcopy(self.results))
            self.resultsQueue.update(newResults)

            # update combos
            NewNimagesInExp = self.resultsQueue.getNimagesInExp()
            if NewNimagesInExp != self.NimagesInExp:
                self.NimagesInExp = NewNimagesInExp
                for i, combo in enumerate(self.imageCombos):
                    combo.clear()
                    combo.insertItems(0, ['Image{:d} ({:s})'.format(i, newResults['imageQueue'][i]) for i in
                                          range(self.NimagesInExp)])
                    combo.insertItem(100, 'None')
                    combo.setCurrentIndex(self.showWhichImage[i])

            # update current histograms
            for i in range(self.Nhist):
                newHistCam = newResults['imageQueue'][self.histImage[i]]
                if self.histCam[i] != newHistCam:  # if cam type changed, reset histogram and thresholds
                    self.myHistogram[i] = myHistogram(self.bins, self.Nsites, self.Nhistory)
                    self.histCam[i] = newHistCam
                    for pAtom, pThresholdLine in enumerate(self.thresholdLine[i]):
                        pThresholdLine.setData([pAtom - 0.5, pAtom + 0.5],
                                               self.threshold[newHistCam][pAtom] * np.ones(2))
                if self.histImage[i] is not None and 'getCounts' in newResults[self.histImage[i]]:
                    self.myHistogram[i].update_count(newResults[self.histImage[i]]['getCounts'])
                    self.hist[i].setImage(self.myHistogram[i].hist.transpose())
                    self.hist[i].setRect([-0.5, self.bins[0], self.Nsites, self.bins[1] - self.bins[0]])

                else:
                    self.hist[i].setImage(np.zeros((self.bins[2], self.Nsites)).transpose())

            # update all lines
            for pLine in range(self.Nline):
                xList, yList = self.myLinePlot[pLine].getPlotData()
                for idxImage, (xdata, ydata) in enumerate(zip(xList, yList)):
                    # print(xdata, ydata)
                    self.line[pLine][idxImage].setData(xdata, ydata)
            t0 = time.time()
            self.newdatain.value = 0
            t1 = time.time()
        self.show()

    def imageComboUpdate(self, i):
        if self.imageCombos[i].currentText() == 'None':
            self.showWhichImage[i] = None
        else:
            self.showWhichImage[i] = self.imageCombos[i].currentIndex()

    def imageComboUpdateWrapper(self, i):
        return lambda: self.imageComboUpdate(i)

    def histComboUpdate(self, i):
        if self.histCombos[i].currentText() == 'None':
            self.histImage[i] = None
        else:
            self.histImage[i] = self.histCombos[i].currentIndex()
        self.myHistogram[i] = myHistogram(self.bins, self.Nsites, self.Nhistory)

    def histComboUpdateWrapper(self, i):
        return lambda: self.histComboUpdate(i)

    def popUpEditAnalysis(self, i):
        dlg = editAnalysisDialog(i, parent=self)
        dlg.exec ()

    def popUpEditAnalysisWrapper(self, i):
        return lambda: self.popUpEditAnalysis(i)

    def popUpEditHist(self, i):
        dlg = editHistDialog(i, parent=self)
        dlg.exec ()

    def popUpEditHistWrapper(self, i):
        return lambda: self.popUpEditHist(i)

    def NhistoryUpdate(self, value):
        self.newNhistory = int(value)

    def setNhistory(self):
        # check if Nhistory has been changed from UI
        if self.newNhistory is not None:
            if self.newNhistory <= 1:
                print('Number of history loops must be greater than 1!')
                return
            elif self.newNhistory != self.Nhistory:
                self.Nhistory = self.newNhistory
                texttemp = self.Nhistory
                self.NhistoryEdit.setText(f'{texttemp}')
                self.resultsQueue = resultsQueue(self.Nhistory)
                self.myLinePlot = [myLinePlot(self.resultsQueue, imageGUI=self, **lineOpt) for lineOpt in self.lineOpts]
                self.myHistogram = [myHistogram(self.bins, self.Nsites, self.Nhistory) for _ in range(self.Nhist)]

    def binUpdate(self, i, dataType, value):
        self.newBins[i] = dataType(value)

    def binUpdateWrapper(self, i, datatype):
        return lambda value: self.binUpdate(i, datatype, value)

    def imageComboUpdate(self, i):
        if self.imageCombos[i].currentText() == 'None':
            self.showWhichImage[i] = None
        else:
            self.showWhichImage[i] = self.imageCombos[i].currentIndex()

    def NhistoryUpdate(self, value):
        self.newNhistory = int(value)

    def showHideCircles(self):
        if self.areCirclesShown:
            for i in range(self.Nimage):
                for rect_item in self.allRects[i]:
                    rect_item.hide()
                # self.tweezerPosScatterPlot[i].setData([])
                self.imageFigure[i].update()
            self.areCirclesShown = False
            print('Hide circles')

        else:
            currImageQueue = self.resultsQueue.resQueue[-1]['imageQueue']
            for i in range(self.Nimage):
                if self.showWhichImage[i] < len(currImageQueue):
                    cam = currImageQueue[self.showWhichImage[i]]
                    if len(self.allRects[i]) == 0:
                        for pAtom in self.position[cam]:
                            rect_item = RectItem(QtCore.QRectF(pAtom[0] - self.rAtom, pAtom[1] - self.rAtom,
                                                               (self.rAtom * 2 + 1), (self.rAtom * 2 + 1)))
                            self.allRects[i].append(rect_item)
                            self.imageFigure[i].addItem(rect_item)

                    else:
                        for pAtom, rect_item in zip(self.position[cam], self.allRects[i]):
                            rect_item.resetRect(QtCore.QRectF(pAtom[0] - self.rAtom, pAtom[1] - self.rAtom,
                                                              (self.rAtom * 2 + 1), (self.rAtom * 2 + 1)))
                            rect_item.show()
                    self.imageFigure[i].update()
            self.areCirclesShown = True
            print('Show circles')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            print('Window closed')
        else:
            event.ignore()
