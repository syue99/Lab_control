from GraphWidgetPyQtGraph import Graph_PyQtGraph as Graph
from PyQt5 import QtGui, QtCore, QtWidgets

class ScrollingGraph_PyQtGraph(Graph):
    def __init__(self, name, reactor, parent = None, ylim=[0,1], cxn=None):
        super(ScrollingGraph_PyQtGraph, self).__init__(name, reactor, parent)
        self.set_xlimits([0, 100])
        self.pointsToKeep = 100
        self._mouse_pressed = False

    def update_figure(self, _input = None):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    index = params.index
                    x = params.dataset.data[:,0]
                    y = params.dataset.data[:,index+1]
                    params.artist.setData(x,y)
                except:
                    pass

        try:
            if self._mouse_pressed:
                return
                # see if we need to redraw
            xmin_cur, xmax_cur = self.current_limits
            x_cur = x[-1] # current largest x value
            window_width = xmax_cur - xmin_cur
            # scroll if we've reached 75% of the window
            if (x_cur > (xmin_cur + 0.75*window_width) and (x_cur < xmax_cur)):
                shift = (xmax_cur - xmin_cur)/2.0
                xmin = xmin_cur + shift
                xmax = xmax_cur + shift
                self.set_xlimits( [xmin, xmax] )
        except Exception as e:
            pass

    #def mousePressEvent(self, mouse_event):
    #    print("AAAAAAAAAAAAA")
    #    if (mouse_event.button() == QtCore.Qt.LeftButton) or (mouse_event.button() == QtCore.Qt.RightButton):
    #        self._mouse_pressed = True
    #    #super(ScrollingGraph_PyQtGraph, self).mousePressEvent(mouse_event)
    #
    #def mouseReleaseEvent(self, mouse_event):
    #    print("BBBBBBBBBBBBB")
    #    self._mouse_pressed = False
    #    #super(ScrollingGraph_PyQtGraph, self).mouseReleaseEvent(mouse_event)
