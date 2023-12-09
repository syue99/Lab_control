from PyQt5 import QtGui, QtCore, QtWidgets
from ParameterListWidget import ParameterList


from traceListConfig import traceListConfig

class TraceList(QtWidgets.QListWidget):
    def __init__(self, parent):
        super(TraceList, self).__init__()
        self.parent = parent
        self.windows = []
        self.config = traceListConfig()
        self.setStyleSheet("background-color:%s;" % self.config.background_color)
        try:
            self.use_trace_color = self.config.use_trace_color
        except AttributeError:
            self.use_trace_color = False

        self.name = 'pmt'
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QtWidgets.QListWidgetItem('Traces')
        item.setCheckState(QtCore.Qt.Checked)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)


    def addTrace(self, ident, color):
        item = QtWidgets.QListWidgetItem(ident)

        if self.use_trace_color:
            foreground_color = QtGui.QColor("#123456")#self.parent.getItemColor(color)
            item.setForeground(foreground_color)
        else:
            item.setForeground(QtGui.QColor(0, 0, 0))
        item.setBackground(QtGui.QColor(255,255,255))

        item.setCheckState(QtCore.Qt.Unchecked)
        self.addItem(item)
        self.trace_dict[ident] = item

    def removeTrace(self, ident):
        item  = self.trace_dict[ident]
        row = self.row(item)
        self.takeItem(row)
        item = None

    def changeTraceListColor(self, ident, new_color):
        item = self.trace_dict[ident]
        item.setForeground(self.parent.getItemColor(new_color))

    def popupMenu(self, pos):
        menu = QtWidgets.QMenu()
        item = self.itemAt(pos)
        if (item == None): 
            dataaddAction = menu.addAction('Add Data Set')
            #spectrumaddAction = menu.addAction('NA')
            removeallAction = menu.addAction('Remove All Traces')

            action = menu.exec_(self.mapToGlobal(pos))
            if action == dataaddAction:
                ps.show()

            #if action == spectrumaddAction:
            #    ps = PredictSpectrum(self)
            #    self.windows.append(ps)
            #    ps.show()

            if action == removeallAction:
                for kk in reversed(range(self.count())):
                    ident = str(self.item(kk).text())
                    self.parent.remove_artist(ident)

        else:
            ident = str(item.text())
            parametersAction = menu.addAction('Parameters')
            togglecolorsAction = menu.addAction('Toggle colors')
            fitAction = menu.addAction('Fit')
            selectColorMenu = menu.addMenu("Select color")
            removeAction = menu.addAction('Remove')
            colorActionDict = {}
            colorSet = GUIConfig.GLOBALCOLORS
            for i in range(len(colorSet)):
                tabName = 'color' + str(i + 1)
                tabColor = GUIConfig.GLOBALCOLORS[i]
                colorAction = selectColorMenu.addAction(tabName)
                colorActionDict[colorAction] = tabColor
            #colorActionDict = {redAction:"r", greenAction:"g", yellowAction:"y", cyanAction:"c", magentaAction:"m", whiteAction:"w"}
            action = menu.exec_(self.mapToGlobal(pos))
            
            if action == parametersAction:
                # option to show parameters in separate window
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()

            if action == togglecolorsAction:               
                # option to change color of line
                new_color = next(self.parent.colorChooser)
                try:
                    if self.parent.show_points:
                        self.parent.artists[ident].artist.setData(pen = new_color, symbolBrush = new_color)
                        self.changeTraceListColor(ident, new_color)
                    else:
                        self.parent.artists[ident].artist.setData(pen = new_color)
                        self.changeTraceListColor(ident, new_color)
                except Exception as e:
                    # histWidget here
                    self.parent.artists[ident].artist.setBrush(new_color)
                

            if action == fitAction:
                pass

            if action in colorActionDict.keys():
                new_color = colorActionDict[action]
                try:
                    if self.parent.show_points:
                        self.parent.artists[ident].artist.setData(pen = new_color, symbolBrush = new_color)
                        self.changeTraceListColor(ident, new_color)
                    else:
                        self.parent.artists[ident].artist.setData(pen = new_color)
                        self.changeTraceListColor(ident, new_color)
                except Exception as e:
                    # histWidget here
                    self.parent.artists[ident].artist.setBrush(new_color + self.parent.opacityhex)

            if action == removeAction:
                self.parent.remove_artist(ident)