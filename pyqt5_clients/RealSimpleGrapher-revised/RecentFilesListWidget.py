from PyQt5 import QtGui, QtCore, QtWidgets
from twisted.internet.defer import inlineCallbacks
import socket
from GUIConfig import traceListConfig
from datetime import date

import functools
def dateCompare(d1, d2):
    monthRank = {
        'Jan': 0,
        'Feb': 1,
        'Mar': 2,
        'Apr': 3,
        'May': 4,
        'Jun': 5,
        'Jul': 6,
        'Aug': 7,
        'Sep': 8,
        'Oct': 9,
        'Nov': 10,
        'Dec': 11
    }
    y1 = d1[:4]
    y2 = d2[:4]
    m1 = d1[4:7]
    m2 = d2[4:7]
    d1 = d1[7:]
    d2 = d2[7:]
    if y1 > y2:
        return -1
    elif y1 == y2:
        if monthRank[m1] > monthRank[m2]:
            return -1
        elif monthRank[m1] == monthRank[m2]:
            if d1 > d2:
                return -1
            else:
                return 1
        else:
            return 1
    else:
        return 1


class RecentFilesListWidget(QtWidgets.QListWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.config = traceListConfig()
        self.setStyleSheet("background-color:%s;" % self.config.background_color)
        self.addItem('Initializing... Be Patient')
        self.connect()
        self.today = None

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name=socket.gethostname() + ' Data Vault Client')
        self.grapher = yield self.cxn.grapher
        self.dv = yield self.cxn.data_vault
        self.filteredText = ''
        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):
        self.doubleClicked.connect(self.onDoubleclick)
        yield self.dv.cd('ScriptScanner')
        self.populate()

    def filter(self, filteredText=''):
        self.filteredText = filteredText.lower()
        self.populate()

    @inlineCallbacks
    def loadDates(self):
        # get the list of directories whose names are dates
        # if today's date not change, no need for repeated work
        today = date.today()
        today = today.strftime("%m/%d/%y")
        if today != self.today:
            self.today = today
            ls = yield self.dv.dir()
            self.dates = sorted(ls[0], key=functools.cmp_to_key(dateCompare))

    @inlineCallbacks
    def populate(self):
        self.clear()
        self.addItem('Filtering... Be Patient')
        yield self.loadDates()
        items = []
        dateCounter = 0
        while (len(items) < 10 and dateCounter < len(self.dates)):
            yield self.dv.cd(self.dates[dateCounter])
            curItems = yield self.dv.dir()
            curItems = sorted(curItems[0], reverse=True)
            if len(curItems) >= 10:
                curItems = curItems[:10]
            for experimentData in curItems:
                yield self.dv.cd(experimentData)
                data = yield self.dv.dir()
                #avoid crashes when a time folder is empty
                try:
                    datasetName = data[1][0]
                    datasetNameWTimeStamp = data[1][0].split(self.dates[dateCounter], 1)
                    timeStamp = datasetNameWTimeStamp[1]
                    datasetName = datasetNameWTimeStamp[0]
                    datasetNameBeautify = self.dates[dateCounter] + timeStamp + ': ' + datasetName 
                    if self.filteredText != '':
                        if self.filteredText in datasetName.lower():
                            items.append(datasetNameBeautify)
                    else:
                        items.append(datasetNameBeautify)
                except:
                    pass
                yield self.dv.cd(1)
            yield self.dv.cd(1)
            dateCounter += 1
            #print(len(items),dateCounter)
        if len(items) == 0:
            items = ['No Result..., check spelling']
        self.clear()
        self.addItems(items)

    @inlineCallbacks
    def onDoubleclick(self, item):
        item = self.currentItem().text()
        if 'No Result' in item:
            return
        path = yield self.dv.cd()
        info = str(item).split(': ')
        datetime = info[0].split('_', 1)
        date = datetime[0]
        timeStamp = datetime[1]
        datasetName = info[1]+date+'_'+timeStamp
        path.append(date)
        path.append(timeStamp)
        yield self.grapher.plot((path, datasetName), self.parent.name, False)